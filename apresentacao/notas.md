# Fuzz Testing for Machine Learning: speaker notes

> AI-generated content (Claude). Review before use.

## 1. cover

Before we begin: all of this material, from the code to the slides, was generated with AI (Claude) and should be reviewed. This work applies fuzz testing to two image classifiers and to the DistilBERT tokenizer.

## 2. fuzzing

Fuzz testing means testing with inputs that are generated automatically and in bulk. The classic example is a file reader: the fuzzer corrupts valid files in thousands of ways until one of them crashes the program. Modern fuzzers such as AFL and libFuzzer are coverage-guided: they record which parts of the program each input executed and keep the inputs that reached new code, so that they can mutate them further. Two concepts will appear throughout the talk: the oracle, which decides whether a failure occurred, and coverage, which guides the search.

## 3. fuzzing-ml

This is a real example from our experiment. The middle image is the left one with slightly altered brightness; the difference, magnified six times on the right, is at most 0.08 per pixel. To a human they are the same image, but the ViT changed its prediction from class 614 to class 727. That is a failure. In ML the model almost never crashes, so the oracle is different: the prediction should not change under such a small perturbation. Coverage, in turn, is measured in activated neurons.

## 4. cobertura-conceito

In classical fuzzing, coverage counts executed lines of code. In a neural network every input runs the same code, so we measure which neurons each input activated instead. A neuron is covered once some input has activated it strongly. When a mutant does not cause a failure but activates neurons that no previous input had activated, it has explored a new region of the network and becomes a seed for further mutations. This is the idea behind DeepXplore and TensorFuzz.

## 5. modelos

All three targets come from Hugging Face. ResNet-50 is a classic convolutional network for recognizing objects in photos. ViT, the Vision Transformer, performs exactly the same task but treats the image as a sequence of small patches, much as a language model treats words. The DistilBERT tokenizer, DistilBERT being a compact version of BERT, turns text into numbers; if it fails, everything downstream receives the wrong input. The input and output examples illustrate normal use of each model.

## 6. gerar-imagens

These are the six mutations applied to one of the seeds from our run, each at the strongest value of its range. They are visible here because we show them before step 3. After clipping, no pixel may lie more than 0.08 from the original image, about 20 intensity levels on a 255 scale. That is why the image that fooled the ViT looked identical to the original. The loop runs 500 times per model.

## 7. gerar-tokenizer

Atheris is libFuzzer for Python. It generates bytes; our harness turns the leading bytes into a max_length between 2 and 512 and the rest into a Unicode string. The example on screen is real: these are the six bytes that triggered the failure. They decode to max_length 2 and the string containing the letter Ƒ, and the pure-Python tokenizer returned three tokens, violating oracle 2. The other oracles check for exceptions, for ids outside the vocabulary, and for whether decoding and re-encoding twice yields the same text.

## 8. configuracao

Both networks ran under the same conditions: the same six seeds, the same mutations, 500 iterations each, all on CPU. The most important point is the yellow box: without access to Hugging Face, we used the real architectures with random weights. This explains the results that follow. The pure-Python tokenizer run stopped after less than a second because it found the failure; the configured limit was 90 seconds.

## 9. resultado-imagens

With the same seeds and mutations, the ViT failed 45 times and ResNet never failed. Almost all ViT failures came from brightness, the only mutation that spends the full 0.08 budget on every pixel; rotation and blur are largely undone by the projection. On their own, these numbers do not show that ViT is less robust, as the discussion will explain.

## 10. grafico

This chart addresses the coverage question. On the left, coverage barely moves: the seeds already covered almost all ViT neurons, and ResNet coverage stalled. On the right, ViT failures rise at a steady rate regardless of coverage. In this experiment, neuron coverage did not act as a useful guide. The correlation rests on only five windows of 100 iterations, so it is weak evidence.

## 11. resultado-tokenizer

With max_length equal to 2, a one-character string becomes three tokens in the pure-Python tokenizer: it logs that it cannot truncate and returns the whole sequence. The fast tokenizer truncates correctly. The table shows why only the Python run found the failure: the fast tokenizer is written in Rust, which Atheris cannot observe, so coverage stopped at 141 edges and the 259,000 executions were effectively random. With the Python tokenizer, coverage doubled and the failure appeared in under a second.

## 12. conclusao

To close, the five research questions from the start. Small perturbations changed the ViT's predictions, and brightness was the most effective mutation. The ResNet versus ViT comparison is inconclusive: with random weights, ResNet always returns the same class and the ViT is nearly undecided. Neuron coverage did not help. The tokenizer fuzzer found a genuine truncation failure in the Python implementation. The next step is to rerun everything with the trained weights.
