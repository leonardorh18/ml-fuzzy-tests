# Fuzz Testing em Machine Learning

## Objetivo

Aplicar técnicas de **fuzz testing** a modelos de machine learning e aos componentes ao redor deles, para encontrar entradas que causam falhas: crashes, exceções, violações de propriedades ou mudanças de predição que não deveriam acontecer.

O trabalho cobre duas abordagens:

1. **Fuzzing clássico guiado por cobertura de código**, aplicado a um componente de ML (o tokenizer do DistilBERT), usando o [Atheris](https://github.com/google/atheris).
2. **Fuzzing adaptado para redes neurais, guiado por cobertura de neurônios**, aplicado a classificadores de imagem (ResNet-50 vs ViT), no estilo do TensorFuzz/DeepHunter.

A comparação entre as duas mostra como os conceitos de *cobertura* (código vs neurônios) e de *oráculo* (crash vs relação metamórfica) mudam quando o sistema testado é um modelo de ML.

### Perguntas que o trabalho responde

- Perturbações pequenas e imperceptíveis conseguem mudar a classe prevista pelo modelo?
- Quais tipos de mutação (ruído, rotação, blur, brilho...) quebram mais o modelo?
- Uma CNN (ResNet) é mais ou menos robusta do que um Transformer (ViT)?
- Aumentar a cobertura de neurônios ajuda a encontrar mais falhas?
- O tokenizer se comporta bem com qualquer texto Unicode?

---

## Links

| Recurso | Link |
|---|---|
| Hugging Face Spaces (demos dos modelos) | https://huggingface.co/spaces |
| Hugging Face Models | https://huggingface.co/models |
| ResNet-50 | https://huggingface.co/microsoft/resnet-50 |
| ViT Base | https://huggingface.co/google/vit-base-patch16-224 |
| DistilBERT (tokenizer) | https://huggingface.co/distilbert-base-uncased |
| Atheris (fuzzer para Python) | https://github.com/google/atheris |

**Dica sobre o Spaces:** os Spaces servem para explorar os modelos e mostrar demos. Para fuzzing pesado, rode os modelos localmente (como os scripts abaixo fazem) ou use **"Duplicate this Space"** para ter uma cópia própria. Não sobrecarregue o Space de outras pessoas, porque muitos usam GPU compartilhada com cota.

---

## Estrutura

```
.
├── README.md
├── fuzz_resnet.py               # Mini-TensorFuzz (cobertura de neurônios)
├── fuzz_tokenizer_atheris.py    # Fuzzing clássico com Atheris
├── compare_results.py           # Compara execuções (ResNet vs ViT)
├── requirements.txt
├── seeds/                       # imagens semente (você coloca)
├── corpus/                      # corpus gerado pelo Atheris
└── results/                     # saída do fuzz_resnet.py
```

---

## Instruções

### Pré-requisitos

- Python 3.8 a 3.11
- Linux, macOS ou WSL (o Atheris não roda no Windows nativo)
- GPU não é necessária, CPU dá conta

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Sem acesso ao Hugging Face?** `fuzz_resnet.py --random-weights` monta a mesma arquitetura com pesos aleatórios, sem baixar nada. Serve só para testar se o pipeline roda; os resultados não dizem nada sobre o modelo real.

### Experimento 1: Mini-TensorFuzz (ResNet vs ViT)

**Como funciona:**
1. Começa com um corpus de imagens semente.
2. Sorteia uma imagem e aplica uma mutação aleatória: ruído, brilho, contraste, rotação, blur ou patch.
3. Limita a perturbação a um raio pequeno (`EPSILON = 0.08`, norma L∞) em torno da imagem original.
4. Mede a cobertura de neurônios em cada camada da rede.
5. **Oráculo:** se a classe prevista mudou, registra uma falha e salva a imagem.
6. **Feedback:** se não falhou mas ativou neurônios novos, a imagem mutada volta para o corpus.

**Passos:**

```bash
# 1. Coloque de 5 a 20 fotos (.jpg/.png) em seeds/: cachorro, carro, xícara...
ls seeds

# 2. Rode com a ResNet-50
python fuzz_resnet.py --iters 2000 --out results_resnet

# 3. Rode com o ViT para comparar
python fuzz_resnet.py --model google/vit-base-patch16-224 --iters 2000 --out results_vit

# 4. Compare as duas execuções
python compare_results.py results_resnet results_vit --out comparacao.png
```

**Saídas (em `results_*/`):**
- `log.csv`: uma linha por iteração (mutação, cobertura, classe original e prevista, falha, distância L∞)
- `failures/`: imagens que enganaram o modelo, com a classe original e a nova no nome
- `fuzzing.png`: cobertura de neurônios e falhas acumuladas ao longo das iterações
- `falhas_por_mutacao.png`: % de falhas por tipo de mutação
- `summary.json`: totais, taxa de falhas, cobertura final, falhas por mutação e cobertura por camada

O `compare_results.py` imprime uma tabela lado a lado, a taxa de falha por mutação de cada modelo, a correlação entre ganho de cobertura e falhas (por janela de 100 iterações) e salva `comparacao.png`.

**Parâmetros ajustáveis** (no topo do script):
- `EPSILON`: tamanho máximo da perturbação. Quanto maior, mais falhas e menos "imperceptível".
- `COV_THRESHOLD`: limiar para considerar um neurônio coberto (padrão 0.5).

Os dois também podem ser passados na linha de comando (`--epsilon`, `--threshold`), junto com `--seeds`, `--batch-size`, `--seed` (reprodutibilidade) e `--device`.

**Detalhes do algoritmo:**
- **Neurônio:** cada canal de um bloco da CNN (média espacial) ou cada dimensão oculta de um bloco do Transformer (média sobre os tokens). São monitorados os blocos `ResNetBottleNeckLayer`/`ResNetConvLayer` da ResNet e os `ViTLayer` do ViT.
- **Cobertura (DeepXplore):** as ativações de cada camada são normalizadas para [0, 1] por entrada (min-max); o neurônio está coberto se alguma entrada já passou de `COV_THRESHOLD`.
- **Seleção de semente (DeepHunter):** a chance de sortear um elemento do corpus é `1 / (1 + vezes_sorteado)`, então mutantes novos são explorados antes.
- **Projeção:** depois de cada mutação, a imagem é cortada para ficar a no máximo `EPSILON` da semente *original* em cada pixel, mesmo depois de várias mutações encadeadas.
- **Oráculo:** a classe prevista do mutante é comparada com a classe que o modelo deu para a semente original (não com o rótulo verdadeiro).

### Experimento 2: Fuzzing do tokenizer com Atheris

**Como funciona:** o Atheris gera bytes aleatórios guiado por cobertura de código, converte em texto e passa pelo tokenizer do DistilBERT. Quatro oráculos são verificados:

1. A chamada não pode lançar exceção.
2. O número de tokens respeita `max_length`.
3. Todos os ids estão dentro do vocabulário.
4. **Metamórfico:** `decode(encode(texto))` é estável quando aplicado duas vezes.

O tokenizer rápido do Hugging Face é escrito em Rust, e o Atheris só mede cobertura do código Python. Para fuzzing guiado de verdade, use o tokenizer em Python puro com `FUZZ_SLOW=1` (precisa de `transformers<5`; a partir da versão 5 só existe o rápido e o script avisa). Outras variáveis: `FUZZ_TOKENIZER` (outro modelo ou pasta local) e `FUZZ_SURROGATES=1` (permite surrogates Unicode isolados no texto).

**Passos:**

```bash
mkdir -p corpus
python fuzz_tokenizer_atheris.py corpus -max_total_time=300

# tokenizer em Python puro (mais cobertura visível ao Atheris)
pip install "transformers<5"
FUZZ_SLOW=1 python fuzz_tokenizer_atheris.py corpus -max_total_time=300
```

**Saídas:**
- `corpus/`: entradas que aumentaram a cobertura de código
- `crash-<hash>`: a entrada que violou algum oráculo, se houver

Para reproduzir um crash:

```bash
python fuzz_tokenizer_atheris.py crash-<hash>
```

**Exemplo de falha encontrada:** com `FUZZ_SLOW=1` (transformers 4.57) e um vocabulário WordPiece local no lugar do DistilBERT, o fuzzer achou em poucos segundos um texto de um caractere com `max_length=2` que gera 3 tokens (`[CLS] x [SEP]`), violando o oráculo 2: o tokenizer em Python registra *"We need to remove 1 to truncate the input but the first sequence has a length 1"* e devolve a sequência sem truncar. O tokenizer rápido, para a mesma entrada, devolve `[CLS] [SEP]`. Os dois tokenizers do mesmo modelo se comportam de forma diferente nesse caso de borda. A falha está na lógica de truncamento, que não depende do vocabulário, então deve aparecer também com o DistilBERT.

---

## Sugestão de estrutura do trabalho escrito

1. **Introdução:** o que é fuzz testing e por que testar sistemas de ML.
2. **Fundamentação teórica:**
   - Fuzzing clássico e guiado por cobertura (AFL, libFuzzer, Atheris)
   - Teste metamórfico e o problema do oráculo em ML
   - Cobertura de neurônios (DeepXplore)
   - Fuzzing de redes neurais (TensorFuzz, DLFuzz, DeepHunter)
3. **Metodologia:** os dois experimentos, os modelos, as mutações e os oráculos.
4. **Resultados:** taxa de falhas, cobertura, comparação ResNet vs ViT, falhas por mutação, crashes do tokenizer.
5. **Discussão:** limitações da cobertura de neurônios como métrica e diferenças entre fuzzing clássico e de ML.
6. **Conclusão.**

## Referências

- Pei, K. et al. *DeepXplore: Automated Whitebox Testing of Deep Learning Systems.* SOSP, 2017.
- Guo, J. et al. *DLFuzz: Differential Fuzzing Testing of Deep Learning Systems.* ESEC/FSE, 2018.
- Odena, A.; Goodfellow, I. *TensorFuzz: Debugging Neural Networks with Coverage-Guided Fuzzing.* ICML, 2019.
- Xie, X. et al. *DeepHunter: A Coverage-Guided Fuzz Testing Framework for Deep Neural Networks.* ISSTA, 2019.
- Wei, A. et al. *Free Lunch for Testing: Fuzzing Deep-Learning Libraries from Open Source (FreeFuzz).* ICSE, 2022.
- Deng, Y. et al. *Large Language Models are Zero-Shot Fuzzers: Fuzzing Deep-Learning Libraries via LLMs (TitanFuzz).* ISSTA, 2023.
