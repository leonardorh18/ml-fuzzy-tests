# Fuzz Testing em Machine Learning: notas do apresentador

> Conteúdo gerado por IA (Claude). Revise antes de usar.

## 1. cover

Antes de começar: todo este material, do código aos slides, foi gerado por IA (Claude) e deve ser revisado. O trabalho aplica fuzz testing a classificadores de imagem e ao tokenizer do DistilBERT.

## 2. fuzzing

Fuzz testing é testar com entradas geradas automaticamente, em massa. O exemplo clássico é um leitor de arquivos: o fuzzer corrompe arquivos válidos de mil formas diferentes até um deles travar o programa. Os fuzzers modernos, como AFL e libFuzzer, são guiados por cobertura: medem que partes do programa cada entrada executou e guardam as que chegaram em lugares novos, para mutar a partir delas. Dois conceitos vão aparecer o tempo todo: o oráculo, que decide se houve falha, e a cobertura, que guia a busca.

## 3. fuzzing-ml

Este é um exemplo real do nosso experimento. A imagem do meio é a da esquerda com o brilho levemente alterado; a diferença, ampliada seis vezes à direita, é de no máximo 0,08 por pixel. Para um humano são a mesma imagem, mas o ViT mudou a classe de 614 para 727. Isso é uma falha. Em ML o modelo quase nunca trava, então o oráculo é outro: a predição não deveria mudar com uma alteração tão pequena. E a cobertura passa a ser medida em neurônios ativados.

## 4. cobertura-conceito

No fuzzing clássico, a cobertura mede linhas de código executadas. Numa rede neural, todas as entradas executam o mesmo código, então mede-se quais neurônios cada entrada ativou. Um neurônio está coberto quando alguma entrada já o ativou com força. Quando um mutante não causa falha mas acende neurônios que nenhuma entrada tinha acendido, ele explorou uma região nova da rede e vira semente para novas mutações. Essa é a ideia do DeepXplore e do TensorFuzz.

## 5. modelos

Os três alvos vêm do Hugging Face. A ResNet-50 é uma rede convolucional clássica para reconhecer objetos em fotos. O ViT, Vision Transformer, faz exatamente a mesma tarefa, mas trata a imagem como uma sequência de quadradinhos, como se fossem palavras. O tokenizer do DistilBERT, uma versão compacta do BERT, transforma texto em números; se ele errar, tudo depois dele recebe a entrada errada. Os exemplos de entrada e saída são ilustrativos do uso normal de cada modelo.

## 6. gerar-imagens

Estas são as seis mutações aplicadas a uma das sementes do teste, no valor mais forte de cada faixa. Repare que elas são visíveis aqui porque mostramos antes do passo 3. Depois do corte, nenhum pixel pode estar a mais de 0,08 da imagem original, uns 20 tons numa escala de 255. É por isso que a imagem que enganou o ViT parecia idêntica à original. O laço roda 500 vezes por modelo.

## 7. gerar-tokenizer

O Atheris é o libFuzzer para Python. Ele gera bytes; nosso código transforma os primeiros bytes num max_length entre 2 e 512 e o resto num texto Unicode. O exemplo na tela é real: são os 6 bytes que encontraram a falha. Eles viram max_length 2 e o texto com a letra Ƒ, e o tokenizer em Python devolveu 3 tokens, violando o oráculo 2. Os outros oráculos checam exceções, ids fora do vocabulário e se codificar e decodificar duas vezes dá o mesmo texto.

## 8. configuracao

As duas redes rodaram nas mesmas condições: mesmas 6 sementes, mesmas mutações, 500 iterações cada, tudo em CPU. O ponto mais importante é o quadro amarelo: sem acesso ao Hugging Face, usamos as arquiteturas reais com pesos aleatórios. Isso vai explicar os resultados que vêm a seguir. O fuzzing do tokenizer em Python parou em menos de um segundo porque encontrou a falha; o limite configurado era 90 segundos.

## 9. resultado-imagens

Com as mesmas sementes e mutações, o ViT falhou 45 vezes e a ResNet nenhuma. Quase todas as falhas do ViT vieram do brilho, a única mutação que usa os 0,08 em todos os pixels; rotação e blur são cortados pela projeção. A cobertura de neurônios não ajudou: saturou no ViT (98%) e travou na ResNet (9%).

## 10. grafico

Este gráfico responde a pergunta sobre cobertura. À esquerda, a cobertura praticamente não se mexe: o ViT já estava quase todo coberto pelas sementes, e a ResNet ficou parada. À direita, as falhas do ViT sobem num ritmo constante, independente da cobertura. Ou seja, aqui a cobertura de neurônios não serviu de guia, o que bate com críticas da literatura a essa métrica.

## 11. resultado-tokenizer

Com max_length igual a 2, um texto de um caractere vira três tokens no tokenizer em Python: ele registra que não consegue truncar e devolve a sequência inteira. O tokenizer rápido trunca corretamente. A tabela mostra por que só o Python encontrou a falha: o tokenizer rápido é escrito em Rust, que o Atheris não enxerga, então a cobertura ficou parada em 141 e as 259 mil execuções foram, na prática, aleatórias. No Python, a cobertura dobrou e a falha apareceu em menos de um segundo.

## 12. conclusao

Fechando com as cinco perguntas do início. Perturbações pequenas trocaram a classe no ViT; o brilho foi a mutação mais eficaz. A comparação entre ResNet e ViT fica inconclusiva: com pesos aleatórios, a ResNet sempre responde a mesma classe e o ViT está quase indeciso. A cobertura de neurônios não ajudou. E o fuzzing do tokenizer achou uma falha real de truncamento na versão em Python. O próximo passo é rodar tudo com os pesos treinados.
