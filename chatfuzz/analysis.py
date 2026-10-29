"""Análise dos resultados: oráculos, teste diferencial e teste metamórfico.

- Diferencial: o mesmo prompt vai para vários modelos; respostas canônicas diferentes
  são um achado. Quando a resposta esperada é conhecida, o achado diz quem errou.
- Metamórfico: paráfrases do mesmo esqueleto devem receber a mesma resposta do mesmo
  modelo; se não recebem, o modelo é inconsistente.
- Consenso errado: todos os modelos dão a mesma resposta errada, caso que o
  diferencial sozinho não vê; só aparece porque a resposta esperada é conhecida.
"""

import itertools
import json

import pandas as pd

from .oracles import check

COMPARABLE = {"arith", "count", "reverse", "json", "echo"}


def build_records(cases, responses):
    """Une casos e respostas e aplica o oráculo. responses: lista de (case_id, ChatResponse)."""
    by_id = {c.case_id: c for c in cases}
    rows = []
    for case_id, resp in responses:
        case = by_id[case_id]
        verdict = check(case.category, case.expected, resp)
        rows.append({
            "model": resp.model, "case_id": case.case_id, "group_id": case.group_id,
            "variant": case.variant, "category": case.category, "prompt": case.prompt,
            "expected": json.dumps(case.expected, ensure_ascii=False),
            "response": resp.text, "error": resp.error, "status_code": resp.status_code,
            "latency_s": round(resp.latency_s, 3), "truncated": resp.truncated, "passed": verdict.passed,
            "answer": None if verdict.answer is None else json.dumps(verdict.answer, ensure_ascii=False),
            "reason": verdict.reason,
        })
    return pd.DataFrame(rows)


def find_issues(df):
    findings = []

    for r in df.itertuples():
        if r.reason == "api_error":
            findings.append({"type": "api_error", "models": r.model, "case_id": r.case_id,
                             "category": r.category, "detail": r.error})
        elif r.reason == "empty":
            findings.append({"type": "empty_response", "models": r.model, "case_id": r.case_id,
                             "category": r.category, "detail": ""})
        elif r.passed is False:
            findings.append({"type": "oracle_failure", "models": r.model, "case_id": r.case_id,
                             "category": r.category,
                             "detail": f"{r.reason}: esperado {r.expected}, obtido {r.answer}"})

    # Diferencial entre modelos, prompt a prompt.
    for case_id, g in df.groupby("case_id"):
        category = g["category"].iloc[0]
        errored = set(g.loc[g["error"].notna(), "model"])
        if errored and len(errored) < len(g):
            findings.append({"type": "differential_error", "models": ", ".join(sorted(errored)),
                             "case_id": case_id, "category": category,
                             "detail": "erro de API em uns modelos e resposta em outros"})
        if category not in COMPARABLE:
            continue
        answered = g[g["answer"].notna()]
        if (len(answered) == len(g) > 1 and answered["answer"].nunique() == 1
                and (answered["passed"] == False).all()):  # noqa: E712
            findings.append({"type": "consensus_wrong", "models": ", ".join(sorted(g["model"])),
                             "case_id": case_id, "category": category,
                             "detail": f"esperado {g['expected'].iloc[0]} | todos responderam {answered['answer'].iloc[0]}"})
        if answered["answer"].nunique() > 1:
            wrong = sorted(answered.loc[answered["passed"] == False, "model"])  # noqa: E712
            detail = "; ".join(f"{m}={a}" for m, a in zip(answered["model"], answered["answer"]))
            findings.append({"type": "differential_disagreement", "models": ", ".join(wrong),
                             "case_id": case_id, "category": category,
                             "detail": f"esperado {g['expected'].iloc[0]} | {detail}"})

    # Metamórfico: o mesmo modelo, paráfrases do mesmo esqueleto.
    comparable = df[df["category"].isin(COMPARABLE)]
    for (model, group_id), g in comparable.groupby(["model", "group_id"]):
        if len(g) < 2:
            continue
        answers = g["answer"].fillna("<sem resposta>")
        if answers.nunique() > 1:
            detail = "; ".join(f"v{v}={a}" for v, a in zip(g["variant"], answers))
            findings.append({"type": "metamorphic_inconsistency", "models": model,
                             "case_id": group_id, "category": g["category"].iloc[0], "detail": detail})

    return pd.DataFrame(findings, columns=["type", "models", "case_id", "category", "detail"])


def metamorphic_consistency(df):
    comparable = df[df["category"].isin(COMPARABLE)]
    out = {}
    for model, g in comparable.groupby("model"):
        groups = [x["answer"].fillna("<sem resposta>").nunique() == 1
                  for _, x in g.groupby("group_id") if len(x) > 1]
        out[model] = sum(groups) / len(groups) if groups else None
    return out


def pairwise_disagreement(df):
    comparable = df[df["category"].isin(COMPARABLE) & df["answer"].notna()]
    pivot = comparable.pivot_table(index="case_id", columns="model", values="answer", aggfunc="first")
    models = list(pivot.columns)
    matrix = {}
    for a, b in itertools.combinations(models, 2):
        both = pivot[[a, b]].dropna()
        if len(both):
            matrix[f"{a} | {b}"] = {"cases": len(both), "disagreement": float((both[a] != both[b]).mean())}
    return matrix


def summarize(df, findings, grammar_coverage, config):
    graded = df[df["passed"].notna()]
    per_model = {}
    consistency = metamorphic_consistency(df)
    for model, g in df.groupby("model"):
        gg = graded[graded["model"] == model]
        per_model[model] = {
            "requests": int(len(g)),
            "api_errors": int((g["reason"] == "api_error").sum()),
            "empty_responses": int((g["reason"] == "empty").sum()),
            "truncated_responses": int(g["truncated"].sum()),
            "failures_when_truncated": int(((g["passed"] == False) & g["truncated"]).sum()),  # noqa: E712
            "pass_rate": float(gg["passed"].mean()) if len(gg) else None,
            "pass_rate_by_category": {c: float(x["passed"].mean()) for c, x in gg.groupby("category")},
            "metamorphic_consistency": consistency.get(model),
            "mean_latency_s": float(g["latency_s"].mean()),
        }
    return {
        "config": config,
        "cases": int(df["case_id"].nunique()),
        "groups": int(df["group_id"].nunique()),
        "grammar_coverage": grammar_coverage,
        "findings_by_type": findings["type"].value_counts().to_dict(),
        "models": per_model,
        "pairwise_disagreement": pairwise_disagreement(df),
    }


SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"


def plot(df, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    graded = df[df["passed"].notna()].copy()
    graded["passed"] = graded["passed"].astype(float)
    rates = graded.pivot_table(index="category", columns="model", values="passed", aggfunc="mean") * 100
    if rates.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width = 0.8 / len(rates.columns)
    for i, model in enumerate(rates.columns):
        xs = [j + i * width for j in range(len(rates.index))]
        ax.bar(xs, rates[model].values, width=width - 0.03, color=SERIES[i % len(SERIES)], label=model)
    ax.set_xticks([j + width * (len(rates.columns) - 1) / 2 for j in range(len(rates.index))], rates.index)
    ax.set_ylabel("Respostas corretas (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Taxa de acerto por categoria", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "acerto_por_categoria.png", dpi=150)
    plt.close(fig)
