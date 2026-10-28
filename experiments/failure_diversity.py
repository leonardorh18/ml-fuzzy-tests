#!/usr/bin/env python3
"""Ablação 2 (com modelos): a escolha guiada por cobertura revela falhas mais variadas?

Para cada semente e cada coverage_bias, roda o fuzzer com o mesmo orçamento de prompts
e mede: número de falhas, regras da gramática presentes em prompts que falharam
("regras reveladoras") e assinaturas distintas de falha (categoria + motivo + forma
do pedido).

Uso:
    python experiments/failure_diversity.py --models local:Qwen/Qwen2.5-0.5B-Instruct \
        local:HuggingFaceTB/SmolLM2-360M-Instruct --seeds 0 1 2 --out results_ablation
"""

import argparse
import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fuzz_chatbots  # noqa: E402
from chatfuzz.analysis import build_records  # noqa: E402
from chatfuzz.grammar import CATEGORIES  # noqa: E402


def run_condition(models, seed, bias, cases, out):
    args = SimpleNamespace(models=models, cases=cases, variants=1, categories=CATEGORIES, seed=seed,
                           coverage_bias=bias, out=str(out), max_tokens=256, temperature=0.0,
                           base_url=None, delay=0.0, resume=True, dry_run=False, analyze=None)
    fuzz_chatbots.run(args)
    test_cases, responses = fuzz_chatbots.load_run(out)
    df = build_records(test_cases, responses)
    expansions = {c.case_id: c.expansions for c in test_cases}
    first_rule = {c.case_id: c.expansions[0] if c.expansions else c.category for c in test_cases}
    failed = df[df["passed"] == False]  # noqa: E712
    revealing = {e for cid in failed["case_id"] for e in expansions[cid]}
    signatures = {(r.model, r.category, r.reason, first_rule[r.case_id]) for r in failed.itertuples()}
    graded = df[df["passed"].notna()]
    return {"prompts": int(len(df)), "failures": int(len(failed)),
            "failure_rate": float(len(failed) / len(graded)) if len(graded) else None,
            "revealing_rules": len(revealing), "distinct_signatures": len(signatures)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--biases", type=float, nargs="+", default=[0.0, 0.8])
    ap.add_argument("--cases", type=int, default=30)
    ap.add_argument("--out", default="results_ablation")
    args = ap.parse_args()
    out = Path(args.out)

    rows = []
    for seed in args.seeds:
        for bias in args.biases:
            r = run_condition(args.models, seed, bias, args.cases, out / f"diversity_bias{bias}_seed{seed}")
            rows.append({"seed": seed, "bias": bias, **r})
            print(rows[-1])

    summary = {}
    for bias in args.biases:
        rs = [r for r in rows if r["bias"] == bias]
        summary[str(bias)] = {k: {"mean": statistics.mean(r[k] for r in rs),
                                  "values": [r[k] for r in rs]}
                              for k in ("failures", "revealing_rules", "distinct_signatures")}
    (out / "failure_diversity.json").write_text(json.dumps({"runs": rows, "summary": summary}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
