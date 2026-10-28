"""Testa a lógica de análise com respostas escritas à mão (não são resultados de modelos)."""

from chatfuzz.analysis import build_records, find_issues, metamorphic_consistency, pairwise_disagreement
from chatfuzz.clients import ChatResponse
from chatfuzz.grammar import TestCase


def case(case_id, group, variant, category, expected):
    return TestCase(case_id=case_id, group_id=group, variant=variant, category=category,
                    prompt=f"prompt {case_id}", expected=expected)


CASES = [
    case("0-0", "0", 0, "arith", 7),
    case("0-1", "0", 1, "arith", 7),
    case("1-0", "1", 0, "edge", None),
]


def r(model, text, error=None):
    return ChatResponse(model=model, text=text, error=error)


def test_differential_metamorphic_and_error_findings():
    responses = [
        ("0-0", r("A", "7")), ("0-0", r("B", "8")),      # A e B discordam; B errou
        ("0-1", r("A", "9")), ("0-1", r("B", "8")),      # A muda de resposta entre paráfrases
        ("1-0", r("A", "ok")), ("1-0", r("B", "", error="http_500")),
    ]
    df = build_records(CASES, responses)
    findings = find_issues(df)
    types = findings["type"].value_counts().to_dict()

    assert types["differential_disagreement"] == 2
    first = findings[(findings["type"] == "differential_disagreement") & (findings["case_id"] == "0-0")]
    assert first["models"].iloc[0] == "B"
    meta = findings[findings["type"] == "metamorphic_inconsistency"]
    assert list(meta["models"]) == ["A"]
    assert types["differential_error"] == 1
    assert types["api_error"] == 1

    assert metamorphic_consistency(df) == {"A": 0.0, "B": 1.0}
    assert pairwise_disagreement(df)["A | B"]["disagreement"] == 1.0
