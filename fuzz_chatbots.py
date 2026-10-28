#!/usr/bin/env python3
"""Fuzzing de chatbots do Hugging Face com gramática e teste diferencial.

1. Uma gramática livre de contexto gera prompts (contas, contagem de letras, inversão
   de strings, pedidos de JSON, cópia literal e entradas Unicode difíceis), com várias
   paráfrases de cada pedido e a resposta esperada quando ela é calculável.
2. Cada prompt é enviado a vários chatbots: modelos baixados e rodados localmente
   (local:) ou a API do Hugging Face (api:).
3. Oráculos verificam cada resposta; o teste diferencial compara os modelos entre si
   e o metamórfico compara as respostas de um modelo às paráfrases.

Uso:
    python fuzz_chatbots.py --out results                      # modelos locais padrão
    python fuzz_chatbots.py --models api:meta-llama/Llama-3.1-8B-Instruct api:Qwen/Qwen2.5-7B-Instruct
    python fuzz_chatbots.py --dry-run                          # só mostra os prompts gerados
    python fuzz_chatbots.py --analyze results                  # refaz a análise de uma execução
"""

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from chatfuzz.analysis import build_records, find_issues, plot, summarize
from chatfuzz.clients import ChatResponse, make_client
from chatfuzz.grammar import CATEGORIES, GrammarFuzzer, TestCase

DEFAULT_MODELS = [
    "local:Qwen/Qwen2.5-0.5B-Instruct",
    "local:HuggingFaceTB/SmolLM2-360M-Instruct",
    "local:TinyLlama/TinyLlama-1.1B-Chat-v1.0",
]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_run(out):
    cases = [TestCase(**c) for c in read_jsonl(out / "cases.jsonl")]
    responses = []
    if (out / "responses.jsonl").exists():
        for r in read_jsonl(out / "responses.jsonl"):
            case_id = r.pop("case_id")
            responses.append((case_id, ChatResponse(**r)))
    return cases, responses


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fuzzer = GrammarFuzzer(seed=args.seed, coverage_bias=args.coverage_bias)
    cases = fuzzer.generate(args.cases, variants=args.variants, categories=args.categories)
    coverage = fuzzer.coverage()
    print(f"{len(cases)} prompts de {args.cases} pedidos · cobertura da gramática: {coverage:.0%}")

    if args.dry_run:
        for c in cases:
            print(f"[{c.case_id}] ({c.category}) esperado={c.expected!r}\n    {c.prompt!r}")
        return

    write_jsonl(out / "cases.jsonl", [asdict(c) for c in cases])
    done = set()
    if args.resume and (out / "responses.jsonl").exists():
        done = {(r["model"], r["case_id"]) for r in read_jsonl(out / "responses.jsonl")}
    elif (out / "responses.jsonl").exists():
        (out / "responses.jsonl").unlink()

    for spec in args.models:
        print(f"\n== {spec}")
        client = make_client(spec, max_tokens=args.max_tokens, **(
            {"temperature": args.temperature, "base_url": args.base_url} if spec.startswith("api:") else {}))
        start = time.time()
        with open(out / "responses.jsonl", "a", encoding="utf-8") as f:
            for i, case in enumerate(cases, 1):
                if (client.spec, case.case_id) in done:
                    continue
                resp = client.chat(case.prompt)
                f.write(json.dumps({"case_id": case.case_id, **asdict(resp)}, ensure_ascii=False) + "\n")
                f.flush()
                if i % 10 == 0 or i == len(cases):
                    print(f"  {i}/{len(cases)} ({time.time() - start:.0f}s)")
                if args.delay:
                    time.sleep(args.delay)

    config = {k: v for k, v in vars(args).items() if k not in ("dry_run", "analyze", "resume")}
    analyze(out, coverage, config)


def analyze(out, coverage=None, config=None):
    out = Path(out)
    cases, responses = load_run(out)
    if not responses:
        raise SystemExit(f"nenhuma resposta em {out}/responses.jsonl")
    df = build_records(cases, responses)
    findings = find_issues(df)
    if config is None and (out / "summary.json").exists():
        old = json.loads((out / "summary.json").read_text())
        config, coverage = old.get("config"), old.get("grammar_coverage")
    summary = summarize(df, findings, coverage, config)

    df.to_csv(out / "records.csv", index=False)
    findings.to_csv(out / "findings.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    plot(df, out)

    print(f"\nAchados: {len(findings)}")
    for t, n in summary["findings_by_type"].items():
        print(f"  {t:<28} {n}")
    print("\nPor modelo:")
    for model, m in summary["models"].items():
        rate = "n/a" if m["pass_rate"] is None else f"{m['pass_rate']:.0%}"
        cons = "n/a" if m["metamorphic_consistency"] is None else f"{m['metamorphic_consistency']:.0%}"
        print(f"  {model:<50} acerto {rate:>4} · consistência {cons:>4} · erros de API {m['api_errors']}")
    print(f"\nResultados em {out}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help="local:<modelo> ou api:<modelo>[:<provedor>]")
    ap.add_argument("--cases", type=int, default=30, help="número de pedidos (esqueletos)")
    ap.add_argument("--variants", type=int, default=2, help="paráfrases por pedido")
    ap.add_argument("--categories", nargs="+", default=CATEGORIES, choices=CATEGORIES)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--coverage-bias", type=float, default=0.8,
                    help="chance de escolher uma expansão ainda não coberta")
    ap.add_argument("--out", default="results")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0, help="só para api:")
    ap.add_argument("--base-url", default="https://router.huggingface.co/v1", help="só para api:")
    ap.add_argument("--delay", type=float, default=0.0, help="segundos entre chamadas")
    ap.add_argument("--resume", action="store_true", help="continua uma execução interrompida")
    ap.add_argument("--dry-run", action="store_true", help="só gera e mostra os prompts")
    ap.add_argument("--analyze", metavar="DIR", help="refaz a análise de uma execução salva")
    args = ap.parse_args()
    if args.analyze:
        analyze(args.analyze)
    else:
        run(args)


if __name__ == "__main__":
    main()
