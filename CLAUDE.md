# CLAUDE.md

Guia do projeto para o Claude Code e registro das decisões tomadas pela IA ao construir este repositório.

> **Conteúdo gerado por IA (Claude).** O código, os testes, a documentação e a apresentação foram gerados com o Claude Code a partir do README fornecido pelo usuário. Revise antes de usar.

## O que é o projeto

Trabalho acadêmico de **fuzz testing em machine learning**, em português. Dois experimentos:

1. **Mini-TensorFuzz** (`fuzz_resnet.py`): fuzzing de classificadores de imagem (ResNet-50 e ViT-Base) guiado por cobertura de neurônios.
2. **Tokenizer com Atheris** (`fuzz_tokenizer_atheris.py`): fuzzing clássico, guiado por cobertura de código, do tokenizer do DistilBERT.

## Estrutura

```
fuzz_resnet.py               # Experimento 1
fuzz_tokenizer_atheris.py    # Experimento 2
compare_results.py           # compara execuções do Experimento 1
requirements.txt
seeds/                       # imagens semente (o usuário coloca)
apresentacao/                # slides exportados (HTML, PDF, notas, fontes dos slides)
  build_deck.py              # gera apresentacao.html e notas.md a partir de slides/
  slides/                    # um .html por slide + deck.json (ordem) + assets.json (imagens)
  img/                       # imagens dos slides, geradas a partir dos resultados reais
```

`results*/`, `corpus/` e `crash-*` são saídas e estão no `.gitignore`.

## Comandos

```bash
pip install -r requirements.txt

# Experimento 1
python fuzz_resnet.py --iters 2000 --out results_resnet
python fuzz_resnet.py --model google/vit-base-patch16-224 --iters 2000 --out results_vit
python compare_results.py results_resnet results_vit --out comparacao.png
python fuzz_resnet.py --random-weights ...     # sem Hugging Face: arquitetura com pesos aleatórios

# Experimento 2
mkdir -p corpus
python fuzz_tokenizer_atheris.py corpus -max_total_time=300
FUZZ_SLOW=1 python fuzz_tokenizer_atheris.py corpus -max_total_time=300   # tokenizer em Python (transformers<5)
python fuzz_tokenizer_atheris.py crash-<hash>                              # reproduz um crash

# Apresentação
python apresentacao/build_deck.py apresentacao/slides apresentacao
```

Não há suíte de testes unitários; a verificação é rodar os scripts (com `--random-weights` quando não houver acesso ao Hugging Face).

## Convenções

- Textos, comentários, saídas e docs em **português**; identificadores de código em inglês.
- Parâmetros ajustáveis ficam como constantes no topo do script (`EPSILON`, `COV_THRESHOLD`) e também como flags de linha de comando.
- Gráficos com matplotlib: fundo limpo, grade leve, uma cor de destaque (`#2a78d6`) e laranja (`#eb6834`) só para a segunda série.
- Todo material de apresentação ou documento leva o aviso **"Conteúdo gerado por IA"**.

## Decisões de implementação

### Experimento 1 (`fuzz_resnet.py`)

| Decisão | Por quê |
| --- | --- |
| Normalização da imagem dentro do modelo (`Classifier`) | Para `EPSILON` ser medido no espaço de pixels [0, 1], independente da média e desvio de cada modelo. |
| Camadas monitoradas = módulos mais externos cujo nome de classe termina em `Layer` | Regra única que pega `ResNetBottleNeckLayer`/`ResNetConvLayer` na ResNet e `ViTLayer` no ViT sem lista fixa por modelo. |
| Neurônio = canal (média espacial) na CNN, dimensão oculta (média sobre tokens) no Transformer | Mantém o número de neurônios comparável e barato de medir. |
| Cobertura estilo DeepXplore: min-max por entrada dentro da camada, coberto acima do limiar | Não precisa de calibração prévia. **Limitação conhecida:** satura no ViT (94,6% só com as sementes). |
| `COV_THRESHOLD = 0.5` (em vez de 0.75) | Com 0.75 a cobertura inicial da ResNet ficava em 1,5%, baixa demais para medir crescimento. Precisa ser recalibrado com pesos reais. |
| Projeção L∞ em relação à semente **original**, não ao pai | Garante que mutações encadeadas nunca passem de `EPSILON = 0.08`. |
| Oráculo = classe do mutante ≠ classe que o modelo deu à semente | Dispensa rótulos verdadeiros. |
| Seleção de semente com peso `1 / (1 + vezes sorteada)` | Seleção probabilística do DeepHunter: explora mutantes novos primeiro. |
| Falhas não voltam ao corpus; só mutantes que cobrem neurônios novos | Segue o README fornecido. |
| Mutantes avaliados em lote (`--batch-size 8`) | Acelera em CPU sem mudar o algoritmo (cobertura é atualizada mutante a mutante). |
| Pré-processamento próprio (resize 256, crop 224) com média/desvio do `AutoImageProcessor` quando disponível | Funciona igual para ResNet e ViT e também offline. |
| Flag `--random-weights` | O ambiente da IA não tinha acesso ao Hugging Face; permite testar o pipeline sem baixar pesos. |
| `summary.json` além do `log.csv` | Base para o `compare_results.py`. |

### Experimento 2 (`fuzz_tokenizer_atheris.py`)

| Decisão | Por quê |
| --- | --- |
| `max_length` também vem do fuzzer (2 a 512) | Explora casos de borda de truncamento; foi assim que a falha foi encontrada. |
| Texto sem surrogates por padrão (`FUZZ_SURROGATES=1` para permitir) | Surrogates isolados quebram a codificação UTF-8 de forma trivial e poluiriam os crashes. |
| Oráculo metamórfico sem truncamento | Testa só encode/decode, sem misturar com o corte do `max_length`. |
| `FUZZ_SLOW=1` (tokenizer em Python) | O tokenizer rápido é Rust e invisível ao Atheris. No `transformers` 5 não existe mais o BERT em Python; o script avisa. |
| `FUZZ_TOKENIZER` aponta para um modelo ou pasta local | Permitiu testar com um vocabulário WordPiece local, sem Hugging Face. |

## Ambiente em que a IA trabalhou

- Container Linux na nuvem, só CPU (4 núcleos, 15 GB), Python 3.13, torch 2.14.1, transformers 5.21.0 (e 4.57.6 num venv para o modo `FUZZ_SLOW`), Atheris 3.1.0.
- **`huggingface.co` bloqueado pelo proxy.** Nenhum peso treinado nem o tokenizer real do DistilBERT foram baixados.
- Substituições usadas nos testes: `--random-weights`, 6 imagens sintéticas (gradientes com um retângulo) como sementes e um vocabulário WordPiece de 125 tokens.

## Resultados obtidos (pesos aleatórios, 28/10/2026)

| | ResNet-50 | ViT-Base |
| --- | --- | --- |
| Falhas em 500 iterações | 0 | 45 (9%) |
| Sementes com falha | 0 de 6 | 4 de 6 |
| Confiança média | 98,4% (todas as sementes em `LABEL_884`) | 0,7% |
| Cobertura inicial → final | 8,2% → 9,2% | 94,6% → 98,1% |
| Falhas por brilho | 0 | 38 de 45 |

Tokenizer:
- Rápido (Rust): 258.995 execuções em 61 s, cobertura 141, nenhuma violação.
- Python puro (transformers 4.57): cobertura 295, **violação do oráculo 2** em menos de 1 s. Com `max_length=2`, o texto `'Ƒ'` gera 3 tokens (`[CLS] x [SEP]`); o tokenizer registra "We need to remove 1 to truncate the input but the first sequence has a length 1" e não trunca. O rápido devolve `[CLS] [SEP]`. Entrada: 6 bytes, base64 `CpEBAAAA`.

**Leitura correta:** a ResNet "não falha" porque colapsou numa classe só; o ViT falha porque está quase indeciso. Os números **não** comparam a robustez real das arquiteturas.

## Pendências

- [ ] Rodar o Experimento 1 com pesos reais, fotos reais em `seeds/` e 2000 iterações.
- [ ] Recalibrar `COV_THRESHOLD` por modelo ou usar faixas calibradas por neurônio (DeepGauge) para o ViT não saturar.
- [ ] Confirmar a falha de truncamento com o tokenizer real do DistilBERT.
- [ ] Adicionar oráculo diferencial (tokenizer rápido × Python).
- [ ] Testar `EPSILON` em 0,02, 0,04, 0,08 e 0,16.

## Histórico de pedidos do usuário

1. Implementar fuzz tests para ML a partir do README → scripts, README, commit inicial.
2. Criar uma doc explicando como o teste foi feito e uma apresentação → doc e slides (artifacts privados no claude.ai); reexecução com 500 iterações por modelo para comparação justa.
3. Colocar aviso de conteúdo gerado por IA e deixar os slides mais diretos → de 13 para 6 slides, aviso na capa e nos rodapés.
4. Começar a apresentação explicando o que é fuzz testing em ML, os modelos e para que servem, como geramos os testes e os resultados → slide de introdução e slide de modelos reescrito (7 slides).
5. Colocar a apresentação e este `CLAUDE.md` no repositório.
6. "Os slides estão fracos": explicar fuzz testing em ML com exemplo e como funciona, os modelos e para que servem, como geramos os testes e os resultados → 12 slides com exemplos reais do teste (a imagem que enganou o ViT, as 6 mutações aplicadas a uma semente, os 6 bytes que quebraram o tokenizer) e um gráfico de cobertura e falhas a partir do `log.csv`.

## Decisões da apresentação

- Exemplos sempre tirados dos nossos próprios resultados, não de artigos: a imagem da iteração 20 do ViT (classe 614 → 727 só com brilho) e a entrada `0a 91 01 00 00 00` do tokenizer.
- As mutações são mostradas no valor máximo da faixa e **antes** do corte em ε, senão ficariam invisíveis; o rodapé do slide avisa isso.
- O esquema de neurônios do slide de cobertura é ilustrativo, e está marcado assim.
- Os exemplos de entrada e saída dos modelos ("golden retriever", "coffee mug", tokens de "the cat is sleeping") são ilustrativos do uso normal, não saídas do teste.
- Todo slide leva "Conteúdo gerado por IA" no rodapé; a capa tem o aviso completo.

## Material fora do repositório

- Doc "Fuzz Testing em Machine Learning: como o teste foi feito": https://claude.ai/artifact/CbXwfNptHjc4N4oXic3kb4
- Slides (versão editável): https://claude.ai/artifact/THjW9Rse5tPXpL5QcqJ296

Ambos são privados até o dono compartilhar. A pasta `apresentacao/` é a cópia versionada dos slides.
