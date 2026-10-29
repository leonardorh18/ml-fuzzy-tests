# Mapa de evidências do artigo

> **Conteúdo gerado por IA (Claude).** Revise antes de usar.

Cada afirmação importante do artigo, com a fonte que a sustenta. Os números vêm de `results_local/paper_stats.json`, gerado por `python experiments/paper_stats.py` a partir das respostas salvas. As pastas `results_*` ficam fora do git; para reproduzir, rode os comandos do `CLAUDE.md` (seção 4).

## Sistema sob teste e ferramenta

| Afirmação | Fonte |
| --- | --- |
| Três modelos locais, revisões fixas, decodificação gulosa, 256 tokens | `fuzz_chatbots.py` (padrões), `chatfuzz/clients.py` (`LocalClient`), `results_local/summary.json` (`config`) |
| A API do Hugging Face foi implementada mas **não usada** (sem token) | `chatfuzz/clients.py` (`APIClient`); nenhum `api:` em `summary.json` |
| Gramática com 16 não terminais e 41 expansões; 12 payloads; 10 palavras; 8 chaves JSON | `chatfuzz/grammar.py` (`GRAMMAR`, `PAYLOADS`, `WORDS`, `JSON_KEYS`) |
| Escolha guiada por cobertura com `coverage_bias=0.8` | `chatfuzz/grammar.py` (`GrammarFuzzer._choose`) |
| Paráfrases diferem em palavras; `echo` só admite duas | `chatfuzz/grammar.py` (`generate`); `paper_stats.json` → `prompts_by_category.echo = 20` |
| Oráculos (último inteiro, normalização, JSON com cerca de código, substring no echo) | `chatfuzz/oracles.py` |
| Consenso errado exclui `echo` | `chatfuzz/analysis.py` (`CONSENSUS`) — mudança feita nesta etapa, porque no echo a resposta canônica é o próprio veredito |
| 19 testes unitários | `tests/`, `python3 -m pytest` |

## Resultados

| Afirmação | Fonte (`paper_stats.json`, salvo indicação) |
| --- | --- |
| 170 prompts (161 distintos), 510 respostas, 420 avaliadas | `main_run.prompts`, `unique_prompts`, `responses`; 140 × 3 |
| 27 pares modelo–prompt repetidos com resposta idêntica | `main_run.repeated_prompt_pairs` |
| 0 erros de execução e 0 respostas vazias | `results_local/summary.json` (`api_errors`, `empty_responses`) |
| 271 falhas (64,5%): 215 erradas, 30 JSON inválido, 22 não literais, 4 sem número | `main_run.failures_total`, `main_run.reasons` |
| Acerto 40,0 / 47,1 / 19,3% com IC de Wilson | `main_run.pass_rate` |
| McNemar: SmolLM×Qwen p=0,11; ambos × TinyLlama p<0,001 | `main_run.mcnemar` |
| Inversão: 1 acerto em 90; 21 respostas iguais à entrada | `pass_rate_by_category`; `failure_details.reverse_returned_input` |
| Aritmética: 44,4% vs 9,3% por tamanho do operando; 77% dentro de 10× | `failure_details.arith_pass_by_operand`, `arith_wrong_within_10x` |
| 25 de 150 pares modelo–esqueleto com acerto misto | `main_run.paraphrase_groups` |
| Exemplo do *strawberry* (Tabela 5) | `results_local/records.csv`, casos `0001-*` e `0035-*` |
| Qwen troca emoji de mulher por homem e acrescenta frase em chinês | `records.csv`, caso `0004-1` |
| RQ2: recall/precisão 98,8/73,9 (diferencial), 79,5/88,0 (metamórfico) | `main_run.rq2_oracles_without_ground_truth` |
| 111 prompts com respostas divergentes: 58 sem modelo correto | `failure_details.disagreeing_prompts_by_correct_models` |
| 1 consenso errado (*onomatopoeia*) | `results_local/findings.csv` (`consensus_wrong`) |
| Rótulos das 90 respostas `edge` | `validation/edge_labels.csv`; `paper_stats.json` → `edge_labels` |
| Latência e custo | `main_run.latency`, `total_compute_min` |
| Ablação 1 | `results_ablation/grammar_coverage.json` |
| Ablação 2 | `results_ablation/failure_diversity.json` |
| RQ4: 57/60, κ=0,89; 3 discordâncias no JSON; JSON tolerante 83% | `validation/oracle_validation.csv`; `oracle_validation`, `json_lenient_pass_rate` |

## Trabalhos relacionados

Os números atribuídos a outros trabalhos vêm das fichas em `referencias/FICHARIO.md`, que resumem os PDFs em `referencias/pdfs/`.

## Lacunas e pontos a resolver

- **[INFORMAÇÃO NECESSÁRIA]** Nomes, afiliação e e-mails dos autores (marcados com `\todo` no `main.tex`).
- **Julgamento manual (RQ4 e `edge`) feito com ajuda da IA.** Precisa ser conferido por pelo menos uma pessoa do grupo; o ideal é um segundo avaliador independente para medir concordância entre avaliadores.
- **A API hospedada não foi testada** (sem `HF_TOKEN`). O título e o texto falam de "chat models", não de "APIs", por isso.
- **McKeeman 1998 e Havrikov & Zeller 2019** sem cópia aberta; os dados bibliográficos e o que o artigo afirma sobre eles precisam ser conferidos na biblioteca.
- **Afirmação de novidade** ("to our knowledge") depende de uma busca final no arXiv e no DBLP.
- **Uma semente** na campanha principal e **três** na Ablação 2: diferenças pequenas não são estatisticamente sustentadas.
