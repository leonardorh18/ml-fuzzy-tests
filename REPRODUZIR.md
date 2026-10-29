# Como reproduzir os testes e os experimentos

> **Conteúdo gerado por IA (Claude).** Revise antes de usar.

Este guia refaz, na sua máquina, tudo o que está no artigo (`paper/main.pdf`): os testes da ferramenta, a execução principal, as duas ablações, a validação dos oráculos e as tabelas e figuras. Cada passo diz quanto tempo leva e o que você deve obter.

## 1. Antes de começar

| Item | Necessário |
| --- | --- |
| Sistema | Linux ou macOS (no Windows, use o WSL) |
| Python | 3.10 ou superior (os experimentos usaram 3.13) |
| Disco | cerca de 4 GB para os três modelos (ficam em `~/.cache/huggingface`) |
| Memória | 8 GB bastam; os experimentos rodaram com 15 GB |
| GPU | não é necessária; os experimentos rodaram só em CPU (4 núcleos) |
| Rede | acesso a `huggingface.co` na primeira execução, para baixar os modelos. Não precisa de conta nem de token |

## 2. Instalação

```bash
git clone <url-do-repositório> ml-fuzzy-tests
cd ml-fuzzy-tests
python -m venv .venv
source .venv/bin/activate          # no Windows/WSL: o mesmo comando
pip install -r requirements-experimentos.txt
```

`requirements-experimentos.txt` fixa as versões exatas dos experimentos. `requirements.txt` aceita versões mais novas; tudo funciona, mas algumas respostas dos modelos podem mudar (veja a seção 9).

## 3. Testes unitários da ferramenta (1 minuto)

```bash
python -m pytest
```

Esperado: `19 passed`. Estes testes verificam o código (gramática, oráculos, análise, clientes) com modelos falsos; eles **não** chamam os chatbots.

| Arquivo | O que testa |
| --- | --- |
| `tests/test_grammar.py` | a gramática é determinística por semente, as paráfrases compartilham o esqueleto e diferem no texto, a resposta esperada bate com os valores, a escolha guiada chega a 100% de cobertura e toda categoria tem regra |
| `tests/test_oracles.py` | extração do último inteiro (com separador de milhar), normalização de strings, leitura de JSON, veredito de cada categoria, erros e respostas vazias |
| `tests/test_analysis.py` | achados diferenciais, metamórficos, de erro e de consenso errado, sobre respostas inventadas |
| `tests/test_clients.py` | cliente da API contra uma sessão HTTP falsa: formato da requisição, resposta cortada, repetição em erros temporários, erros como dados, resposta malformada |
| `tests/test_pipeline.py` | a execução de ponta a ponta com um cliente falso grava todas as saídas e pode ser reanalisada |

## 4. Ver os prompts sem chamar modelos (segundos)

```bash
python fuzz_chatbots.py --cases 60 --variants 3 --seed 0 --dry-run
```

Mostra os 170 prompts da execução principal e a resposta esperada de cada um. A mesma semente sempre gera os mesmos prompts.

## 5. Execução principal — RQ1 e RQ2 (cerca de 1 hora em CPU)

```bash
python fuzz_chatbots.py --cases 60 --variants 3 --seed 0 --out results_local
```

- Usa os três modelos padrão, nas **mesmas revisões** do artigo (fixadas em `chatfuzz/clients.py`, `PINNED_REVISIONS`), com decodificação gulosa e no máximo 256 tokens por resposta.
- A primeira chamada de cada modelo demora mais (download e carregamento). O TinyLlama responde 5 vezes mais devagar que os outros e ocupa cerca de 70% do tempo total.
- As respostas são gravadas uma a uma em `results_local/responses.jsonl`. Se a execução parar, continue com o mesmo comando mais `--resume`.
- Para um teste rápido antes da execução completa: `--cases 6 --variants 1 --out results_teste` (poucos minutos).

**Saídas** em `results_local/`:

| Arquivo | Conteúdo |
| --- | --- |
| `cases.jsonl` | os 170 prompts, com categoria, valores sorteados e resposta esperada |
| `responses.jsonl` | a resposta bruta de cada modelo a cada prompt (510 linhas) |
| `records.csv` | uma linha por resposta, com o veredito do oráculo e a resposta canônica |
| `findings.csv` | os achados: `oracle_failure`, `differential_disagreement`, `metamorphic_inconsistency`, `consensus_wrong` |
| `summary.json` | acerto por modelo e categoria, consistência entre paráfrases, discordância entre modelos |
| `acerto_por_categoria.png` | gráfico rápido do acerto |

**Esperado** (o mesmo do artigo): 510 respostas, 0 erros de execução, 271 falhas de oráculo nas 420 respostas avaliadas, acerto de 40,0% (Qwen), 47,1% (SmolLM2) e 19,3% (TinyLlama).

### Conferir se você reproduziu as mesmas respostas

As respostas de referência estão versionadas em `referencia/execucao_principal/`. Compare:

```bash
python experiments/compare_runs.py results_local referencia/execucao_principal
```

Esperado na mesma pilha de software: `idênticas 170/170` para cada modelo. Uma nova execução do Qwen com as revisões fixadas, feita em 29/10/2026 no mesmo ambiente dos experimentos, deu 170/170. Veja a seção 9 se não for.

Para refazer só a análise de uma execução salva (sem chamar modelos): `python fuzz_chatbots.py --analyze results_local`.

## 6. Ablação 1 — cobertura da gramática, RQ3 (segundos, sem modelos)

```bash
python experiments/grammar_coverage.py --out results_ablation
```

Compara a escolha aleatória (`b = 0`) com a guiada por cobertura (`b = 0,8`) em 30 sementes de 120 prompts. Esperado em `results_ablation/grammar_coverage.json`: guiada com 34/59/80/92% de cobertura após 6/12/24/48 prompts e 100% em 27 de 30 sementes; aleatória com 33/51/71/86% e 100% em 4 de 30. Este resultado não depende de modelos, então é idêntico em qualquer máquina.

## 7. Ablação 2 — diversidade de falhas, RQ3 (cerca de 1 hora em CPU)

```bash
python experiments/failure_diversity.py \
    --models local:Qwen/Qwen2.5-0.5B-Instruct local:HuggingFaceTB/SmolLM2-360M-Instruct \
    --seeds 0 1 2 --out results_ablation
```

Seis condições (3 sementes × 2 valores de `b`), 30 prompts × 2 modelos cada. Esperado em `results_ablation/failure_diversity.json`: em média 30,0 falhas (aleatória) contra 30,3 (guiada), e 17,0 contra 18,7 assinaturas de falha distintas. A referência está em `referencia/ablacoes/`.

## 8. Estatísticas, figuras e artigo (1 minuto)

```bash
python experiments/paper_stats.py      # gera results_local/paper_stats.json e paper/figures/*.pdf
cd paper && latexmk -pdf main.tex      # compila o artigo
```

`paper_stats.py` calcula todos os números do artigo a partir das respostas salvas: intervalos de Wilson, testes de McNemar, recall e precisão dos oráculos sem resposta conhecida (RQ2), o oráculo de JSON tolerante, a concordância da validação manual (RQ4) e as figuras. Compare o seu `paper_stats.json` com `referencia/execucao_principal/paper_stats.json`.

Para compilar o artigo é preciso LaTeX. No Ubuntu/Debian:

```bash
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended latexmk
```

### Validação manual dos oráculos (RQ4)

A amostra julgada à mão já está em `validation/oracle_validation.csv` (60 respostas) e os rótulos das respostas `edge` em `validation/edge_labels.csv`. Para sortear a mesma amostra numa execução nova:

```bash
python experiments/sample_validation.py --run results_local --out validation/nova_amostra.csv
```

O arquivo sai com as colunas `human_correct` (a resposta está certa, mesmo com texto a mais), `format_ok` (também segue o formato pedido) e `note` em branco, para preencher. Depois aponte o `paper_stats.py` para ele com `--validation validation/nova_amostra.csv`.

> Os julgamentos de `validation/` foram feitos com ajuda da IA e ainda precisam ser revisados por uma pessoa do grupo.

## 9. Se os números não baterem

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| `compare_runs.py` mostra algumas respostas diferentes | outra versão de `torch`/`transformers`, outro processador ou GPU (operações em ponto flutuante mudam a escolha gulosa em empates) | instale `requirements-experimentos.txt` e rode em CPU (`CUDA_VISIBLE_DEVICES=""`). Diferenças pequenas mudam os números, mas não as conclusões |
| `0 respostas em comum` | semente, `--cases` ou `--variants` diferentes | use exatamente `--cases 60 --variants 3 --seed 0` |
| erro ao baixar o modelo | sem acesso a `huggingface.co` | libere o acesso; depois do primeiro download, `HF_HUB_OFFLINE=1` roda sem rede |
| execução muito lenta | TinyLlama em CPU | é esperado; para testar, rode só `--models local:Qwen/Qwen2.5-0.5B-Instruct` |
| `pytest` não encontra `pandas` | o `pytest` de outro Python | use `python -m pytest` dentro do ambiente virtual |

## 10. Opcional: testar modelos pela API do Hugging Face

Os experimentos do artigo não usaram a API (não havia token). Para usá-la, crie um token em https://huggingface.co/settings/tokens, guarde-o na variável de ambiente `HF_TOKEN` (nunca no código) e rode, por exemplo:

```bash
python fuzz_chatbots.py --cases 30 --variants 2 --out results_api \
    --models api:Qwen/Qwen2.5-7B-Instruct api:meta-llama/Llama-3.1-8B-Instruct
```

O uso consome créditos da conta, e os modelos hospedados podem mudar sem aviso, então esses resultados não são reproduzíveis da mesma forma que os locais.

## Onde cada resultado do artigo é gerado

| No artigo | Gerado por | Arquivo |
| --- | --- | --- |
| Tabela 5 e Figura 2 (acerto por categoria) | seções 5 e 8 | `paper_stats.json` → `pass_rate_by_category`; `paper/figures/pass_rate_by_category.pdf` |
| Exemplo do *strawberry* (Tabela 6) | seção 5 | `records.csv`, casos `0001-*` e `0037-*` |
| Tabela 7 (oráculos sem resposta conhecida, RQ2) | seção 8 | `paper_stats.json` → `rq2_oracles_without_ground_truth` |
| Figura 3 e Tabela 8 (ablações, RQ3) | seções 6 a 8 | `grammar_coverage.json`, `failure_diversity.json` |
| RQ4 (concordância 95%, κ = 0,89) | seção 8 | `paper_stats.json` → `oracle_validation` |
| Respostas `edge` (rótulos manuais) | `validation/edge_labels.csv` | `paper_stats.json` → `edge_labels` |

O mapa completo de cada afirmação do artigo até a sua fonte está em `paper/MAPA_DE_EVIDENCIAS.md`.
