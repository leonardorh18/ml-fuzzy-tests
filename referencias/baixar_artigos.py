#!/usr/bin/env python3
"""Baixa os PDFs das 20 referências do artigo a partir de fontes de acesso aberto.

Os PDFs ficam em referencias/pdfs/ (fora do git, por direitos autorais). Rode de novo
para recriar a pasta. Referências sem cópia aberta ficam listadas no fim.

Uso:
    python referencias/baixar_artigos.py
"""

import subprocess
import sys
import urllib.request
from pathlib import Path

# chave do .bib -> URL de acesso aberto (None = sem cópia aberta encontrada)
SOURCES = {
    "mckeeman1998differential": None,
    "chen1998metamorphic": "https://arxiv.org/pdf/2002.12543",
    "yang2011csmith": "https://users.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf",
    "holler2012langfuzz": "https://www.usenix.org/system/files/conference/usenixsecurity12/sec12-final73.pdf",
    "barr2015oracle": "https://discovery.ucl.ac.uk/id/eprint/1471263/1/06963470.pdf",
    "pei2017deepxplore": "https://arxiv.org/pdf/1705.06640",
    "havrikov2019kpath": None,
    "ribeiro2020checklist": "https://aclanthology.org/2020.acl-main.442.pdf",
    "zeller2024fuzzingbook": "https://www.fuzzingbook.org/html/GrammarCoverageFuzzer.html",
    "yu2023gptfuzzer": "https://arxiv.org/pdf/2309.10253",
    "zhang2023sac3": "https://aclanthology.org/2023.findings-emnlp.1032.pdf",
    "hyun2024metal": "https://arxiv.org/pdf/2312.06056",
    "wang2024survey": "https://arxiv.org/pdf/2307.07221",
    "sclar2024formatting": "https://arxiv.org/pdf/2310.11324",
    "edman2024cute": "https://aclanthology.org/2024.emnlp-main.177.pdf",
    "cho2025metamorphic": "https://arxiv.org/pdf/2511.02108",
    "guo2026mortar": "https://arxiv.org/pdf/2412.15557",
    "qwen2024qwen25": "https://arxiv.org/pdf/2412.15115",
    "benallal2025smollm2": "https://arxiv.org/pdf/2502.02737",
    "zhang2024tinyllama": "https://arxiv.org/pdf/2401.02385",
}


def html_to_pdf(url, out):
    """Capítulos do Fuzzing Book são páginas HTML: imprime em PDF com o Chromium."""
    script = (
        "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
        f"const p=await b.newPage();await p.goto('{url}',{{waitUntil:'networkidle',timeout:60000}});"
        f"await p.pdf({{path:'{out}',format:'A4',printBackground:true}});await b.close();}})();"
    )
    subprocess.run(["node", "-e", script], check=True)


def main():
    out_dir = Path(__file__).resolve().parent / "pdfs"
    out_dir.mkdir(exist_ok=True)
    missing = []
    for key, url in SOURCES.items():
        target = out_dir / f"{key}.pdf"
        if url is None:
            missing.append(key)
            continue
        if target.exists() and target.stat().st_size > 10_000:
            print(f"ok (já existe)  {key}")
            continue
        try:
            if url.endswith(".html"):
                html_to_pdf(url, target)
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research download)"})
                data = urllib.request.urlopen(req, timeout=60).read()
                if not data.startswith(b"%PDF"):
                    raise ValueError("a resposta não é um PDF")
                target.write_bytes(data)
            print(f"ok              {key}")
        except Exception as e:  # noqa: BLE001
            print(f"FALHOU          {key}: {e}", file=sys.stderr)
            missing.append(key)
    if missing:
        print("\nSem cópia aberta (consultar pela biblioteca da universidade):")
        for key in missing:
            print(f"  - {key}")


if __name__ == "__main__":
    main()
