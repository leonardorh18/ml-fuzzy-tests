"""Oráculos: decidem se uma resposta passou e extraem a resposta canônica.

A resposta canônica (um número, uma string normalizada, a lista de chaves de um
JSON) é o que o teste diferencial compara entre modelos e entre paráfrases.
"""

import json
import re
from dataclasses import dataclass

INT_RE = re.compile(r"[-−]?\d[\d,]*")


@dataclass
class Verdict:
    passed: bool | None      # None = categoria sem resposta esperada (só verifica erro)
    answer: object           # resposta canônica, ou None se não deu para extrair
    reason: str              # "ok", "api_error", "empty", "no_number", "wrong_answer", ...


def extract_int(text):
    """Último inteiro do texto ("3 + 4 = 7" -> 7), aceitando separador de milhar e o sinal −."""
    matches = INT_RE.findall(text)
    if not matches:
        return None
    token = matches[-1].replace("−", "-").replace(",", "")
    try:
        return int(token)
    except ValueError:
        return None


def normalize_text(text):
    """Remove espaços, crases, aspas e ponto final em volta da resposta."""
    t = re.sub(r"^```\w*\s*|\s*```$", "", text.strip()).strip()
    previous = None
    while t != previous:
        previous = t
        t = t.strip("`\"'“”‘’ \n").rstrip(".")
    return t


def parse_json_object(text):
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()).strip()
    try:
        obj = json.loads(t)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def check(category, expected, response):
    """Aplica o oráculo da categoria a um ChatResponse."""
    if response.error:
        return Verdict(False, None, "api_error")
    text = response.text or ""
    if not text.strip():
        return Verdict(False, None, "empty")

    if category in ("arith", "count"):
        value = extract_int(text)
        if value is None:
            return Verdict(False, None, "no_number")
        return Verdict(value == expected, value, "ok" if value == expected else "wrong_answer")

    if category == "reverse":
        value = normalize_text(text)
        return Verdict(value == expected, value, "ok" if value == expected else "wrong_answer")

    if category == "json":
        obj = parse_json_object(text)
        if obj is None:
            return Verdict(False, None, "invalid_json")
        keys = sorted(obj)
        missing = set(expected) - set(keys)
        return Verdict(not missing, keys, "ok" if not missing else "missing_keys")

    if category == "echo":
        ok = expected in text
        return Verdict(ok, ok, "ok" if ok else "not_verbatim")

    if category == "edge":
        return Verdict(None, None, "ok")

    raise ValueError(f"categoria desconhecida: {category}")
