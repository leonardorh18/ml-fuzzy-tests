"""Roda o script de ponta a ponta com clientes falsos (sem rede, sem modelos)."""

import json
from types import SimpleNamespace

import fuzz_chatbots
from chatfuzz.clients import ChatResponse


class EchoExpectedClient:
    """Responde certo nas contas e repete o prompt no resto; serve só para exercitar o código."""

    def __init__(self, spec, cases):
        self.spec = spec
        self.answers = {c.prompt: c.expected for c in cases}

    def chat(self, prompt):
        expected = self.answers[prompt]
        text = str(expected) if isinstance(expected, int) else prompt
        return ChatResponse(self.spec, text)


def test_run_writes_all_outputs(tmp_path, monkeypatch):
    args = SimpleNamespace(models=["api:fake/a", "api:fake/b"], cases=6, variants=2,
                           categories=fuzz_chatbots.CATEGORIES, seed=0, coverage_bias=0.8,
                           out=str(tmp_path), max_tokens=16, temperature=0.0,
                           base_url="http://unused", delay=0.0, resume=False, dry_run=False, analyze=None)
    cases = fuzz_chatbots.GrammarFuzzer(seed=0).generate(6, variants=2)
    monkeypatch.setattr(fuzz_chatbots, "make_client", lambda spec, **kw: EchoExpectedClient(spec, cases))

    fuzz_chatbots.run(args)

    for name in ["cases.jsonl", "responses.jsonl", "records.csv", "findings.csv", "summary.json"]:
        assert (tmp_path / name).exists(), name
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert set(summary["models"]) == {"api:fake/a", "api:fake/b"}
    assert summary["models"]["api:fake/a"]["requests"] == len(cases)
    assert summary["models"]["api:fake/a"]["pass_rate_by_category"]["arith"] == 1.0

    fuzz_chatbots.analyze(tmp_path)  # reanálise a partir dos arquivos salvos
