# Fuzz Testing em Machine Learning: notas do apresentador

> Conteúdo gerado por IA (Claude). Revise antes de usar.

## 1. cover

Antes de começar: todo este material, do código aos slides, foi gerado por IA (Claude) e deve ser revisado. O trabalho aplica fuzz testing a classificadores de imagem e ao tokenizer do DistilBERT.

## 2. fuzzing

Fuzz testing é testar com entradas geradas automaticamente, em grande quantidade, até achar uma que quebre o sistema. Os fuzzers modernos são guiados por cobertura: guardam as entradas que exercitam partes novas do programa e mutam a partir delas. Em machine learning, um modelo raramente dá crash; a falha típica é errar a predição com uma entrada quase idêntica a uma que ele acerta. Por isso mudam o oráculo, que decide o que é falha, e a cobertura, que passa a ser medida em neurônios.

## 3. modelos

ResNet e ViT fazem a mesma coisa, classificar imagens, mas com arquiteturas diferentes: convolução e atenção. Isso permite comparar as duas com as mesmas imagens. O tokenizer é a porta de entrada do DistilBERT, uma versão compacta do BERT: transforma texto em números. Ele é testado com fuzzing clássico.

## 4. metodo

Os dois fuzzers seguem a mesma ideia: gerar entradas, checar um oráculo e guardar as que exploram partes novas do sistema. Nas imagens, cobertura é de neurônios; no tokenizer, de código Python. Ponto importante: o ambiente não acessava o Hugging Face, então os classificadores rodaram com pesos aleatórios. Os resultados mostram que o pipeline funciona, não a robustez dos modelos treinados.

## 5. resultado-imagens

Com as mesmas sementes e mutações, o ViT falhou 45 vezes e a ResNet nenhuma. Quase todas as falhas do ViT vieram do brilho, a única mutação que usa os 0,08 em todos os pixels; rotação e blur são cortados pela projeção. A cobertura de neurônios não ajudou: saturou no ViT (98%) e travou na ResNet (9%).

## 6. resultado-tokenizer

Com max_length igual a 2, um texto de um caractere vira três tokens no tokenizer em Python, porque o truncamento desiste. O tokenizer rápido trunca corretamente. A entrada tem 6 bytes e reproduz sempre.

## 7. conclusao

Resumo: o código está pronto e encontrou uma falha real no tokenizer. Os números das imagens refletem modelos com pesos aleatórios e não permitem dizer qual arquitetura é mais robusta. Basta rodar sem a opção --random-weights numa máquina com acesso ao Hugging Face.
