# Fichário das referências

> **Conteúdo gerado por IA (Claude).** Fichas escritas a partir do resumo e da introdução de cada PDF baixado (29/10/2026). Confira os pontos importantes no texto original antes de citar.

As 20 referências do artigo, na ordem em que aparecem na fundamentação. Cada ficha traz a referência, o arquivo, um resumo, os números principais do próprio artigo e a relação com o nosso trabalho. Os PDFs ficam em `referencias/pdfs/` (fora do git, por direitos autorais); para baixá-los de novo, rode `python referencias/baixar_artigos.py`. O método de busca está em `METODO_DE_BUSCA.md`.

| # | Chave (`references.bib`) | Ano | Tema | PDF |
| --- | --- | --- | --- | --- |
| 1 | `mckeeman1998differential` | 1998 | Teste diferencial (clássico) | sem cópia aberta |
| 2 | `chen1998metamorphic` | 1998 | Teste metamórfico (clássico) | sim |
| 3 | `yang2011csmith` | 2011 | Teste diferencial / geração de entradas válidas | sim |
| 4 | `holler2012langfuzz` | 2012 | Fuzzing com gramática (clássico) | sim |
| 5 | `barr2015oracle` | 2015 | Problema do oráculo | sim |
| 6 | `pei2017deepxplore` | 2017 | Teste diferencial em ML | sim |
| 7 | `havrikov2019kpath` | 2019 | Cobertura de gramática | sem cópia aberta |
| 8 | `ribeiro2020checklist` | 2020 | Teste comportamental de NLP | sim |
| 9 | `zeller2024fuzzingbook` | 2024 | Cobertura de gramática (base do gerador) | sim (HTML impresso em PDF) |
| 10 | `yu2023gptfuzzer` | 2023 | Fuzzing de LLMs | sim |
| 11 | `zhang2023sac3` | 2023 | Consistência entre modelos | sim |
| 12 | `hyun2024metal` | 2024 | Teste metamórfico de LLMs | sim |
| 13 | `wang2024survey` | 2024 | LLMs e teste de software (survey) | sim |
| 14 | `sclar2024formatting` | 2024 | Sensibilidade ao formato do prompt | sim |
| 15 | `edman2024cute` | 2024 | Falhas no nível de caractere | sim |
| 16 | `cho2025metamorphic` | 2025 | Teste metamórfico de LLMs | sim |
| 17 | `guo2026mortar` | 2026 | Teste metamórfico de chatbots | sim |
| 18 | `qwen2024qwen25` | 2024 | Modelo testado | sim |
| 19 | `benallal2025smollm2` | 2025 | Modelo testado | sim |
| 20 | `zhang2024tinyllama` | 2024 | Modelo testado | sim |

---

## 1. McKeeman (1998) — Differential Testing for Software

- **Referência:** McKeeman, W. M. Differential Testing for Software. *Digital Technical Journal*, 10(1):100–107, 1998.
- **PDF:** sem cópia aberta acessível (o site da HP que hospedava o periódico não respondeu). **Ficha baseada em fontes secundárias; o texto não foi lido.**
- **Resumo:** artigo que deu nome e forma ao teste diferencial. A ideia: quando há várias implementações que deveriam se comportar igual (por exemplo, vários compiladores de C), basta dar a mesma entrada a todas e comparar as saídas; uma divergência indica um erro em pelo menos uma delas, sem precisar de oráculo.
- **Relação com o nosso trabalho:** é a origem do oráculo diferencial que aplicamos entre chatbots.
- **Atenção:** os dados bibliográficos (volume, número e páginas) só foram confirmados por artigos que o citam. Conferir na biblioteca antes de entregar.

## 2. Chen, Cheung e Yiu (1998) — Metamorphic Testing

- **Referência:** Chen, T. Y., Cheung, S. C., Yiu, S. M. Metamorphic Testing: A New Approach for Generating Next Test Cases. Relatório técnico HKUST-CS98-01, 1998 (arXiv:2002.12543).
- **PDF:** `pdfs/chen1998metamorphic.pdf`
- **Resumo:** parte de três observações: casos de teste que passam são descartados sem análise; erros continuam existindo depois dos testes; e, como notou Weyuker, oráculos quase nunca estão disponíveis na prática. Propõe derivar novos casos de teste a partir dos que passaram, usando relações que as saídas de entradas relacionadas devem satisfazer.
- **Relação com o nosso trabalho:** proposta original do teste metamórfico. A nossa relação "paráfrases do mesmo pedido devem ter a mesma resposta" é uma relação metamórfica.

## 3. Yang et al. (2011) — Csmith

- **Referência:** Yang, X., Chen, Y., Eide, E., Regehr, J. Finding and Understanding Bugs in C Compilers. *PLDI*, 2011.
- **PDF:** `pdfs/yang2011csmith.pdf` (preprint dos autores)
- **Resumo:** apresenta o Csmith, gerador aleatório de programas em C que evita comportamento indefinido, para que todo programa gerado tenha um único resultado correto. Os programas são compilados por vários compiladores e as saídas comparadas (teste diferencial).
- **Números:** mais de 325 bugs desconhecidos encontrados em três anos; todos os compiladores testados travaram e também geraram código errado silenciosamente.
- **Relação com o nosso trabalho:** precedente clássico de "gerador de entradas válidas + oráculo diferencial". Gerar só entradas com resposta bem definida é exatamente o papel das nossas categorias verificáveis.

## 4. Holler, Herzig e Zeller (2012) — LangFuzz

- **Referência:** Holler, C., Herzig, K., Zeller, A. Fuzzing with Code Fragments. *21st USENIX Security Symposium*, pp. 445–458, 2012.
- **PDF:** `pdfs/holler2012langfuzz.pdf`
- **Resumo:** um interpretador rejeita entradas sintaticamente inválidas, então fuzzing aleatório não passa da análise sintática. O LangFuzz é um fuzzer caixa-preta que recebe uma gramática livre de contexto e gera programas válidos, recombinando fragmentos de código de testes existentes.
- **Números:** 105 vulnerabilidades graves novas no interpretador JavaScript do Mozilla em três meses.
- **Relação com o nosso trabalho:** referência canônica de fuzzing baseado em gramática. Usamos a mesma ideia (gramática gera entradas válidas), mas para prompts em linguagem natural.

## 5. Barr et al. (2015) — The Oracle Problem in Software Testing: A Survey

- **Referência:** Barr, E. T., Harman, M., McMinn, P., Shahbaz, M., Yoo, S. *IEEE Transactions on Software Engineering*, 41(5):507–525, 2015.
- **PDF:** `pdfs/barr2015oracle.pdf` (repositório aberto da UCL)
- **Resumo:** define o problema do oráculo (distinguir o comportamento correto do incorreto para uma entrada) e revisa as formas de automatizá-lo: modelos, especificações, contratos e teste metamórfico. Quando nada disso basta, o oráculo volta a ser humano.
- **Relação com o nosso trabalho:** dá a taxonomia para classificar os nossos três oráculos: especificado (resposta conhecida), derivado (metamórfico) e implícito (erro de execução).

## 6. Pei et al. (2017) — DeepXplore

- **Referência:** Pei, K., Cao, Y., Yang, J., Jana, S. DeepXplore: Automated Whitebox Testing of Deep Learning Systems. *SOSP*, 2017.
- **PDF:** `pdfs/pei2017deepxplore.pdf` (arXiv:1705.06640)
- **Resumo:** primeiro framework de teste caixa-branca para sistemas de deep learning. Introduz a cobertura de neurônios e usa **vários modelos de mesma função como oráculos cruzados**, evitando rótulos manuais; busca, por gradiente, entradas que maximizam ao mesmo tempo a divergência entre modelos e a cobertura.
- **Números:** milhares de comportamentos errados em casos de canto, em modelos treinados em cinco bases de dados.
- **Relação com o nosso trabalho:** precedente mais direto do oráculo diferencial entre modelos. Diferenças: usamos gramática em vez de gradiente (os chatbots são caixa-preta) e temos resposta conhecida para decidir quem errou.

## 7. Havrikov e Zeller (2019) — Systematically Covering Input Structure

- **Referência:** Havrikov, N., Zeller, A. Systematically Covering Input Structure. *ASE*, pp. 189–199, 2019.
- **PDF:** sem cópia aberta encontrada (consultar pela biblioteca da universidade, IEEE Xplore). **Ficha baseada nos metadados e em fontes secundárias; o texto não foi lido.**
- **Resumo:** formaliza a cobertura de k-caminhos de uma gramática: a proporção de sequências de k expansões da gramática que os testes exercitam. A versão de periódico (TOSEM 2022) mostra que essa cobertura de entrada se correlaciona com a cobertura de código.
- **Relação com o nosso trabalho:** a nossa cobertura de gramática é o caso k = 1. Justifica usar a cobertura da gramática como guia quando o código do sistema não pode ser observado, como nos chatbots.

## 8. Ribeiro et al. (2020) — CheckList

- **Referência:** Ribeiro, M. T., Wu, T., Guestrin, C., Singh, S. Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. *ACL*, pp. 4902–4912, 2020.
- **PDF:** `pdfs/ribeiro2020checklist.pdf`
- **Resumo:** a acurácia em dados reservados superestima modelos de NLP. Inspirado no teste comportamental da engenharia de software, o CheckList organiza testes numa matriz de capacidades × tipos de teste e gera muitos casos a partir de templates, incluindo testes de invariância (a saída não deve mudar com alterações que preservam o sentido).
- **Números:** num estudo com usuários, quem usou o CheckList criou o dobro de testes e achou quase três vezes mais bugs.
- **Relação com o nosso trabalho:** o nosso teste de paráfrase é um teste de invariância no estilo CheckList, mas gerado por gramática com guia de cobertura e aplicado a vários modelos.

## 9. Zeller et al. (2024) — The Fuzzing Book, capítulo "Grammar Coverage"

- **Referência:** Zeller, A., Gopinath, R., Böhme, M., Fraser, G., Holler, C. Grammar Coverage. In *The Fuzzing Book*. CISPA, 2024. https://www.fuzzingbook.org/html/GrammarCoverageFuzzer.html (acesso em 29/10/2026).
- **PDF:** `pdfs/zeller2024fuzzingbook.pdf` (página HTML impressa em PDF)
- **Resumo:** gerar entradas de uma gramática dando a mesma chance a todas as expansões repete as mesmas formas. O capítulo apresenta o `GrammarCoverageFuzzer`, que prefere expansões ainda não cobertas para maximizar a variedade.
- **Relação com o nosso trabalho:** **base direta do nosso gerador** (`chatfuzz/grammar.py`, parâmetro `coverage_bias`). A Ablação 1 compara exatamente essa estratégia com a escolha uniforme.

## 10. Yu et al. (2023) — GPTFuzzer

- **Referência:** Yu, J., Lin, X., Yu, Z., Xing, X. GPTFUZZER: Red Teaming Large Language Models with Auto-Generated Jailbreak Prompts. arXiv:2309.10253, 2023 (preprint).
- **PDF:** `pdfs/yu2023gptfuzzer.pdf`
- **Resumo:** fuzzer caixa-preta inspirado no AFL que parte de templates de jailbreak escritos por pessoas e os muta automaticamente; um modelo julga se a resposta do LLM-alvo foi um jailbreak bem-sucedido.
- **Números:** mais de 90% de sucesso de ataque contra ChatGPT e Llama-2, mesmo partindo de templates ruins.
- **Relação com o nosso trabalho:** mostra que o fuzzing de LLMs hoje mira segurança (o oráculo é "o ataque funcionou?"). Nós miramos falhas funcionais, com oráculos de correção, diferencial e metamórfico.

## 11. Zhang et al. (2023) — SAC3

- **Referência:** Zhang, J., Li, Z., Das, K., Malin, B., Kumar, S. SAC3: Reliable Hallucination Detection in Black-Box Language Models via Semantic-aware Cross-check Consistency. *Findings of EMNLP*, 2023.
- **PDF:** `pdfs/zhang2023sac3.pdf`
- **Resumo:** detectores de alucinação baseados na autoconsistência de um modelo falham em dois casos: alucinações ligadas à forma da pergunta e alucinações em que o modelo é consistentemente errado. O SAC3 acrescenta perguntas reformuladas e a checagem cruzada com outros modelos.
- **Relação com o nosso trabalho:** justifica tanto as paráfrases quanto a comparação entre modelos, e alerta que modelos podem concordar numa resposta errada. Isso motivou a nossa métrica de **consenso errado**.

## 12. Hyun, Guo e Babar (2024) — METAL

- **Referência:** Hyun, S., Guo, M., Babar, M. A. METAL: Metamorphic Testing Framework for Analyzing Large-Language Model Qualities. *ICST*, 2024 (arXiv:2312.06056).
- **PDF:** `pdfs/hyun2024metal.pdf`
- **Resumo:** framework de teste metamórfico para atributos de qualidade de LLMs (robustez, justiça etc.). Gera centenas de relações metamórficas a partir de templates e propõe métricas que combinam a taxa de sucesso de ataque com a qualidade semântica do texto.
- **Relação com o nosso trabalho:** precedente mais próximo de teste metamórfico de LLMs numa conferência de teste de software. Diferença: o METAL compara cada modelo consigo mesmo e não tem resposta conhecida.

## 13. Wang et al. (2024) — Software Testing with Large Language Models: Survey

- **Referência:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., Wang, Q. Software Testing With Large Language Models: Survey, Landscape, and Vision. *IEEE Transactions on Software Engineering*, 2024 (arXiv:2307.07221).
- **PDF:** `pdfs/wang2024survey.pdf`
- **Resumo:** revisão de 102 estudos que usam LLMs em teste de software, principalmente para preparar casos de teste e reparar programas; analisa modelos, técnicas de prompt, desafios e oportunidades.
- **Relação com o nosso trabalho:** situa o nosso trabalho no lado menos explorado: testar **os** LLMs, e não usar LLMs para testar outros programas.

## 14. Sclar et al. (2024) — Sensibilidade ao formato do prompt

- **Referência:** Sclar, M., Choi, Y., Tsvetkov, Y., Suhr, A. Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I Learned to Start Worrying about Prompt Formatting. *ICLR*, 2024 (arXiv:2310.11324).
- **PDF:** `pdfs/sclar2024formatting.pdf`
- **Resumo:** vários LLMs abertos são muito sensíveis a mudanças de formatação do prompt que não mudam o sentido; a sensibilidade persiste com modelos maiores, mais exemplos ou ajuste por instrução.
- **Números:** diferença de até 76 pontos de acurácia no LLaMA-2-13B só por formatação.
- **Relação com o nosso trabalho:** motiva gerar muitas formas de dizer o mesmo pedido (paráfrases) e checar se a resposta muda.

## 15. Edman, Schmid e Fraser (2024) — CUTE

- **Referência:** Edman, L., Schmid, H., Fraser, A. CUTE: Measuring LLMs' Understanding of Their Tokens. *EMNLP*, 2024.
- **PDF:** `pdfs/edman2024cute.pdf`
- **Resumo:** LLMs processam tokens de vários caracteres, sem acesso direto às letras. O benchmark CUTE testa conhecimento ortográfico (soletrar, inverter, manipular caracteres) em modelos de 7B a 132B parâmetros.
- **Números/achado:** a maioria dos modelos parece saber como seus tokens se soletram, mas não consegue usar isso para manipular texto.
- **Relação com o nosso trabalho:** explica por que contagem de letras e inversão de strings são categorias difíceis, e por que modelos pequenos devem errar mais nelas.

## 16. Cho, Ruberto e Terragni (2025) — Metamorphic Testing of LLMs for NLP

- **Referência:** Cho, S., Ruberto, S., Terragni, V. Metamorphic Testing of Large Language Models for Natural Language Processing. *ICSME*, pp. 174–186, 2025 (arXiv:2511.02108).
- **PDF:** `pdfs/cho2025metamorphic.pdf`
- **Resumo:** o estudo mais amplo de teste metamórfico de LLMs até então: uma revisão da literatura reuniu 191 relações metamórficas para tarefas de NLP, e 36 delas foram implementadas e testadas em três LLMs.
- **Números:** cerca de 560 mil testes metamórficos.
- **Relação com o nosso trabalho:** confirma o teste metamórfico como forma de contornar a falta de oráculo em LLMs e documenta seus limites; o nosso trabalho soma resposta conhecida e comparação entre modelos.

## 17. Guo et al. (2026) — MORTAR

- **Referência:** Guo, G., Aleti, A., Neelofar, N., Tantithamthavorn, C., Qi, Y., Chen, T. Y. MORTAR: Multi-Turn Metamorphic Testing for LLM-Based Dialogue Systems. *IEEE Transactions on Software Engineering*, 2026 (arXiv:2412.15557).
- **PDF:** `pdfs/guo2026mortar.pdf`
- **Resumo:** teste metamórfico para conversas de várias rodadas com sistemas de diálogo baseados em LLM; gera diálogos de pergunta e resposta com perturbações no nível do diálogo e associa relações metamórficas automaticamente.
- **Números:** em oito sistemas, 51% mais bugs por caso de teste que o melhor método de uma rodada só, com 24,6% mais precisão.
- **Relação com o nosso trabalho:** trabalho mais próximo especificamente sobre chatbots. Nós fazemos teste de uma rodada, mas entre modelos e com resposta conhecida; testar várias rodadas fica como trabalho futuro.

## 18. Qwen Team (2024) — Qwen2.5 Technical Report

- **Referência:** Qwen Team. Qwen2.5 Technical Report. arXiv:2412.15115, 2024.
- **PDF:** `pdfs/qwen2024qwen25.pdf`
- **Resumo:** série de modelos de 0,5B a 72B parâmetros, pré-treinada em 18 trilhões de tokens e ajustada com mais de 1 milhão de exemplos supervisionados e aprendizado por reforço (DPO e GRPO). Destaca melhorias em seguir instruções e em dados estruturados.
- **Relação com o nosso trabalho:** documenta o `Qwen2.5-0.5B-Instruct`, um dos três modelos testados.

## 19. Ben Allal et al. (2025) — SmolLM2

- **Referência:** Ben Allal, L., et al. SmolLM2: When Smol Goes Big — Data-Centric Training of a Small Language Model. arXiv:2502.02737, 2025.
- **PDF:** `pdfs/benallal2025smollm2.pdf`
- **Resumo:** modelo "pequeno" do Hugging Face treinado em cerca de 11 trilhões de tokens, em várias etapas que misturam texto da web com dados especializados de matemática e código. O artigo foca a versão de 1,7B; a família inclui as versões de 360M e 135M.
- **Relação com o nosso trabalho:** documenta o `SmolLM2-360M-Instruct`, um dos três modelos testados.

## 20. Zhang et al. (2024) — TinyLlama

- **Referência:** Zhang, P., Zeng, G., Wang, T., Lu, W. TinyLlama: An Open-Source Small Language Model. arXiv:2401.02385, 2024.
- **PDF:** `pdfs/zhang2024tinyllama.pdf`
- **Resumo:** modelo de 1,1B parâmetros pré-treinado em cerca de 1 trilhão de tokens por até 3 épocas, com a arquitetura e o tokenizador do Llama 2.
- **Relação com o nosso trabalho:** documenta o `TinyLlama-1.1B-Chat-v1.0`, um dos três modelos testados. Usar o tokenizador do Llama 2 importa para interpretar as falhas de contagem de letras.
