#!/usr/bin/env python3
"""Compara execuções do fuzz_resnet.py (ex.: ResNet-50 vs ViT).

Uso:
    python compare_results.py results_resnet results_vit --out comparacao.png
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # ordem categorical fixa
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"


def load(run_dir):
    run = Path(run_dir)
    summary = json.loads((run / "summary.json").read_text())
    log = pd.read_csv(run / "log.csv")
    return summary, log


def coverage_failure_correlation(log, window=100):
    """Correlação entre ganho de cobertura e falhas encontradas por janela de iterações."""
    groups = log.groupby((log["iter"] - 1) // window)
    gain = groups["coverage"].last() - groups["coverage"].first()
    fails = groups["failure"].sum()
    if len(gain) < 3 or gain.std() == 0 or fails.std() == 0:
        return float("nan")
    return float(np.corrcoef(gain, fails)[0, 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="pastas geradas pelo fuzz_resnet.py")
    ap.add_argument("--out", default="comparacao.png")
    args = ap.parse_args()

    runs = [load(r) for r in args.runs]
    names = [s["model"].split("/")[-1] for s, _ in runs]

    print(f"{'modelo':<26}{'falhas':>9}{'taxa':>9}{'sementes':>10}{'cobertura':>11}{'corr cob×falha':>16}")
    for name, (s, log) in zip(names, runs):
        corr = coverage_failure_correlation(log)
        print(f"{name:<26}{s['failures']:>9}{s['failure_rate']:>9.2%}"
              f"{s['seeds_with_failure']:>5}/{s['seeds']:<4}{s['final_coverage']:>11.2%}{corr:>16.2f}")

    mutations = sorted({m for s, _ in runs for m in s["failures_by_mutation"]})
    print("\nTaxa de falha por mutação:")
    print(f"{'mutação':<12}" + "".join(f"{n[:16]:>18}" for n in names))
    for m in mutations:
        rates = [s["failures_by_mutation"].get(m, {}).get("rate", 0.0) for s, _ in runs]
        print(f"{m:<12}" + "".join(f"{r:>18.2%}" for r in rates))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    width = 0.8 / len(runs)
    y = np.arange(len(mutations))
    for i, (name, (s, _)) in enumerate(zip(names, runs)):
        rates = [s["failures_by_mutation"].get(m, {}).get("rate", 0.0) * 100 for m in mutations]
        axes[0].barh(y + i * width, rates, height=width - 0.04, color=SERIES[i % len(SERIES)], label=name)
    axes[0].set_yticks(y + width * (len(runs) - 1) / 2, mutations)
    axes[0].set_xlabel("Falhas (% das mutações aplicadas)")
    axes[0].set_title("Falhas por tipo de mutação", loc="left")
    axes[0].grid(axis="x", color=GRID, linewidth=0.8)

    for i, (name, (_, log)) in enumerate(zip(names, runs)):
        axes[1].plot(log["iter"], log["total_failures"], color=SERIES[i % len(SERIES)], linewidth=2, label=name)
    axes[1].set_xlabel("Iteração")
    axes[1].set_ylabel("Falhas acumuladas")
    axes[1].set_title("Falhas acumuladas", loc="left")
    axes[1].grid(axis="y", color=GRID, linewidth=0.8)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(GRID)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"\nGráfico salvo em {args.out}")


if __name__ == "__main__":
    main()
