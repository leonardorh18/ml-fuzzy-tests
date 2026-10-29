# CLAUDE.md

Guia do projeto e registro de **todas as decisões e do contexto**, para que outra pessoa ou IA possa assumir o trabalho sem o histórico da conversa.

> **Conteúdo gerado por IA (Claude).** O código, os testes, os experimentos e o artigo foram gerados com o Claude Code. Revise antes de usar.

---

## 1. O que é o projeto

Trabalho final de uma disciplina de **teste de software / fuzzing**, em grupo de 3 ou 4 pessoas (nomes ainda não informados pelo usuário). O tema escolhido pelo usuário:

> **Natural Language Chatbot APIs (Hugging Face) — Grammar-based fuzzing and differential testing.**

### Entregas exigidas pelo enunciado da disciplina

1. **Artefato de software** — `chatfuzz/` + `fuzz_chatbots.py` + `experiments/` + `tests/`. **Pronto.**
2. **Avaliação experimental** — **concluída** (ver seção 6); falta revisão humana dos julgamentos manuais.
3. **Artigo científico** — estrutura exigida: title and abstract, introduction, background and related work, research questions and objectives, methodology, experimental setup, results, discussion, threats to validity and limitations, conclusion and future work, references. Em `paper/`, **template SBC**, em inglês. **Versão completa** com números reais; faltam nomes dos autores e revisão humana. Mapa de evidências em `paper/MAPA_DE_EVIDENCIAS.md`.
4. **Apresentação** — deve cobrir: (1) software alvo e problema, (2) pergunta de pesquisa e motivação, (3) técnicas, (4) implementação e desenho experimental, (5) resultados principais, (6) exemplo de falha/discrepância, (7) conclusões e limitações. **Feita:** https://claude.ai/artifact/F8jSSUJkvwYhfuJ6PWvjc1 (11 slides em inglês, notas em português; cópia em `apresentacao/`; PDF em `apresentacao/slides.pdf`, gerado por `apresentacao/gerar_pdf.js`). Faltam os nomes dos autores na capa. Guia em português de cada slide (Claude Docs): https://claude.ai/artifact/NZkJ6BqEJrYV7q3TwiRRja.

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
experiments/paper_stats.py        # todas as estatísticas e figuras do artigo -> results_local/paper_stats.json, paper/figures/
experiments/sample_validation.py  # sorteia a amostra da RQ4
experiments/compare_runs.py       # compara uma execução nova com a de referência
referencia/                   # respostas e resultados de referência (execução principal e ablações), versionados
REPRODUZIR.md                 # guia de reprodução local
validation/                   # oracle_validation.csv (RQ4, 60 respostas julgadas) e edge_labels.csv (90 respostas edge rotuladas)
tests/                        # 19 testes unitários da ferramenta (pytest)
paper/                        # artigo SBC: main.tex, sections/*.tex, references.bib, sbc-template.sty, main.pdf
apresentacao/                 # cópia do deck (claude.ai) e README com o mapa dos 7 pontos
referencias/                  # FICHARIO.md, METODO_DE_BUSCA.md, baixar_artigos.py (PDFs fora do git)
research_notes/Trabalhos relacionados fuzzing de chatbots/   # notas da busca de literatura (4 temas)
reports/Trabalhos relacionados fuzzing de chatbots.md        # bibliografia anotada consolidada, com status de verificação
results_local/                # execução principal (no .gitignore)
results_ablation/             # ablações (no .gitignore)
```

## 4. Comandos

Passo a passo completo, com tempos e resultados esperados: `REPRODUZIR.md`. Versões exatas: `requirements-experimentos.txt`. Respostas de referência versionadas em `referencia/` (comparar com `python experiments/compare_runs.py results_local`).

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
| Revisões dos modelos fixadas em `PINNED_REVISIONS` (`chatfuzz/clients.py`); `local:modelo@rev` escolhe outra | Antes não estavam fixadas no código; sem isso, um download futuro poderia trazer outros pesos. O nome nos resultados não inclui a revisão. |
| Resultados de referência versionados em `referencia/` (≈600 KB) | `results*/` fica fora do git; sem a referência, ninguém conseguiria conferir uma reprodução. |
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

## 6. Estado dos experimentos (todos concluídos)

Números completos em `results_local/paper_stats.json` (`python experiments/paper_stats.py`).

| Experimento | Resultado |
| --- | --- |
| Principal (`results_local/`, semente 0, b=0,8): 60 esqueletos → **170 prompts** (echo só admite 2 paráfrases; 161 strings distintas) → **510 respostas**, 420 avaliadas | 271 falhas (64,5%). Acerto: Qwen 40,0%, SmolLM2 47,1%, TinyLlama 19,3% (McNemar: Qwen×SmolLM p=0,11; ambos > TinyLlama p<0,001). Inversão 1/90. JSON: TinyLlama 0/30 (JSON dentro de prosa). Echo: Qwen 5/20. 25/150 pares modelo–esqueleto com acerto misto entre paráfrases. 0 erros/vazios. 1 consenso errado (*onomatopoeia*). 53,9 min de CPU. 27 prompts repetidos deram resposta idêntica (determinismo). |
| RQ2 (sem resposta conhecida, 360 respostas) | Diferencial: recall 98,8%, precisão 73,9%. Metamórfico: 79,5% / 88,0%. Em 58 de 111 divergências nenhum modelo acertou. |
| Ablação 1 (30 sementes) | Guiada: 34/59/80/92% após 6/12/24/48 prompts, 100% em 27/30. Aleatória: 33/51/71/86%, 4/30. |
| Ablação 2 (Qwen+SmolLM, sementes 0–2) | Falhas 30,0 vs 30,3; regras reveladoras 21,7 vs 23,7; assinaturas 17,0 vs 18,7 (aleatória vs guiada). Diferença pequena, indicativa. |
| RQ4 (60 respostas) | 57/60 = 95%, κ=0,89. As 3 discordâncias: TinyLlama com JSON válido dentro de prosa (oráculo estrito). JSON tolerante: TinyLlama 83%. Critério estrito (formato): 17/60. |
| `edge` (90 respostas, rótulo manual) | 33 benignas, 29 alucinadas/erradas, 13 recusas, 12 loops de repetição, 3 vazamentos de `<|user|>`. |

**Julgamentos manuais (RQ4 e edge) foram feitos pela IA** e precisam de revisão humana; isso está declarado no artigo.

Mudança de código nesta etapa: `consensus_wrong` deixou de considerar `echo` (a resposta canônica do echo é o próprio veredito); `findings.csv` foi regenerado.

## 7. Próximos passos (em ordem)

1. Revisão humana de `validation/oracle_validation.csv` e `validation/edge_labels.csv` (idealmente um segundo avaliador).
2. Pedir os nomes do grupo e substituir os `\todo` do artigo.
3. Pôr os nomes do grupo na capa da apresentação.
4. Conferir McKeeman 1998 e Havrikov & Zeller 2019 na biblioteca; busca final no arXiv/DBLP para o "to our knowledge".
5. Atualizar o rascunho no claude.ai (ainda tem 47 referências e seções vazias) ou descartá-lo.

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
17. Pediu o artigo completo como pesquisador sênior, baseado só em evidências, com mapa de evidências e marcadores de lacunas → Ablação 2, RQ4, análise do `edge`, `paper_stats.py`, artigo inteiro reescrito, `paper/MAPA_DE_EVIDENCIAS.md`.
18. Pediu a apresentação refeita com os 7 pontos → deck no claude.ai + `apresentacao/`.
19. Pediu um doc em português explicando cada slide e os testes documentados para reprodução local → guia no Claude Docs, `REPRODUZIR.md`, `referencia/`, `compare_runs.py`, revisões fixadas.

## 11. Material fora do repositório

- Rascunho do artigo (inglês) no claude.ai, mesmo conteúdo das seções escritas: https://claude.ai/artifact/Ff8ZThoNqWKE1Crdhd388j
- Apresentação atual: https://claude.ai/artifact/F8jSSUJkvwYhfuJ6PWvjc1
- Guia dos slides em português: https://claude.ai/artifact/NZkJ6BqEJrYV7q3TwiRRja
- **Sobre o projeto antigo (desatualizados):** doc https://claude.ai/artifact/CbXwfNptHjc4N4oXic3kb4, slides https://claude.ai/artifact/THjW9Rse5tPXpL5QcqJ296, guia em português https://claude.ai/artifact/UdCMocEWpagFZJFM9KdYUy.
