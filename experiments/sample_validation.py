#!/usr/bin/env python3
"""RQ4: sorteia uma amostra estratificada de respostas para julgamento manual.

Quatro respostas por (modelo, categoria verificável), semente fixa. O arquivo gerado tem
as colunas human_correct (a resposta dá a resposta certa, mesmo com texto extra),
format_ok (além disso, segue o pedido de formato, como "only the number") e note,
que são preenchidas à mão.

Uso:
    python experiments/sample_validation.py --run results_local --out validation/oracle_validation.csv
"""

import argparse
from pathlib import Path

import pandas as pd

CATEGORIES = ["arith", "count", "reverse", "json", "echo"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results_local")
    ap.add_argument("--per-cell", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="validation/oracle_validation.csv")
    args = ap.parse_args()

    df = pd.read_csv(Path(args.run) / "records.csv")
    df = df[df["category"].isin(CATEGORIES)]
    sample = pd.concat([g.sample(n=min(args.per_cell, len(g)), random_state=args.seed)
                        for _, g in df.groupby(["model", "category"])])
    sample = sample.rename(columns={"passed": "auto_passed"})
    sample = sample[["model", "case_id", "category", "prompt", "expected", "response", "auto_passed", "reason"]]
    sample["human_correct"] = ""
    sample["format_ok"] = ""
    sample["note"] = ""
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.out, index=False)
    print(f"{len(sample)} respostas em {args.out}")


if __name__ == "__main__":
    main()
