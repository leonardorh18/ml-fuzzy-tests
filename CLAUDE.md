# CLAUDE.md

Guia do projeto para o Claude Code e registro das decisões tomadas pela IA ao construir este repositório.

> **Conteúdo gerado por IA (Claude).** O código, os testes e a documentação foram gerados com o Claude Code. Revise antes de usar.

## O que é o projeto

Trabalho acadêmico, em português, de **fuzz testing de chatbots de linguagem natural do Hugging Face** com **fuzzing baseado em gramática** e **teste diferencial**, mais teste metamórfico entre paráfrases.

## Estrutura

```
fuzz_chatbots.py        # CLI: gera prompts, chama os modelos, analisa
chatfuzz/grammar.py     # gramática livre de contexto + fuzzer guiado por cobertura
chatfuzz/clients.py     # local:<modelo> (transformers) e api:<modelo> (roteador do HF)
chatfuzz/oracles.py     # oráculos por categoria e resposta canônica
chatfuzz/analysis.py    # diferencial, metamórfico, resumo e gráfico
tests/                  # testes unitários da ferramenta
```

`results*/` é saída e está no `.gitignore`.

## Comandos

```bash
pip install -r requirements.txt
pytest                                                   # testes da ferramenta
python fuzz_chatbots.py --dry-run                        # só mostra os prompts
python fuzz_chatbots.py --out results                    # modelos locais padrão
HF_TOKEN=... python fuzz_chatbots.py --models api:<modelo> api:<modelo> --out results_api
python fuzz_chatbots.py --analyze results                # refaz a análise
```

## Convenções

- Textos, comentários, saídas, README e este arquivo em **português**; identificadores de código e os prompts gerados em inglês (os modelos testados são mais fortes em inglês).
- Erros de API ou do modelo viram dados (`ChatResponse.error`), nunca exceções: um erro também é um resultado do fuzzing.
- Respostas são gravadas em `responses.jsonl` a cada chamada, para não perder execuções longas (`--resume`).
- Gráficos com matplotlib: grade leve, cores categóricas em ordem fixa (`#2a78d6`, `#eb6834`, `#1baf7a`, ...).
- Todo material de apresentação ou documento leva o aviso **"Conteúdo gerado por IA"**.
- **Nunca** apresentar resultados simulados como resultados de modelos. Clientes falsos só existem nos testes unitários, para testar o código.

## Decisões de implementação

| Decisão | Por quê |
| --- | --- |
| Caso de teste = esqueleto (categoria + valores sorteados) + derivação da gramática | Os valores dão a resposta esperada; derivações diferentes do mesmo esqueleto são paráfrases para o teste metamórfico. |
| Símbolo `<nome>` fora da gramática é lido dos valores; `<nome_VALOR>` tem prioridade | Permite que a forma de dizer a operação (`+`, `plus`) dependa da operação sorteada sem duplicar a gramática. |
| Escolha de expansão guiada por cobertura (`coverage_bias=0.8`) | Ideia do GrammarCoverageFuzzer (The Fuzzing Book): exercita todas as formas de pedir; a cobertura sai no `summary.json`. |
| Paráfrases precisam diferir em palavras, não só em espaços | Variantes que só trocam espaço por quebra de linha quase não testam nada. |
| Sem capitalização automática dos prompts | Ela alterava as entradas difíceis (a ligadura "ﬁ" virava "FI"). |
| Categorias com resposta verificável (`arith`, `count`, `reverse`, `json`, `echo`) + `edge` só com oráculo de erro | Resolve o problema do oráculo em linguagem natural para a maioria dos casos. |
| Prompts em inglês | Os modelos pequenos padrão são bem mais fracos em português; as entradas difíceis (`PAYLOADS`) incluem outros idiomas e escritas. |
| Oráculo numérico = último inteiro da resposta | Os modelos costumam repetir a conta antes do resultado ("3 + 4 = 7"). Heurística; pode errar. |
| `local:` com decodificação gulosa | Torna os modelos locais determinísticos, o que é essencial para o teste diferencial e o metamórfico. |
| `api:` usa o endpoint compatível com OpenAI do roteador do HF (`https://router.huggingface.co/v1/chat/completions`) | Funciona com qualquer provedor (`modelo:provedor`) e com servidores locais compatíveis via `--base-url`. Repete em 429/5xx/timeout com espera exponencial. |
| Modelos locais padrão: Qwen2.5-0.5B-Instruct, SmolLM2-360M-Instruct, TinyLlama-1.1B-Chat | Pequenos o bastante para rodar em CPU; famílias diferentes, bom para o teste diferencial. |
| `apply_chat_template(..., return_dict=True)["input_ids"]` | Funciona no `transformers` 4 e 5. Verificado com um modelo minúsculo de pesos aleatórios montado localmente (só para testar o código). |

## Ambiente em que a IA trabalhou

- Container Linux na nuvem, só CPU (4 núcleos, 15 GB), Python 3.13, torch 2.14.1, transformers 5.21.0.
- **Bloqueados pelo proxy:** `huggingface.co` (inclusive CDN e espelhos), ModelScope, Ollama, GPT4All. Liberados: PyPI, npm, GitHub. Sem `HF_TOKEN`.
- Consequência: **nenhum chatbot real foi executado ainda.** Para rodar aqui, é preciso liberar `huggingface.co` nas configurações de rede do ambiente e, para a API, guardar o token como `HF_TOKEN` nos segredos do ambiente. Também dá para rodar na máquina do usuário.

## Status

- [x] Gramática, clientes, oráculos, análise e CLI implementados; 17 testes unitários passando.
- [ ] Primeira execução real com os modelos locais padrão.
- [ ] Execução pela API com 2 ou mais modelos maiores e, se possível, o mesmo modelo em provedores diferentes.
- [ ] Revisar manualmente uma amostra de `records.csv` para medir o erro dos oráculos heurísticos.
- [ ] Refazer a doc e os slides com os resultados reais.

## Histórico de pedidos do usuário

1. Implementar fuzz tests para ML a partir de um README (ResNet/ViT com cobertura de neurônios e tokenizer do DistilBERT com Atheris).
2. Doc e apresentação sobre o teste.
3. Aviso de IA e slides mais diretos.
4. Slides explicando fuzzing em ML, modelos, testes e resultados.
5. Apresentação e `CLAUDE.md` no repositório.
6. Slides mais fortes, com exemplos reais.
7. Reescrita da apresentação e da doc em inglês acadêmico.
8. Commit de tudo, incluindo a doc em `docs/relatorio.md`; depois, um guia em português no claude.ai explicando cada slide.
9. "Os testes são válidos?": não para a robustez dos modelos de imagem (pesos aleatórios, sementes sintéticas, ε grande, corte único anulando rotação e blur).
10. **"Muda tudo":** o trabalho passou a testar chatbots de linguagem natural do Hugging Face com fuzzing baseado em gramática e teste diferencial. Os experimentos antigos (`fuzz_resnet.py`, `fuzz_tokenizer_atheris.py`, `compare_results.py`, `seeds/`, `apresentacao/`, `docs/`) foram removidos do repositório; continuam no histórico do git (commit `933355d`).

## Material fora do repositório (sobre o trabalho antigo)

A doc, os slides e o guia no claude.ai ainda descrevem os experimentos antigos de imagem e tokenizer:

- Doc em inglês: https://claude.ai/artifact/CbXwfNptHjc4N4oXic3kb4
- Slides: https://claude.ai/artifact/THjW9Rse5tPXpL5QcqJ296
- Guia em português: https://claude.ai/artifact/UdCMocEWpagFZJFM9KdYUy
