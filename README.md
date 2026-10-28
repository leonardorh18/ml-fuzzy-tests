# Fuzz Testing de Chatbots do Hugging Face: gramática + teste diferencial

> **Conteúdo gerado por IA (Claude).** O código, os testes e esta documentação foram gerados com o Claude Code. As decisões tomadas estão em `CLAUDE.md`. Revise antes de usar.

## Objetivo

Aplicar **fuzzing baseado em gramática** e **teste diferencial** a chatbots de linguagem natural do Hugging Face, para encontrar entradas em que eles erram, se contradizem ou falham.

- **Fuzzing baseado em gramática:** uma gramática livre de contexto gera milhares de prompts válidos e variados (contas, contagem de letras, inversão de texto, pedidos de JSON, cópia literal e entradas Unicode difíceis). Cada pedido sai em várias paráfrases, e a escolha das regras é guiada por **cobertura da gramática**: formas de pedir ainda não usadas têm prioridade.
- **Teste diferencial:** o mesmo prompt vai para vários chatbots, e as respostas são comparadas. Quando a resposta certa é conhecida (numa conta, por exemplo), dá para dizer quem errou; quando não é, a discordância já aponta onde olhar.
- **Teste metamórfico:** paráfrases do mesmo pedido devem receber a mesma resposta do mesmo modelo.

### Perguntas que o trabalho responde

- Os chatbots acertam tarefas simples e verificáveis?
- Eles dão a mesma resposta para paráfrases do mesmo pedido?
- Modelos diferentes concordam entre si? Quando discordam, quem erra?
- Eles seguem instruções de formato (só o número, só JSON, copiar sem mudar)?
- Eles lidam com Unicode difícil (emoji compostos, texto da direita para a esquerda, caracteres invisíveis) sem erro?

---

## Como funciona

```
gramática ──► prompts + resposta esperada ──► chatbots (local: e api:) ──► oráculos
                    │                                                     │
                    └─ paráfrases ─────────► teste metamórfico ◄──────────┤
                                             teste diferencial ◄──────────┘
```

| Categoria | Exemplo de prompt gerado | Oráculo |
| --- | --- | --- |
| `arith` | `What is 4 multiplied by 101? Give only the numeric result.` | último número da resposta = resultado da conta |
| `count` | `How many times does the letter 'e' appear in the word 'referrer'?` | número = contagem real |
| `reverse` | `Reverse the string 'NhFLOv2mp'. Reply with the result only.` | resposta = string invertida |
| `json` | `Return a JSON object with the keys "city" and "tags". Reply with JSON only.` | JSON válido com as chaves pedidas |
| `echo` | `Repeat exactly the following text, without any change: 👩‍💻🚀🇧🇷` | o texto aparece intacto na resposta |
| `edge` | `Translate to Portuguese: مرحبا بالعالم` | sem erro e sem resposta vazia |

Além do oráculo de cada categoria, a análise gera:

- **`differential_disagreement`:** modelos deram respostas diferentes ao mesmo prompt (com a lista de quem errou, quando a resposta certa é conhecida);
- **`differential_error`:** um modelo deu erro e outro respondeu;
- **`metamorphic_inconsistency`:** o mesmo modelo respondeu diferente a paráfrases do mesmo pedido;
- **`api_error`, `empty_response`, `oracle_failure`.**

## Estrutura

```
.
├── fuzz_chatbots.py        # script principal
├── chatfuzz/
│   ├── grammar.py          # gramática e fuzzer guiado por cobertura
│   ├── clients.py          # modelos locais (local:) e API do Hugging Face (api:)
│   ├── oracles.py          # verificação das respostas
│   └── analysis.py         # teste diferencial, metamórfico, resumo e gráfico
├── tests/                  # testes unitários da ferramenta (pytest)
├── requirements.txt
└── CLAUDE.md               # decisões e contexto registrados pela IA
```

## Instruções

### Pré-requisitos

- Python 3.10 ou superior
- Acesso a `huggingface.co`: para baixar os modelos locais na primeira execução, ou para usar a API
- GPU não é necessária para os modelos locais pequenos

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Modo 1: modelos baixados e rodados localmente (padrão)

Sem o prefixo de API, o script baixa os modelos do Hugging Face (ficam em cache) e roda na máquina, com decodificação gulosa (sem aleatoriedade):

```bash
python fuzz_chatbots.py --out results
```

Modelos padrão (pequenos, para rodar em CPU):

| Modelo | Tamanho |
| --- | --- |
| `Qwen/Qwen2.5-0.5B-Instruct` | 0,5 bilhão de parâmetros |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | 360 milhões |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1,1 bilhão |

Outros modelos: `--models local:<organização>/<modelo> ...`.

### Modo 2: API do Hugging Face (Inference Providers)

1. Crie um token em https://huggingface.co/settings/tokens com a permissão de chamar Inference Providers.
2. Exporte-o como `HF_TOKEN`.
3. Rode com o prefixo `api:`:

```bash
export HF_TOKEN=...
python fuzz_chatbots.py --out results_api \
  --models api:meta-llama/Llama-3.1-8B-Instruct api:Qwen/Qwen2.5-7B-Instruct
```

Um sufixo escolhe o provedor (`api:meta-llama/Llama-3.1-8B-Instruct:novita`). Isso permite outro teste diferencial: **o mesmo modelo servido por provedores diferentes** deveria responder igual. A disponibilidade de cada modelo na API muda com o tempo; o uso consome os créditos da conta.

Os dois modos podem ser misturados na mesma execução.

### Parâmetros úteis

| Parâmetro | Padrão | O que faz |
| --- | --- | --- |
| `--cases` | 30 | número de pedidos (cada um vira `--variants` prompts) |
| `--variants` | 2 | paráfrases por pedido |
| `--categories` | todas | limita as categorias |
| `--seed` | 0 | semente da gramática (reprodutibilidade) |
| `--max-tokens` | 256 | tamanho máximo da resposta; respostas cortadas no limite ficam marcadas em `truncated` |
| `--delay` | 0 | pausa entre chamadas (para limites da API) |
| `--resume` | | continua uma execução interrompida |
| `--dry-run` | | só gera e mostra os prompts, sem chamar modelos |
| `--analyze DIR` | | refaz a análise de uma execução salva |

### Saídas (em `results/`)

- `cases.jsonl`: os prompts gerados, com a resposta esperada
- `responses.jsonl`: a resposta bruta de cada modelo (gravada a cada chamada)
- `records.csv`: uma linha por modelo e prompt, com o veredito do oráculo
- `findings.csv`: os achados (diferencial, metamórfico, erros, falhas de oráculo)
- `summary.json`: acerto por modelo e categoria, consistência entre paráfrases, discordância entre pares de modelos e cobertura da gramática
- `acerto_por_categoria.png`: gráfico do acerto por categoria e modelo

### Testes da ferramenta

```bash
pytest
```

Os testes verificam a gramática, os oráculos, a análise e o cliente da API (contra uma sessão HTTP falsa). Eles testam o código, não os chatbots.

---

## Limitações

- **Chatbots não são determinísticos.** Os modelos locais usam decodificação gulosa; na API, `--temperature 0` reduz, mas nem todo provedor garante a mesma resposta.
- **Os oráculos usam heurísticas.** "O último número da resposta" pode errar quando o modelo escreve mais de um número; vale conferir uma amostra em `records.csv`.
- **Discordância nem sempre é bug.** Nas categorias sem resposta conhecida, uma discordância é um sinal para investigar, não uma falha comprovada.
- **Modelos pequenos erram muito.** Os resultados dos modelos locais padrão dizem respeito a eles, não a chatbots grandes.

## Sugestão de estrutura do trabalho escrito

1. **Introdução:** por que testar chatbots e o problema do oráculo em linguagem natural.
2. **Fundamentação:** fuzzing baseado em gramática, cobertura de gramática, teste diferencial e teste metamórfico.
3. **Metodologia:** a gramática, os modelos, os oráculos e as métricas.
4. **Resultados:** acerto por categoria, discordância entre modelos, consistência entre paráfrases e exemplos de achados.
5. **Discussão:** limites dos oráculos heurísticos e diferenças entre modelos e provedores.
6. **Conclusão.**

## Referências

Confira os dados bibliográficos nas fontes originais antes de citar.

- McKeeman, W. M. (1998). Differential testing for software. *Digital Technical Journal*, 10(1).
- Holler, C., Herzig, K., & Zeller, A. (2012). Fuzzing with code fragments. *USENIX Security Symposium*.
- Zeller, A., Gopinath, R., Böhme, M., Fraser, G., & Holler, C. *The Fuzzing Book*. https://www.fuzzingbook.org (capítulos "Fuzzing with Grammars" e "Grammar Coverage").
- Hugging Face. Inference Providers. https://huggingface.co/docs/inference-providers
