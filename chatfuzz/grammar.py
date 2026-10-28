"""Gramática livre de contexto que gera prompts para chatbots.

Cada caso de teste nasce de um *esqueleto* (categoria + valores sorteados, como os
números de uma conta) e de uma *derivação* da gramática, que escolhe as palavras.
Como os valores ficam guardados, cada caso sabe a resposta esperada, e variantes
do mesmo esqueleto (paráfrases) devem receber a mesma resposta.

A escolha das expansões é guiada por cobertura da gramática (como o
GrammarCoverageFuzzer de "The Fuzzing Book"): expansões ainda não usadas têm
prioridade, para que todas as formas de pedir algo sejam exercitadas.
"""

import random
import re
import string
from dataclasses import dataclass, field

# Símbolos não terminais aparecem entre <>. Um símbolo que não está na gramática é
# lido dos valores do caso (ex.: <a>). Se existir <nome_VALOR> na gramática, ele é
# expandido no lugar de <nome> (ex.: <op> com op=add expande <op_add>).
# Cada categoria é um símbolo inicial; o fuzzer alterna entre elas.
GRAMMAR = {
    "<arith>": [
        "<what_is> <a> <op> <b>?<sep><only_number>",
        "<please> <compute> <a> <op> <b>.<sep><only_number>",
        "<a> <op> <b> = ?<sep><only_number>",
    ],
    "<what_is>": ["What is", "How much is", "What's the result of"],
    "<please>": ["Please", "Kindly"],
    "<compute>": ["compute", "calculate", "work out"],
    "<op_add>": ["+", "plus"],
    "<op_sub>": ["-", "minus"],
    "<op_mul>": ["*", "times", "multiplied by"],
    "<only_number>": [
        "Answer with only the number.",
        "Reply with just the final number.",
        "Give only the numeric result.",
    ],

    "<count>": [
        "How many times does the letter '<letter>' appear in the word '<word>'?<sep><only_number>",
        "Count the occurrences of the letter '<letter>' in '<word>'.<sep><only_number>",
        "In the word \"<word>\", how many '<letter>' characters are there?<sep><only_number>",
    ],

    "<reverse>": [
        "Reverse the string '<token>'.<sep><only_text>",
        "Write '<token>' backwards.<sep><only_text>",
        "What is '<token>' spelled in reverse order?<sep><only_text>",
    ],
    "<only_text>": [
        "Reply with the result only.",
        "Output only the reversed string, without quotes.",
    ],

    "<json>": [
        "Return a JSON object with the keys <keys>.<sep><json_only>",
        "Create a JSON object containing the fields <keys>, with any values.<sep><json_only>",
    ],
    "<json_only>": ["Reply with JSON only.", "Output valid JSON and nothing else."],

    "<echo>": [
        "Repeat exactly the following text, without any change: <payload>",
        "Copy this text verbatim and reply with nothing else:<sep><payload>",
    ],

    "<edge>": [
        "<payload>",
        "<payload> <payload>",
        "Translate to Portuguese: <payload>",
        "Summarize in one sentence: <payload>",
    ],

    "<sep>": [" ", "\n"],
}

CATEGORIES = ["arith", "count", "reverse", "json", "echo", "edge"]

WORDS = ["strawberry", "mississippi", "banana", "bookkeeper", "onomatopoeia",
         "committee", "assessment", "parallel", "possession", "referrer"]
JSON_KEYS = ["name", "age", "city", "email", "score", "active", "tags", "id"]

# Entradas difíceis: Unicode variado, escrita da direita para a esquerda, emoji
# compostos, caracteres invisíveis, marcação e texto muito longo.
PAYLOADS = [
    "naïve café résumé",
    "日本語のテキストです",
    "مرحبا بالعالم",
    "👩‍💻🚀🇧🇷",
    "zero​width​space",
    "tab\tseparated\tvalues",
    "<b>bold</b> & <i>italic</i>",
    "{\"key\": [1, 2, 3]}",
    "line one\nline two",
    "ab" * 150,
    "Ω≈ç√∫˜µ≤≥÷",
    "ﬁ ﬂ ligatures",
]


@dataclass
class TestCase:
    __test__ = False  # não é uma classe de teste do pytest

    case_id: str
    group_id: str
    variant: int
    category: str
    prompt: str
    expected: object
    values: dict = field(default_factory=dict)


class GrammarFuzzer:
    """Deriva prompts da gramática, preferindo expansões ainda não cobertas."""

    def __init__(self, grammar=GRAMMAR, seed=0, coverage_bias=0.8, max_depth=12):
        self.grammar = grammar
        self.rng = random.Random(seed)
        self.coverage_bias = coverage_bias
        self.max_depth = max_depth
        self.covered = set()

    # -- cobertura -----------------------------------------------------------
    def all_expansions(self):
        return {(sym, i) for sym, exps in self.grammar.items() for i in range(len(exps))}

    def coverage(self):
        total = self.all_expansions()
        return len(self.covered & total) / len(total)

    def _choose(self, symbol):
        expansions = self.grammar[symbol]
        uncovered = [i for i in range(len(expansions)) if (symbol, i) not in self.covered]
        if uncovered and self.rng.random() < self.coverage_bias:
            i = self.rng.choice(uncovered)
        else:
            i = self.rng.randrange(len(expansions))
        self.covered.add((symbol, i))
        return expansions[i]

    # -- derivação ----------------------------------------------------------
    def expand(self, symbol, values, depth=0):
        if depth > self.max_depth:
            raise RecursionError(f"derivação passou de {self.max_depth} níveis em {symbol}")
        name = symbol[1:-1]
        if symbol not in self.grammar:
            keyed = f"<{name}_{values.get(name)}>"
            if keyed in self.grammar:
                symbol = keyed
            elif name in values:
                return str(values[name])
            else:
                raise KeyError(f"símbolo sem regra nem valor: {symbol}")
        expansion = self._choose(symbol)
        return re.sub(r"<[a-z_]+>", lambda m: self.expand(m.group(0), values, depth + 1), expansion)

    # -- esqueletos ---------------------------------------------------------
    def _number(self):
        kind = self.rng.random()
        if kind < 0.3:
            return self.rng.randint(0, 9)
        if kind < 0.7:
            return self.rng.randint(10, 999)
        if kind < 0.9:
            return self.rng.randint(1000, 999_999)
        return -self.rng.randint(1, 999)

    def skeleton(self, category):
        rng = self.rng
        if category == "arith":
            a, b, op = self._number(), self._number(), rng.choice(["add", "sub", "mul"])
            result = {"add": a + b, "sub": a - b, "mul": a * b}[op]
            return {"a": a, "b": b, "op": op}, result
        if category == "count":
            word = rng.choice(WORDS)
            letter = rng.choice(word) if rng.random() < 0.85 else rng.choice(
                [c for c in string.ascii_lowercase if c not in word])
            return {"word": word, "letter": letter}, word.count(letter)
        if category == "reverse":
            token = "".join(rng.choice(string.ascii_letters + string.digits)
                            for _ in range(rng.randint(4, 12)))
            return {"token": token}, token[::-1]
        if category == "json":
            keys = rng.sample(JSON_KEYS, rng.randint(2, 4))
            quoted = [f'"{k}"' for k in keys]
            return {"keys": ", ".join(quoted[:-1]) + " and " + quoted[-1]}, sorted(keys)
        if category in ("echo", "edge"):
            payload = rng.choice(PAYLOADS)
            return {"payload": payload}, payload if category == "echo" else None
        raise ValueError(f"categoria desconhecida: {category}")

    def generate(self, n_cases, variants=3, categories=CATEGORIES):
        """Gera n_cases esqueletos, cada um com até `variants` paráfrases distintas."""
        cases = []
        for g in range(n_cases):
            category = categories[g % len(categories)]
            values, expected = self.skeleton(category)
            prompts, wordings = [], set()
            for _ in range(variants * 10):
                prompt = self.expand(f"<{category}>", values).strip(" ")
                wording = " ".join(prompt.split())  # paráfrases devem diferir em palavras
                if wording not in wordings:
                    wordings.add(wording)
                    prompts.append(prompt)
                if len(prompts) == variants:
                    break
            for v, prompt in enumerate(prompts):
                cases.append(TestCase(case_id=f"{g:04d}-{v}", group_id=f"{g:04d}", variant=v,
                                      category=category, prompt=prompt, expected=expected,
                                      values=values))
        return cases
