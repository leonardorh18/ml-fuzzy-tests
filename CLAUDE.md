# CLAUDE.md

Guia do projeto e registro de **todas as decisões e do contexto**, para que outra pessoa ou IA possa assumir o trabalho sem o histórico da conversa.

> **Conteúdo gerado por IA (Claude).** O código, os testes, os experimentos e o artigo foram gerados com o Claude Code. Revise antes de usar.

---

## 1. O que é o projeto

Trabalho final de uma disciplina de **teste de software / fuzzing**, em grupo de 3 ou 4 pessoas (nomes ainda não informados pelo usuário). O tema escolhido pelo usuário:

> **Natural Language Chatbot APIs (Hugging Face) — Grammar-based fuzzing and differential testing.**

### Entregas exigidas pelo enunciado da disciplina

1. **Artefato de software** — `chatfuzz/` + `fuzz_chatbots.py` + `experiments/` + `tests/`. **Pronto.**
2. **Avaliação experimental** — em andamento (ver seção 6).
3. **Artigo científico** — estrutura exigida: title and abstract, introduction, background and related work, research questions and objectives, methodology, experimental setup, results, discussion, threats to validity and limitations, conclusion and future work, references. Em `paper/`, **template SBC**, em inglês. Faltam abstract, results, discussion, conclusion.
4. **Apresentação** — deve cobrir: (1) software alvo e problema, (2) pergunta de pesquisa e motivação, (3) técnicas, (4) implementação e desenho experimental, (5) resultados principais, (6) exemplo de falha/discrepância, (7) conclusões e limitações. **Não feita ainda** para o projeto novo.

O enunciado pede ir além de rodar um fuzzer: formular pergunta de pesquisa, desenhar a estratégia, experimentar, analisar e tirar conclusões **sobre a eficácia e as limitações da técnica** (não só sobre os modelos).

## 2. Perguntas de pesquisa (fixadas no artigo)

- **RQ1 (Effectiveness):** quantas falhas, e de que tipos, o fuzzing com gramática revela em chatbots pequenos do Hugging Face?
- **RQ2 (Oracles):** o que os oráculos diferencial (entre modelos) e metamórfico (entre paráfrases) acrescentam além dos oráculos com resposta conhecida?
- **RQ3 (Guidance):** a expansão guiada por cobertura da gramática melhora a cobertura e a diversidade de falhas em relação à expansão aleatória, com o mesmo orçamento?
- **RQ4 (Oracle reliability):** com que frequência os oráculos heurísticos erram, numa amostra conferida à mão?

## 3. Estrutura do repositório

```
fuzz_chatbots.py              # CLI: gera prompts, chama modelos, analisa
chatfuzz/grammar.py           # gramática livre de contexto + fuzzer guiado por cobertura
chatfuzz/clients.py           # local:<modelo> (transformers, guloso) e api:<modelo> (roteador HF)
chatfuzz/oracles.py           # oráculos por categoria e resposta canônica
chatfuzz/analysis.py          # diferencial, metamórfico, consenso errado, resumo, gráfico
experiments/grammar_coverage.py   # Ablação 1 (sem modelos)
experiments/failure_diversity.py  # Ablação 2 (com modelos)
tests/                        # 19 testes unitários da ferramenta (pytest)
paper/                        # artigo SBC: main.tex, sections/*.tex, references.bib, sbc-template.sty, main.pdf
referencias/                  # FICHARIO.md, METODO_DE_BUSCA.md, baixar_artigos.py (PDFs fora do git)
research_notes/Trabalhos relacionados fuzzing de chatbots/   # notas da busca de literatura (4 temas)
reports/Trabalhos relacionados fuzzing de chatbots.md        # bibliografia anotada consolidada, com status de verificação
results_local/                # execução principal (no .gitignore)
results_ablation/             # ablações (no .gitignore)
```

## 4. Comandos

```bash
pip install -r requirements.txt
pytest                                                    # 19 testes
python fuzz_chatbots.py --dry-run                         # só mostra os prompts
python fuzz_chatbots.py --cases 60 --variants 3 --seed 0 --out results_local      # execução principal
python fuzz_chatbots.py --analyze results_local           # refaz a análise
python experiments/grammar_coverage.py --out results_ablation
python experiments/failure_diversity.py --models local:Qwen/Qwen2.5-0.5B-Instruct \
    local:HuggingFaceTB/SmolLM2-360M-Instruct --seeds 0 1 2 --out results_ablation
cd paper && latexmk -pdf main.tex                         # compila o artigo
```

## 5. Decisões e o porquê

### Ferramenta

| Decisão | Por quê |
| --- | --- |
| Caso de teste = esqueleto (categoria + valores sorteados) + derivação da gramática | Os valores dão a resposta esperada; derivações diferentes do mesmo esqueleto são paráfrases (teste metamórfico). |
| `<nome>` fora da gramática é lido dos valores; `<nome_VALOR>` tem prioridade | A forma de dizer a operação (`+`, `plus`) depende da operação sorteada sem duplicar regras. |
| Escolha guiada por cobertura (`coverage_bias=0.8`) | GrammarCoverageFuzzer do Fuzzing Book; equivale a cobertura 1-path (Havrikov & Zeller 2019). |
| Cada `TestCase` guarda `expansions` (regras usadas) | Necessário para medir diversidade de falhas na Ablação 2. Não altera o sorteio (mesmos prompts para a mesma semente). |
| Paráfrases devem diferir em palavras, não só espaços | Variantes só de espaço não testam nada. |
| Sem capitalização automática | Ela alterava entradas Unicode (ligadura "ﬁ" virava "FI"). |
| 6 categorias: `arith`, `count`, `reverse`, `json`, `echo` (verificáveis) e `edge` (só erro/vazio) | Resolve o problema do oráculo para a maioria dos casos. |
| Prompts em inglês | Modelos pequenos são bem mais fracos em português. |
| Oráculo numérico = último inteiro da resposta | Modelos repetem a conta antes do resultado. Heurística; a RQ4 mede o erro. |
| `local:` com decodificação gulosa | Determinismo, essencial para diferencial e metamórfico. |
| `max_tokens` padrão 256 e flag `truncated` | No piloto com 128, o TinyLlama era cortado antes do número; falhas em respostas cortadas são contadas à parte. |
| `api:` usa `https://router.huggingface.co/v1/chat/completions` (OpenAI-compatível) | Qualquer provedor (`modelo:provedor`), repete em 429/5xx/timeout. Não usado nos experimentos (sem `HF_TOKEN`). |
| Achado `consensus_wrong` (todos os modelos dão a mesma resposta errada) | Sugestão da literatura (SAC3): diferencial puro não vê erros compartilhados. |
| Erros viram dados (`ChatResponse.error`) | Um erro também é resultado do fuzzing. |
| Modelos: Qwen2.5-0.5B-Instruct, SmolLM2-360M-Instruct, TinyLlama-1.1B-Chat-v1.0 | Pequenos para CPU; famílias diferentes. Revisões: `7ae5576`, `a10cc15`, `fe8a4ea`. |

### Artigo

| Decisão | Por quê |
| --- | --- |
| Inglês | O enunciado da disciplina está em inglês; o usuário pediu inglês acadêmico antes. |
| Template SBC **reimplementado** em `paper/sbc-template.sty` | O `.sty` oficial não pôde ser baixado (sbc.org.br bloqueado; Overleaf exige login para o código). As regras vieram do PDF oficial do template no Overleaf ("SBC Conferences Template", v2017): A4, margens 3,5/2,5/3,0 cm, Times 12, 6pt antes de parágrafos, título 16pt negrito, seções 13pt, legendas Helvetica 10pt negrito, resumo com recuo de 0,8 cm, referências com recuo pendente de 0,5 cm, citações `[Autor Ano]`. O `.sty` oficial pode substituir o nosso sem mudar o `main.tex`. |
| `apalike` + natbib (`square`, sem vírgula entre autor e ano) | Reproduz o formato de referências e citações da SBC (o `sbc.bst` oficial deriva do `apalike`). Use `\citep` para `[Autor Ano]` e `\citet` para "Autor [Ano]". |
| Autores e afiliação como `\todo{...}` em vermelho | Nomes do grupo ainda não informados. |
| Declaração de uso de IA no fim | Exigência ética; também diz que a validação dos oráculos (RQ4) foi feita com ajuda da IA. |
| Afirmação de novidade com "to our knowledge" | A busca não encontrou trabalho que combine os quatro elementos, mas arXiv/DBLP/ACM DL não puderam ser consultados diretamente. |

### Bibliografia

- **20 referências** (pedido do grupo: no máximo 20; clássicos na base teórica, 2023–2026 no teste de LLMs). Lista, critérios e funil de seleção em `referencias/METODO_DE_BUSCA.md`; fichas com resumo de cada artigo em `referencias/FICHARIO.md`.
- PDFs em `referencias/pdfs/` (fora do git por direitos autorais); `python referencias/baixar_artigos.py` baixa de novo. 18 de 20 baixados e conferidos pelo título; **sem cópia aberta:** McKeeman 1998 e Havrikov & Zeller 2019 (consultar pela biblioteca).
- A conferir antes de entregar: dados bibliográficos do McKeeman 1998 (só confirmados por citações) e uma busca final no arXiv/DBLP para sustentar o "to our knowledge".
- O relatório amplo da busca (≈90 trabalhos, status de verificação) continua em `reports/`; as referências cortadas estão listadas no método de busca e podem voltar.

## 6. Estado dos experimentos

| Experimento | Estado | Resultado |
| --- | --- | --- |
| Execução principal (`results_local/`, 60 esqueletos × 3 paráfrases × 3 modelos = 540 respostas, semente 0) | Rodando em segundo plano no momento desta escrita (≈441/540) | — |
| Ablação 1 (`results_ablation/grammar_coverage.json`, 30 sementes, 120 prompts) | **Concluída** | Guiada (b=0,8): cobertura 34/59/80/92% após 6/12/24/48 prompts, 100% em 27/30 sementes (mediana 73 prompts). Aleatória (b=0): 33/51/71/86%, 100% em só 4/30 sementes (mediana 94). |
| Ablação 2 (diversidade de falhas, Qwen + SmolLM, sementes 0–2, 30 esqueletos × 1, b ∈ {0, 0,8}) | **Não rodada** (esperando a principal terminar, para não disputar CPU) | — |
| Validação dos oráculos (RQ4) | **Não feita** | Plano: amostra estratificada (≈60 respostas, equilibrada por categoria e modelo) de `records.csv`, julgamento manual vs. veredito automático. |

Piloto (3 prompts por modelo, só para estimar tempo; não é resultado): Qwen/SmolLM ≈1–2 s por prompt em CPU, TinyLlama 3–10 s (até ≈40 s quando chega a 256 tokens).

## 7. Próximos passos (em ordem)

1. Esperar `results_local/responses.jsonl` chegar a 540 linhas; a análise roda sozinha e gera `summary.json`, `findings.csv`, `records.csv`, `acerto_por_categoria.png`. Se o processo tiver morrido: `python fuzz_chatbots.py --cases 60 --variants 3 --seed 0 --out results_local --resume`.
2. Rodar a Ablação 2 (comando na seção 4).
3. RQ4: sortear a amostra, julgar cada resposta, calcular concordância oráculo × julgamento.
4. Escolher um exemplo real de falha/discrepância (para o artigo e a apresentação).
5. Preencher `paper/sections/{abstract,results,discussion,conclusion}.tex` com os números reais; gerar figuras em `paper/figures/` (gráfico de cobertura da Ablação 1, acerto por categoria). Recompilar e commitar `main.pdf`.
6. Fazer a apresentação com os 7 pontos do enunciado (o deck antigo no claude.ai é sobre o projeto anterior; pode ser reaproveitado como artefato, substituindo os slides).
7. Pedir os nomes do grupo e substituir os `\todo` do artigo.
8. Conferir as referências marcadas como não verificadas.

## 8. Convenções

- Código e identificadores em inglês; comentários, saídas, README e este arquivo em português; artigo em inglês.
- **Nunca** apresentar resultados simulados como resultados de modelos. Clientes falsos só nos testes unitários.
- Todo material de apresentação ou documento leva o aviso "Conteúdo gerado por IA".
- Gráficos: matplotlib, grade leve, cores categóricas em ordem fixa (`#2a78d6`, `#eb6834`, `#1baf7a`, ...).
- Commits terminam com as linhas de coautoria/sessão do Claude; branch de trabalho `claude/jolly-galileo-ghok7l`.

## 9. Ambiente

- Container Linux na nuvem, 4 núcleos, 15 GB, sem GPU, Ubuntu 24.04, Python 3.13, torch 2.14.1, transformers 5.21.0, TeX Live do Ubuntu (instalado via apt nesta sessão; um container novo precisa reinstalar: `apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended latexmk`).
- `huggingface.co` foi **liberado** pelo usuário na rede do ambiente (antes era bloqueado). Não há `HF_TOKEN`, então só modelos locais. Bloqueados: sbc.org.br, arxiv.org (páginas), dblp (anti-bot), ACM DL. Liberados: PyPI, Ubuntu archive, CTAN, Overleaf (páginas públicas), GitHub (git), Crossref API.
- Modelos baixados ficam em `~/.cache/huggingface` (3,7 GB); um container novo baixa de novo na primeira execução.

## 10. Histórico de pedidos do usuário

1. Fuzz tests de ML a partir de um README (ResNet/ViT com cobertura de neurônios; tokenizer DistilBERT com Atheris).
2–8. Doc, slides, aviso de IA, versões em inglês, guia em português (claude.ai) — tudo sobre o projeto antigo.
9. "Os testes são válidos?" — não para robustez de modelos de imagem (pesos aleatórios, sementes sintéticas, ε grande).
10. **"Muda tudo"**: projeto passou a ser fuzzing de chatbots do Hugging Face com gramática + teste diferencial. Projeto antigo removido (está no histórico do git, commit `933355d`).
11. Liberou `huggingface.co`; execução real com modelos locais iniciada.
12. Colou o enunciado da disciplina (entregas: software, avaliação, artigo, apresentação) → RQs, ablações e validação de oráculos.
13. Pediu o artigo com busca de literatura (agentes + deep research) → rascunho no claude.ai e bibliografia verificada.
14. Pediu o artigo no **template SBC**, em `.tex` e `.pdf`, com commit → `paper/`.
15. Pediu este arquivo atualizado com todas as decisões e contexto.
16. Pediu no máximo 20 referências (clássicos + atuais), download dos artigos, fichário com resumos e o método de busca → `referencias/`.

## 11. Material fora do repositório

- Rascunho do artigo (inglês) no claude.ai, mesmo conteúdo das seções escritas: https://claude.ai/artifact/Ff8ZThoNqWKE1Crdhd388j
- **Sobre o projeto antigo (desatualizados):** doc https://claude.ai/artifact/CbXwfNptHjc4N4oXic3kb4, slides https://claude.ai/artifact/THjW9Rse5tPXpL5QcqJ296, guia em português https://claude.ai/artifact/UdCMocEWpagFZJFM9KdYUy.
