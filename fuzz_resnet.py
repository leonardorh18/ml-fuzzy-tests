#!/usr/bin/env python3
"""Mini-TensorFuzz: fuzzing de classificadores de imagem guiado por cobertura de neurônios.

Algoritmo (no estilo TensorFuzz / DeepHunter):

    corpus <- sementes (imagens de seeds/)
    para cada semente: guarda a classe original prevista pelo modelo
    repita ITERS vezes:
        escolhe um elemento do corpus (prioriza os menos sorteados)
        aplica uma mutação aleatória (ruído, brilho, contraste, rotação, blur, patch)
        projeta na bola L∞ de raio EPSILON em torno da semente original
        roda o modelo e mede a cobertura de neurônios
        oráculo:  classe prevista != classe original  ->  falha (salva a imagem)
        feedback: sem falha mas cobriu neurônios novos  ->  volta para o corpus

Cobertura de neurônios (DeepXplore): para cada camada monitorada, cada canal
(CNN) ou dimensão oculta (Transformer) é um neurônio. A ativação é a média
espacial/sobre os tokens, normalizada para [0, 1] dentro da camada (min-max por
entrada). Um neurônio está coberto se alguma entrada já o levou acima de
COV_THRESHOLD.

Uso:
    python fuzz_resnet.py --iters 2000 --out results_resnet
    python fuzz_resnet.py --model google/vit-base-patch16-224 --iters 2000 --out results_vit
"""

import argparse
import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torchvision.transforms.functional as TF
from PIL import Image

# ---------------------------------------------------------------------------
# Parâmetros ajustáveis
# ---------------------------------------------------------------------------
EPSILON = 0.08          # raio máximo da perturbação (norma L∞, pixels em [0, 1])
COV_THRESHOLD = 0.5     # neurônio coberto se ativação normalizada > limiar
IMAGE_SIZE = 224
DEFAULT_MODEL = "microsoft/resnet-50"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------
class Classifier(torch.nn.Module):
    """Recebe imagens em [0, 1] e devolve logits; a normalização fica aqui dentro
    para que EPSILON seja medido no espaço de pixels."""

    def __init__(self, model, mean, std):
        super().__init__()
        self.model = model
        self.register_buffer("mean", torch.tensor(mean).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(std).view(1, 3, 1, 1))

    def forward(self, x):
        return self.model(pixel_values=(x - self.mean) / self.std).logits


def load_model(name, random_weights=False):
    from transformers import (AutoImageProcessor, AutoModelForImageClassification,
                              ResNetConfig, ResNetForImageClassification,
                              ViTConfig, ViTForImageClassification)

    is_vit = "vit" in name.lower()
    if random_weights:
        # Teste offline: mesma arquitetura, pesos aleatórios, nada é baixado.
        torch.manual_seed(0)
        if is_vit:
            model = ViTForImageClassification(ViTConfig(num_labels=1000))
        else:
            model = ResNetForImageClassification(ResNetConfig(num_labels=1000))
    else:
        model = AutoModelForImageClassification.from_pretrained(name)

    mean, std = ((0.5,) * 3, (0.5,) * 3) if is_vit else (IMAGENET_MEAN, IMAGENET_STD)
    if not random_weights:
        try:
            proc = AutoImageProcessor.from_pretrained(name)
            mean, std = tuple(proc.image_mean), tuple(proc.image_std)
        except Exception:
            pass
    return Classifier(model, mean, std).eval()


def select_layers(model):
    """Camadas monitoradas: os blocos mais externos cujo nome de classe termina em
    'Layer' (ResNetBottleNeckLayer, ResNetConvLayer do embedder, ViTLayer...)."""
    selected = []
    for name, module in model.named_modules():
        if not type(module).__name__.endswith("Layer"):
            continue
        if any(name.startswith(prev + ".") for prev, _ in selected):
            continue
        selected.append((name, module))
    if not selected:
        raise RuntimeError("Nenhuma camada encontrada para medir cobertura.")
    return selected


class NeuronCoverage:
    """Registra hooks nas camadas e mantém o conjunto de neurônios já cobertos."""

    def __init__(self, model, threshold):
        self.threshold = threshold
        self.layers = select_layers(model)
        self.covered = {}
        self._acts = {}
        for name, module in self.layers:
            module.register_forward_hook(self._hook(name))

    def _hook(self, name):
        def fn(_module, _inputs, output):
            out = output[0] if isinstance(output, (tuple, list)) else output
            if out.dim() == 4:      # CNN: (B, C, H, W) -> média espacial por canal
                act = out.mean(dim=(2, 3))
            elif out.dim() == 3:    # Transformer: (B, T, D) -> média sobre tokens
                act = out.mean(dim=1)
            else:
                act = out.flatten(1)
            self._acts[name] = act.detach().float().cpu()
        return fn

    def batch_activations(self):
        """Para cada entrada do último batch, devolve {camada: máscara de neurônios ativos}."""
        per_layer = {}
        for name, act in self._acts.items():
            lo = act.min(dim=1, keepdim=True).values
            hi = act.max(dim=1, keepdim=True).values
            scaled = (act - lo) / (hi - lo + 1e-8)
            per_layer[name] = (scaled > self.threshold).numpy()
            if name not in self.covered:
                self.covered[name] = np.zeros(act.shape[1], dtype=bool)
        batch_size = next(iter(per_layer.values())).shape[0]
        return [{n: m[i] for n, m in per_layer.items()} for i in range(batch_size)]

    def new_neurons(self, active):
        return int(sum((active[n] & ~self.covered[n]).sum() for n in active))

    def update(self, active):
        for n, mask in active.items():
            self.covered[n] |= mask

    def total(self):
        return sum(c.size for c in self.covered.values())

    def ratio(self):
        return sum(int(c.sum()) for c in self.covered.values()) / max(self.total(), 1)

    def per_layer(self):
        return {n: float(c.mean()) for n, c in self.covered.items()}


# ---------------------------------------------------------------------------
# Mutações (todas operam em tensores (3, H, W) com valores em [0, 1])
# ---------------------------------------------------------------------------
def mut_noise(x, rng):
    return x + torch.randn_like(x) * rng.uniform(0.01, 0.1)


def mut_brightness(x, rng):
    return x + rng.uniform(-0.15, 0.15)


def mut_contrast(x, rng):
    mean = x.mean(dim=(1, 2), keepdim=True)
    return (x - mean) * rng.uniform(0.7, 1.3) + mean


def mut_rotation(x, rng):
    return TF.rotate(x, rng.uniform(-15, 15), interpolation=TF.InterpolationMode.BILINEAR)


def mut_blur(x, rng):
    k = rng.choice([3, 5, 7])
    return TF.gaussian_blur(x, kernel_size=k, sigma=rng.uniform(0.5, 2.0))


def mut_patch(x, rng):
    x = x.clone()
    _, h, w = x.shape
    size = rng.randint(h // 16, h // 5)
    top, left = rng.randint(0, h - size), rng.randint(0, w - size)
    color = torch.tensor([rng.random() for _ in range(3)]).view(3, 1, 1)
    x[:, top:top + size, left:left + size] = color
    return x


MUTATIONS = {
    "noise": mut_noise,
    "brightness": mut_brightness,
    "contrast": mut_contrast,
    "rotation": mut_rotation,
    "blur": mut_blur,
    "patch": mut_patch,
}


def project(x, original, eps):
    """Projeta x na bola L∞ de raio eps em torno da imagem original e em [0, 1]."""
    return torch.clamp(torch.min(torch.max(x, original - eps), original + eps), 0.0, 1.0)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
@dataclass
class Entry:
    image: torch.Tensor     # imagem atual (possivelmente já mutada)
    seed_id: int            # índice da semente de origem
    picks: int = 0          # quantas vezes foi sorteada


def load_seeds(seed_dir):
    paths = sorted(p for p in Path(seed_dir).iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    if not paths:
        raise SystemExit(f"Nenhuma imagem em {seed_dir}/. Coloque de 5 a 20 fotos (.jpg/.png) lá.")
    images = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        img = TF.resize(img, int(IMAGE_SIZE * 256 / 224))
        img = TF.center_crop(img, IMAGE_SIZE)
        images.append(TF.to_tensor(img))
    return paths, images


def pick(corpus, rng):
    """Seleção probabilística do DeepHunter: quanto mais sorteado, menor a chance."""
    weights = [1.0 / (1 + e.picks) for e in corpus]
    entry = rng.choices(corpus, weights=weights, k=1)[0]
    entry.picks += 1
    return entry


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:40] or "x"


# ---------------------------------------------------------------------------
# Laço principal
# ---------------------------------------------------------------------------
def fuzz(args):
    rng = random.Random(args.seed)
    torch.manual_seed(args.seed)
    out = Path(args.out)
    (out / "failures").mkdir(parents=True, exist_ok=True)

    model = load_model(args.model, args.random_weights).to(args.device)
    id2label = model.model.config.id2label
    coverage = NeuronCoverage(model, args.threshold)
    print(f"Modelo: {args.model} | camadas monitoradas: {len(coverage.layers)}")

    paths, seeds = load_seeds(args.seeds)
    with torch.no_grad():
        logits = model(torch.stack(seeds).to(args.device))
    original_labels = logits.argmax(1).tolist()
    for active in coverage.batch_activations():
        coverage.update(active)
    for p, lbl in zip(paths, original_labels):
        print(f"  semente {p.name}: {id2label[lbl]}")
    print(f"Neurônios: {coverage.total()} | cobertura inicial: {coverage.ratio():.2%}\n")

    corpus = [Entry(img, i) for i, img in enumerate(seeds)]
    rows, failures, it = [], 0, 0
    start = time.time()

    while it < args.iters:
        batch = []
        for _ in range(min(args.batch_size, args.iters - it)):
            entry = pick(corpus, rng)
            mutation = rng.choice(list(MUTATIONS))
            original = seeds[entry.seed_id]
            mutant = project(MUTATIONS[mutation](entry.image, rng), original, args.epsilon)
            batch.append((entry, mutation, mutant))

        with torch.no_grad():
            probs = model(torch.stack([m for _, _, m in batch]).to(args.device)).softmax(1).cpu()
        activations = coverage.batch_activations()

        for (entry, mutation, mutant), p, active in zip(batch, probs, activations):
            it += 1
            orig_label = original_labels[entry.seed_id]
            pred = int(p.argmax())
            new = coverage.new_neurons(active)
            coverage.update(active)
            failed = pred != orig_label
            linf = float((mutant - seeds[entry.seed_id]).abs().max())

            if failed:
                failures += 1
                name = (f"{it:05d}_{mutation}_{slug(id2label[orig_label])}"
                        f"_to_{slug(id2label[pred])}.png")
                TF.to_pil_image(mutant).save(out / "failures" / name)
            elif new > 0:
                corpus.append(Entry(mutant, entry.seed_id))

            rows.append({
                "iter": it,
                "seed": paths[entry.seed_id].name,
                "mutation": mutation,
                "coverage": coverage.ratio(),
                "new_neurons": new,
                "orig_label": id2label[orig_label],
                "pred_label": id2label[pred],
                "confidence": float(p[pred]),
                "orig_class_prob": float(p[orig_label]),
                "failure": int(failed),
                "linf": linf,
                "corpus_size": len(corpus),
                "total_failures": failures,
            })

        if it % args.log_every < args.batch_size or it == args.iters:
            print(f"[{it:5d}/{args.iters}] cobertura={coverage.ratio():.2%} "
                  f"falhas={failures} corpus={len(corpus)} ({time.time() - start:.0f}s)")

    log = pd.DataFrame(rows)
    log.to_csv(out / "log.csv", index=False)
    summary = summarize(log, coverage, args, len(seeds), time.time() - start)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    plot(log, out, args.model)
    print_summary(summary, out)


def summarize(log, coverage, args, n_seeds, elapsed):
    by_mut = log.groupby("mutation")["failure"].agg(["count", "sum", "mean"])
    return {
        "model": args.model,
        "random_weights": args.random_weights,
        "iters": int(len(log)),
        "epsilon": args.epsilon,
        "cov_threshold": args.threshold,
        "seeds": n_seeds,
        "failures": int(log["failure"].sum()),
        "failure_rate": float(log["failure"].mean()),
        "seeds_with_failure": int(log.loc[log["failure"] == 1, "seed"].nunique()),
        "final_coverage": coverage.ratio(),
        "final_corpus_size": int(log["corpus_size"].iloc[-1]),
        "neurons": coverage.total(),
        "seconds": round(elapsed, 1),
        "failures_by_mutation": {
            m: {"tried": int(r["count"]), "failures": int(r["sum"]), "rate": float(r["mean"])}
            for m, r in by_mut.iterrows()
        },
        "coverage_by_layer": coverage.per_layer(),
    }


def print_summary(s, out):
    print(f"\nFalhas: {s['failures']}/{s['iters']} ({s['failure_rate']:.2%}) "
          f"em {s['seeds_with_failure']}/{s['seeds']} sementes")
    print(f"Cobertura final: {s['final_coverage']:.2%} | corpus final: {s['final_corpus_size']}")
    print("Falhas por mutação:")
    for m, r in sorted(s["failures_by_mutation"].items(), key=lambda kv: -kv[1]["rate"]):
        print(f"  {m:<11} {r['failures']:>5}/{r['tried']:<5} ({r['rate']:.2%})")
    print(f"\nResultados em {out}/")


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot(log, out, model_name):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(log["iter"], log["coverage"] * 100, color=SERIES_1, linewidth=2)
    ax1.set_ylabel("Cobertura de neurônios (%)")
    ax1.set_title(f"Fuzzing de {model_name}", loc="left")
    ax2.plot(log["iter"], log["total_failures"], color=SERIES_2, linewidth=2)
    ax2.set_ylabel("Falhas acumuladas")
    ax2.set_xlabel("Iteração")
    for ax in (ax1, ax2):
        _style(ax)
    fig.tight_layout()
    fig.savefig(out / "fuzzing.png", dpi=150)
    plt.close(fig)

    rates = log.groupby("mutation")["failure"].mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(rates.index, rates.values, color=SERIES_1, height=0.6)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlabel("Falhas (% das mutações aplicadas)")
    ax.set_title(f"Falhas por tipo de mutação: {model_name}", loc="left")
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_xlim(0, max(rates.max() * 1.2, 1))
    fig.tight_layout()
    fig.savefig(out / "falhas_por_mutacao.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL, help="modelo do Hugging Face")
    ap.add_argument("--iters", type=int, default=2000)
    ap.add_argument("--out", default="results")
    ap.add_argument("--seeds", default="seeds", help="pasta com as imagens semente")
    ap.add_argument("--epsilon", type=float, default=EPSILON)
    ap.add_argument("--threshold", type=float, default=COV_THRESHOLD)
    ap.add_argument("--batch-size", type=int, default=8, help="mutantes avaliados por forward")
    ap.add_argument("--seed", type=int, default=0, help="semente do gerador aleatório")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--log-every", type=int, default=100)
    ap.add_argument("--random-weights", action="store_true",
                    help="usa a arquitetura com pesos aleatórios (teste offline, sem download)")
    fuzz(ap.parse_args())


if __name__ == "__main__":
    main()
