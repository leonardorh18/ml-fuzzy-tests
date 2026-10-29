#!/usr/bin/env python3
"""Estatísticas e figuras do artigo, calculadas a partir dos resultados salvos.

Lê a execução principal (records.csv), as ablações e, se existir, a validação manual
dos oráculos; grava paper_stats.json e as figuras em paper/figures/.

Uso:
    python experiments/paper_stats.py --run results_local --ablation results_ablation \
        --validation validation/oracle_validation.csv --out results_local/paper_stats.json
"""

import argparse
import itertools
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chatfuzz.analysis import GRID, SERIES, TEXT_SECONDARY  # noqa: E402

# Categorias cuja resposta canônica não depende do oráculo (no echo ela é o próprio veredito).
INDEPENDENT = ["arith", "count", "reverse", "json"]
SHORT = {"local:Qwen/Qwen2.5-0.5B-Instruct": "Qwen2.5-0.5B",
         "local:HuggingFaceTB/SmolLM2-360M-Instruct": "SmolLM2-360M",
         "local:TinyLlama/TinyLlama-1.1B-Chat-v1.0": "TinyLlama-1.1B"}


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def rate(series):
    k, n = int(series.sum()), int(len(series))
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "ci95": [lo, hi]}


def mcnemar_exact(b, c):
    """p-valor bilateral exato do teste de McNemar (binomial nos pares discordantes)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def lenient_json(text, expected):
    """Oráculo tolerante: aceita o primeiro objeto JSON embutido no texto (análise de sensibilidade)."""
    for m in re.finditer(r"\{", text or ""):
        depth = 0
        for j in range(m.start(), len(text)):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                try:
                    obj = json.loads(text[m.start():j + 1])
                except ValueError:
                    break
                return isinstance(obj, dict) and set(expected) <= set(obj)
    return False


def failure_details(df, cases):
    """Números citados no texto da RQ1/RQ2 que dependem dos valores sorteados."""
    values = {c["case_id"]: c["values"] for c in cases}
    out = {}
    a = df[df["category"] == "arith"].copy()
    a["large"] = a["case_id"].map(lambda i: max(abs(values[i]["a"]), abs(values[i]["b"])) >= 1000)
    out["arith_pass_by_operand"] = {("large" if k else "small"): rate(g["passed"].astype(bool))
                                    for k, g in a.groupby("large")}
    wrong = a[(a["passed"] == False) & a["answer"].notna()]  # noqa: E712
    ratio = (pd.to_numeric(wrong["answer"]).abs() + 1) / (pd.to_numeric(wrong["expected"]).abs() + 1)
    out["arith_wrong_within_10x"] = rate((ratio > 0.1) & (ratio < 10))
    r = df[df["category"] == "reverse"]
    same = [str(ans).strip('"') == values[cid]["token"] for cid, ans in zip(r["case_id"], r["answer"])]
    out["reverse_returned_input"] = r.assign(same=same).groupby("model")["same"].sum().astype(int).to_dict()
    # Prompts com respostas divergentes: quantos modelos acertaram?
    g = df[df["category"].isin(INDEPENDENT)]
    resolved = {0: 0, 1: 0, 2: 0, 3: 0}
    for _, x in g.groupby("case_id"):
        if x["answer"].fillna("<none>").nunique() > 1:
            resolved[int(x["passed"].astype(bool).sum())] += 1
    out["disagreeing_prompts_by_correct_models"] = resolved
    return out


def main_run_stats(df):
    graded = df[df["passed"].notna()].copy()
    graded["passed"] = graded["passed"].astype(bool)
    out = {"responses": int(len(df)), "prompts": int(df["case_id"].nunique()),
           "skeletons": int(df["group_id"].nunique()),
           "prompts_by_category": df.drop_duplicates("case_id")["category"].value_counts().to_dict()}

    out["pass_rate"] = {m: rate(g["passed"]) for m, g in graded.groupby("model")}
    out["pass_rate_by_category"] = {m: {c: rate(x["passed"]) for c, x in g.groupby("category")}
                                    for m, g in graded.groupby("model")}
    out["reasons"] = {m: g["reason"].value_counts().to_dict() for m, g in df.groupby("model")}

    # Comparação pareada entre modelos (mesmos prompts): McNemar exato.
    pivot = graded.pivot_table(index="case_id", columns="model", values="passed", aggfunc="first")
    out["mcnemar"] = {}
    for a, b in itertools.combinations(pivot.columns, 2):
        both = pivot[[a, b]].dropna().astype(bool)
        only_a = int((both[a] & ~both[b]).sum())
        only_b = int((~both[a] & both[b]).sum())
        out["mcnemar"][f"{SHORT[a]} vs {SHORT[b]}"] = {"n": int(len(both)), "only_first": only_a,
                                                       "only_second": only_b, "p": mcnemar_exact(only_a, only_b)}

    # Prompts em que todos erram, e em que todos erram com a mesma resposta.
    per_case = graded.groupby("case_id")
    all_wrong = [cid for cid, g in per_case if not g["passed"].any()]
    same_wrong = [cid for cid in all_wrong
                  if (a := df[df["case_id"] == cid]["answer"]).notna().all() and a.nunique() == 1]
    all_right = [cid for cid, g in per_case if g["passed"].all()]
    out["all_models_wrong"] = len(all_wrong)
    out["all_models_wrong_by_category"] = (graded[graded["case_id"].isin(all_wrong)]
                                           .drop_duplicates("case_id")["category"].value_counts().to_dict())
    out["consensus_wrong"] = len(same_wrong)
    out["all_models_right"] = len(all_right)
    out["graded_prompts"] = int(graded["case_id"].nunique())

    # RQ2: o que os oráculos sem resposta conhecida veriam. Por resposta:
    #  - diferencial: a resposta canônica difere da de pelo menos um outro modelo no mesmo prompt
    #    (ou o modelo não produziu resposta canônica e outro produziu);
    #  - metamórfico: o modelo não deu a mesma resposta canônica a todas as paráfrases.
    ind = df[df["category"].isin(INDEPENDENT)].copy()
    ind["passed"] = ind["passed"].astype(bool)
    ind["ans"] = ind["answer"].fillna("<none>")
    ind["diff_flag"] = ind.groupby("case_id")["ans"].transform(lambda s: s.nunique() > 1)
    ind["meta_flag"] = ind.groupby(["model", "group_id"])["ans"].transform(lambda s: s.nunique() > 1)
    fail = ~ind["passed"]
    rq2 = {"responses": int(len(ind)), "failures": int(fail.sum())}
    for name, flag in [("differential", ind["diff_flag"]), ("metamorphic", ind["meta_flag"]),
                       ("either", ind["diff_flag"] | ind["meta_flag"])]:
        tp = int((flag & fail).sum())
        rq2[name] = {"flagged": int(flag.sum()), "failures_flagged": tp,
                     "recall": tp / int(fail.sum()), "precision": tp / int(flag.sum()) if flag.sum() else None}
    rq2["failures_missed_by_both"] = int((fail & ~ind["diff_flag"] & ~ind["meta_flag"]).sum())
    rq2["by_category"] = {}
    for c, g in ind.groupby("category"):
        f = ~g["passed"]
        either = g["diff_flag"] | g["meta_flag"]
        rq2["by_category"][c] = {"failures": int(f.sum()),
                                 "recall_either": float((either & f).sum() / f.sum()) if f.sum() else None,
                                 "precision_either": float((either & f).sum() / either.sum()) if either.sum() else None}
    out["rq2_oracles_without_ground_truth"] = rq2

    # Metamórfico com a resposta conhecida: o modelo acerta umas paráfrases e erra outras?
    meta = {}
    for m, g in graded[graded["category"].isin(INDEPENDENT + ["echo"])].groupby("model"):
        kinds = {"all_correct": 0, "all_wrong": 0, "mixed": 0}
        for _, x in g.groupby("group_id"):
            kinds["all_correct" if x["passed"].all() else "all_wrong" if not x["passed"].any() else "mixed"] += 1
        meta[m] = kinds
    out["paraphrase_groups"] = meta

    # Respostas cortadas no limite de tokens e custo.
    out["truncated"] = {m: {"all": int(g["truncated"].sum()),
                            "edge": int(g.loc[g["category"] == "edge", "truncated"].sum())}
                        for m, g in df.groupby("model")}
    out["latency"] = {m: {"mean_s": float(g["latency_s"].mean()), "median_s": float(g["latency_s"].median()),
                          "total_min": float(g["latency_s"].sum() / 60)} for m, g in df.groupby("model")}
    out["total_compute_min"] = float(df["latency_s"].sum() / 60)
    out["failures_total"] = int((~graded["passed"]).sum())

    # Prompts repetidos (o sorteio pode repetir um esqueleto): com decodificação gulosa,
    # o mesmo prompt deve receber a mesma resposta do mesmo modelo.
    unique = df.drop_duplicates("case_id")
    out["unique_prompts"] = int(unique["prompt"].nunique())
    rep = df[df["prompt"].isin(unique.loc[unique["prompt"].duplicated(), "prompt"])]
    same = rep.groupby(["model", "prompt"])["response"].nunique() == 1
    out["repeated_prompt_pairs"] = {"model_prompt_pairs": int(len(same)), "identical_responses": int(same.sum())}

    # Sensibilidade do oráculo de JSON: aceitar JSON embutido em texto.
    js = df[df["category"] == "json"]
    out["json_lenient_pass_rate"] = {
        m: rate(pd.Series([lenient_json(t, json.loads(e)) for t, e in zip(g["response"].fillna(""), g["expected"])]))
        for m, g in js.groupby("model")}
    return out


def validation_stats(val):
    v = val.dropna(subset=["human_correct"]).copy()
    v["auto"] = v["auto_passed"].astype(bool)
    v["human"] = v["human_correct"].astype(bool)
    agree = v["auto"] == v["human"]
    tp = int((v["auto"] & v["human"]).sum())
    tn = int((~v["auto"] & ~v["human"]).sum())
    fp = int((v["auto"] & ~v["human"]).sum())   # oráculo aprovou, julgamento reprova
    fn = int((~v["auto"] & v["human"]).sum())   # oráculo reprovou, julgamento aprova
    n = len(v)
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / n ** 2
    out = {"n": n, "agreement": rate(agree), "cohen_kappa": (po - pe) / (1 - pe) if pe < 1 else None,
           "oracle_pass_human_fail": fp, "oracle_fail_human_pass": fn, "both_pass": tp, "both_fail": tn,
           "by_category": {c: {"n": int(len(g)), "agreement": float((g["auto"] == g["human"]).mean())}
                           for c, g in v.groupby("category")},
           "disagreements": v.loc[~agree, ["model", "case_id", "category", "auto_passed", "human_correct",
                                           "note"]].to_dict("records")}
    if "format_ok" in v:
        f = v.dropna(subset=["format_ok"])
        out["format_ok_rate"] = rate(f["format_ok"].astype(bool))
        strict = f["format_ok"].astype(bool)
        out["agreement_strict"] = rate(f["auto_passed"].astype(bool) == strict)
        out["strict_oracle_pass_human_fail"] = int((f["auto_passed"].astype(bool) & ~strict).sum())
    return out


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)


def figures(stats, coverage, fig_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "font.family": "serif"})
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Pass rate por categoria com IC de 95%.
    cats = ["arith", "count", "reverse", "json", "echo"]
    models = [m for m in SHORT if m in stats["pass_rate_by_category"]]
    fig, ax = plt.subplots(figsize=(6.2, 2.7))
    w = 0.8 / len(models)
    for i, m in enumerate(models):
        d = stats["pass_rate_by_category"][m]
        ys = [d[c]["rate"] * 100 for c in cats]
        lo = [ys[j] - d[c]["ci95"][0] * 100 for j, c in enumerate(cats)]
        hi = [d[c]["ci95"][1] * 100 - ys[j] for j, c in enumerate(cats)]
        xs = [j + (i - (len(models) - 1) / 2) * w for j in range(len(cats))]
        ax.bar(xs, ys, w * 0.92, color=SERIES[i], label=SHORT[m], yerr=[lo, hi],
               error_kw={"elinewidth": 0.7, "capsize": 1.5, "ecolor": TEXT_SECONDARY})
    ax.set_xticks(range(len(cats)), cats)
    ax.set_ylabel("Correct replies (%)")
    ax.set_ylim(0, 100)
    style(ax)
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "pass_rate_by_category.pdf")
    plt.close(fig)

    # Curva de cobertura da gramática (Ablação 1).
    fig, ax = plt.subplots(figsize=(6.2, 2.4))
    for i, (b, label) in enumerate([("0.8", "coverage-guided ($b=0.8$)"), ("0.0", "random ($b=0$)")]):
        curve = [x * 100 for x in coverage[b]["mean_curve"]]
        ax.plot(range(1, len(curve) + 1), curve, color=SERIES[i], label=label, lw=1.6)
    ax.set_xlabel("Prompts generated")
    ax.set_ylabel("Grammar coverage (%)")
    ax.set_ylim(0, 102)
    style(ax)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(fig_dir / "grammar_coverage.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results_local")
    ap.add_argument("--ablation", default="results_ablation")
    ap.add_argument("--validation", default="validation/oracle_validation.csv")
    ap.add_argument("--figures", default="paper/figures")
    ap.add_argument("--out", default="results_local/paper_stats.json")
    args = ap.parse_args()

    df = pd.read_csv(Path(args.run) / "records.csv")
    stats = {"main_run": main_run_stats(df)}
    cases = [json.loads(line) for line in open(Path(args.run) / "cases.jsonl")]
    stats["main_run"]["failure_details"] = failure_details(df, cases)
    cov_path = Path(args.ablation) / "grammar_coverage.json"
    coverage = json.loads(cov_path.read_text()) if cov_path.exists() else None
    if coverage:
        stats["grammar_coverage"] = {b: {k: v for k, v in d.items() if k != "mean_curve"} for b, d in coverage.items()}
    div_path = Path(args.ablation) / "failure_diversity.json"
    if div_path.exists():
        stats["failure_diversity"] = json.loads(div_path.read_text())
    edge_path = Path(args.validation).parent / "edge_labels.csv"
    if edge_path.exists():
        e = pd.read_csv(edge_path)
        stats["edge_labels"] = {m: g["label"].value_counts().to_dict() for m, g in e.groupby("model")}
        stats["edge_labels"]["all"] = e["label"].value_counts().to_dict()
    if Path(args.validation).exists():
        stats["oracle_validation"] = validation_stats(pd.read_csv(args.validation))

    Path(args.out).write_text(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
    if coverage:
        figures(stats["main_run"], coverage, Path(args.figures))
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
