#!/usr/bin/env python3
"""Ablação 1 (sem modelos): a escolha guiada por cobertura cobre a gramática mais rápido?

Para cada semente e cada valor de coverage_bias, gera prompts um a um e registra a
cobertura da gramática após cada prompt. Compara a escolha aleatória uniforme
(bias 0) com a guiada por cobertura (bias 0.8, o padrão).

Uso:
    python experiments/grammar_coverage.py --out results_ablation
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chatfuzz.grammar import CATEGORIES, GrammarFuzzer  # noqa: E402


def curve(seed, bias, n_prompts):
    fuzzer = GrammarFuzzer(seed=seed, coverage_bias=bias)
    points = []
    for g in range(n_prompts):
        category = CATEGORIES[g % len(CATEGORIES)]
        values, _ = fuzzer.skeleton(category)
        fuzzer.expand(f"<{category}>", values)
        points.append(fuzzer.coverage())
    return points


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--prompts", type=int, default=120)
    ap.add_argument("--biases", type=float, nargs="+", default=[0.0, 0.8])
    ap.add_argument("--out", default="results_ablation")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    result = {}
    for bias in args.biases:
        curves = [curve(s, bias, args.prompts) for s in range(args.seeds)]
        to_full = [next((i + 1 for i, c in enumerate(cv) if c >= 1.0), None) for cv in curves]
        reached = [t for t in to_full if t is not None]
        result[str(bias)] = {
            "mean_curve": [statistics.mean(c[i] for c in curves) for i in range(args.prompts)],
            "coverage_after": {n: statistics.mean(c[n - 1] for c in curves) for n in (6, 12, 24, 48)},
            "prompts_to_full_coverage": {
                "reached": f"{len(reached)}/{args.seeds}",
                "median": statistics.median(reached) if reached else None,
                "min": min(reached) if reached else None,
                "max": max(reached) if reached else None,
            },
        }
        print(f"bias={bias}: cobertura após 6/12/24/48 prompts = "
              + " / ".join(f"{v:.0%}" for v in result[str(bias)]["coverage_after"].values())
              + f" · prompts até 100%: mediana {result[str(bias)]['prompts_to_full_coverage']['median']}"
              + f" ({result[str(bias)]['prompts_to_full_coverage']['reached']} sementes)")
    (out / "grammar_coverage.json").write_text(json.dumps(result, indent=2))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ["#7A8090", "#2a78d6", "#eb6834"]
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, bias in enumerate(args.biases):
        mc = result[str(bias)]["mean_curve"]
        label = "aleatória (bias 0)" if bias == 0 else f"guiada por cobertura (bias {bias})"
        ax.plot(range(1, len(mc) + 1), [c * 100 for c in mc], color=colors[i % 3], lw=2, label=label)
    ax.set_xlabel("Prompts gerados")
    ax.set_ylabel("Cobertura da gramática (%)")
    ax.set_title(f"Cobertura média da gramática ({args.seeds} sementes)", loc="left")
    ax.set_ylim(0, 102)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e4e3df")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "grammar_coverage.png", dpi=150)


if __name__ == "__main__":
    main()
