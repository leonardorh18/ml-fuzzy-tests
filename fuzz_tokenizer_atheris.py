#!/usr/bin/env python3
"""Fuzzing clássico guiado por cobertura de código do tokenizer do DistilBERT, com Atheris.

O Atheris (libFuzzer para Python) gera bytes, mede quais linhas/ramos do código
Python foram executados e guarda no corpus as entradas que aumentam a cobertura.
Cada entrada vira (max_length, texto Unicode) e passa pelo tokenizer. Oráculos:

    1. A chamada não pode lançar exceção.
    2. O número de tokens respeita max_length.
    3. Todos os ids estão dentro do vocabulário.
    4. Metamórfico: decode(encode(texto)) é estável quando aplicado duas vezes,
       isto é, d1 = decode(encode(texto)) e d2 = decode(encode(d1)) são iguais.

Qualquer violação lança OracleViolation; o Atheris salva a entrada em crash-<hash>.

Uso:
    mkdir corpus
    python fuzz_tokenizer_atheris.py corpus -max_total_time=300
    python fuzz_tokenizer_atheris.py crash-<hash>        # reproduz um crash

Variáveis de ambiente:
    FUZZ_TOKENIZER   modelo ou pasta local do tokenizer (padrão: distilbert-base-uncased)
    FUZZ_SLOW=1      usa o tokenizer em Python puro (use_fast=False, requer
                     transformers<5); o tokenizer rápido é Rust e o Atheris não
                     enxerga a cobertura dentro dele
    FUZZ_SURROGATES=1  permite surrogates Unicode isolados no texto
"""

import os
import sys

import atheris

with atheris.instrument_imports():
    from transformers import AutoTokenizer
    from transformers.utils import logging as hf_logging

TOKENIZER_NAME = os.environ.get("FUZZ_TOKENIZER", "distilbert-base-uncased")
USE_FAST = os.environ.get("FUZZ_SLOW", "0") != "1"
ALLOW_SURROGATES = os.environ.get("FUZZ_SURROGATES", "0") == "1"
MIN_MAX_LENGTH = 2      # [CLS] + [SEP]
MAX_MAX_LENGTH = 512

hf_logging.set_verbosity_error()
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, use_fast=USE_FAST)
VOCAB_SIZE = len(tokenizer)     # inclui tokens adicionados


class OracleViolation(AssertionError):
    pass


def check(condition, oracle, text, detail):
    if not condition:
        raise OracleViolation(f"[oráculo {oracle}] {detail}\n  texto={text!r}")


def roundtrip(text):
    # Sem truncamento: o oráculo metamórfico testa só encode/decode, não o corte.
    ids = tokenizer(text, add_special_tokens=False, truncation=False)["input_ids"]
    return tokenizer.decode(ids, skip_special_tokens=True)


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    max_length = fdp.ConsumeIntInRange(MIN_MAX_LENGTH, MAX_MAX_LENGTH)
    if ALLOW_SURROGATES:
        text = fdp.ConsumeUnicode(fdp.remaining_bytes())
    else:
        text = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())

    # Oráculo 1: qualquer exceção aqui é reportada pelo Atheris como crash.
    enc = tokenizer(text, truncation=True, max_length=max_length)
    ids = enc["input_ids"]

    # Oráculo 2
    check(len(ids) <= max_length, 2, text,
          f"{len(ids)} tokens com max_length={max_length}")

    # Oráculo 3
    bad = [i for i in ids if not 0 <= i < VOCAB_SIZE]
    check(not bad, 3, text, f"ids fora do vocabulário (tamanho {VOCAB_SIZE}): {bad[:10]}")

    # Oráculo 4 (metamórfico)
    d1 = roundtrip(text)
    d2 = roundtrip(d1)
    check(d1 == d2, 4, text, f"decode/encode instável\n  d1={d1!r}\n  d2={d2!r}")


def main():
    print(f"Tokenizer: {TOKENIZER_NAME} ({type(tokenizer).__name__}, "
          f"fast={tokenizer.is_fast}, vocab={VOCAB_SIZE})", file=sys.stderr)
    if not USE_FAST and tokenizer.is_fast:
        print("AVISO: FUZZ_SLOW=1 pediu o tokenizer em Python, mas esta versão do "
              "transformers só oferece o rápido (Rust). Use transformers<5 para o "
              "tokenizer em Python puro.", file=sys.stderr)
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
