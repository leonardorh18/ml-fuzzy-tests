# Método de busca dos trabalhos relacionados

> **Conteúdo gerado por IA (Claude).** A busca foi feita por agentes de IA (Claude Code) em 28 e 29/10/2026. Este arquivo descreve o processo para que ele possa ser repetido, auditado ou descrito no artigo.

## 1. Objetivo

Encontrar trabalhos reais, verificáveis e citáveis para a fundamentação e os trabalhos relacionados do artigo "Grammar-Based Differential Fuzzing of Hugging Face Chatbots", e escolher no máximo 20 referências: **trabalhos clássicos** para a base teórica e **trabalhos atuais (2023–2026)** para teste de LLMs e chatbots.

## 2. Estratégia

A busca foi dividida em quatro temas, cada um pesquisado por um agente em paralelo, com perguntas-chave fixadas antes de começar:

| Tema | Perguntas-chave | Termos e trabalhos-semente |
| --- | --- | --- |
| 1. Fuzzing com gramática e cobertura de gramática | Quais são os fuzzers de gramática fundamentais? Que trabalhos definem cobertura de gramática? Alguém gera prompts de LLM com gramática? | grammar-based fuzzing, grammar coverage, k-path coverage, LangFuzz, Nautilus, Grammarinator, Superion, Gramatron, The Fuzzing Book |
| 2. Teste diferencial | Quais os trabalhos clássicos? Como foi aplicado a sistemas de deep learning? E a LLMs? | differential testing, McKeeman 1998, Csmith, EMI, DeepXplore, CRADLE, FreeFuzz, TitanFuzz, Fuzz4All |
| 3. Problema do oráculo e teste metamórfico | Quais os surveys de base? Como o teste metamórfico foi aplicado a NLP e a LLMs? Consistência sob paráfrase? | test oracle problem, metamorphic testing, metamorphic relations, CheckList, paraphrase robustness, prompt sensitivity, self-consistency |
| 4. Fuzzing e teste de LLMs e chatbots | Fuzzing de LLMs, seguimento de formato (JSON), falhas de tokenização (contagem de letras, inversão), modelos pequenos | LLM fuzzing, jailbreak fuzzing, chatbot testing, instruction following, IFEval, tokenization, character-level, Qwen2.5, SmolLM2, TinyLlama |

Um quinto agente consolidou as notas dos quatro num relatório único (`reports/Trabalhos relacionados fuzzing de chatbots.md`).

## 3. Fontes consultadas

- **Usadas:** API de metadados de DOI do Crossref (`api.crossref.org`), API do arXiv (`export.arxiv.org`), buscadores web e, quando acessíveis, páginas oficiais dos anais.
- **Bloqueadas no ambiente durante a busca de 28/10:** páginas do arXiv, DBLP (tela anti-robô), ACM Digital Library, IEEE Xplore, Semantic Scholar (limite de requisições), USENIX e NDSS. Por isso, não foi possível fazer uma busca sistemática nesses índices; o artigo diz "to our knowledge" ao afirmar a lacuna.
- **No download de 29/10**, arXiv, ACL Anthology, USENIX e páginas de autores já estavam acessíveis.

## 4. Critérios

**Inclusão:**
- existência confirmada pelo registro de DOI (Crossref) ou pelo registro do arXiv; nada citado só de memória;
- trabalhos revisados por pares de 2018 a 2026, mais os clássicos de cada tema;
- relação direta com uma parte do nosso método (gerador, oráculo diferencial, oráculo metamórfico, alvo do teste).

**Exclusão:**
- trabalhos sobre a "reversal curse" (inverter fatos, não strings), por confundirem o leitor;
- trabalhos cuja venue ou autoria não pôde ser confirmada, quando havia alternativa verificada para a mesma ideia.

**Marcação de verificação** (no relatório consolidado): `CR` = registro do Crossref conferido; `AX` = registro do arXiv conferido; `WS` = existência vista só em resultado de busca; `P` = verificado em parte.

## 5. Funil de seleção

| Etapa | Trabalhos |
| --- | --- |
| Levantados pelos quatro agentes (somando as notas) | ≈150 |
| Selecionados no relatório consolidado (12 por tema + extras) | ≈90 |
| Citados no primeiro rascunho do artigo | 47 |
| **Versão final (pedido do grupo: no máximo 20)** | **20** |

Critérios do corte final para 20:
1. **Base teórica com clássicos:** McKeeman 1998 (teste diferencial), Chen et al. 1998 (teste metamórfico), Csmith 2011, LangFuzz 2012, Barr et al. 2015 (oráculo), DeepXplore 2017, Havrikov & Zeller 2019 (cobertura de gramática), CheckList 2020 e o capítulo do Fuzzing Book.
2. **Teste de LLMs com trabalhos de 2023 a 2026:** GPTFuzzer, SAC3, METAL, o survey de Wang et al., Sclar et al., CUTE, Cho et al. 2025 e MORTAR (2026).
3. **Os três relatórios técnicos dos modelos testados**, obrigatórios para descrever o alvo.
4. Uma referência por ideia; entre duas equivalentes, ficou a verificada e revisada por pares.

Referências que saíram no corte (podem voltar se o grupo quiser mais profundidade): Purdom 1972, Skyfire, Nautilus, Superion, Gramatron, Inputs From Hell, Havrikov et al. 2022, Davis & Weyuker 1981, Chen et al. 2016, CRADLE, TitanFuzz, SelfCheckGPT, Weyuker 1982, TransRepair, Elazar et al. 2021, Mizrahi et al. 2024, Errica et al. 2025, Drowzee, Self-Consistency, FuzzLLM, h4rm3l, Bozic & Wotawa, DialTest, IFEval, Chai et al., Fishing for Magikarp e GSM-Symbolic.

## 6. Download dos artigos

Script: `referencias/baixar_artigos.py`. Fontes de acesso aberto, nesta ordem de preferência: anais oficiais abertos (ACL Anthology, USENIX), arXiv, preprint dos autores, repositório institucional (UCL Discovery). O capítulo do Fuzzing Book é uma página web e foi impresso em PDF.

- **Baixados:** 18 de 20. Cada PDF foi conferido pelo título da primeira página.
- **Sem cópia aberta:** McKeeman 1998 e Havrikov & Zeller 2019. Consultar pela biblioteca da universidade (IEEE Xplore no caso de Havrikov & Zeller).
- Os PDFs ficam em `referencias/pdfs/`, **fora do git** por direitos autorais; o script os baixa de novo.

## 7. Limitações da busca

- Os índices principais (arXiv, DBLP, ACM DL, IEEE Xplore) não puderam ser consultados diretamente durante a busca; a ausência de trabalhos que combinem gramática, cobertura, teste diferencial e metamórfico em chatbots pode refletir a busca limitada.
- Contagens de citação não foram obtidas, então "trabalho mais citado" não tem número que o sustente.
- Antes de entregar, refazer uma busca no arXiv e no DBLP por "grammar" + "LLM" + "fuzz" e por "differential testing" + "LLM", para confirmar que nenhum preprint de 2025–2026 já faz a mesma combinação.
