#!/usr/bin/env python3
"""Compara uma execução nova com a de referência (reprodutibilidade).

Para cada modelo, conta quantos prompts receberam exatamente a mesma resposta nas duas
execuções. Com as revisões fixadas e decodificação gulosa, o esperado é 100% na mesma
pilha de software; diferenças de hardware ou de versão do torch/transformers podem
mudar algumas respostas.

Uso:
    python experiments/compare_runs.py results_local referencia/execucao_principal
"""

import argparse
import json
from pathlib import Path


def load(run):
    out = {}
    with open(Path(run) / "responses.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[(r["model"], r["case_id"])] = r["text"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("new")
    ap.add_argument("reference", nargs="?", default="referencia/execucao_principal")
    ap.add_argument("--show", type=int, default=3, help="exemplos de diferença por modelo")
    args = ap.parse_args()

    new, ref = load(args.new), load(args.reference)
    common = sorted(set(new) & set(ref))
    if not common:
        raise SystemExit("nenhum par (modelo, caso) em comum: confira semente, --cases e --variants")
    print(f"{len(common)} respostas em comum ({len(ref)} na referência, {len(new)} na nova)\n")
    for model in sorted({m for m, _ in common}):
        keys = [k for k in common if k[0] == model]
        diff = [k for k in keys if new[k] != ref[k]]
        print(f"{model:45s} idênticas {len(keys) - len(diff)}/{len(keys)}")
        for k in diff[:args.show]:
            print(f"    {k[1]}: referência={ref[k][:60]!r} | nova={new[k][:60]!r}")


if __name__ == "__main__":
    main()
