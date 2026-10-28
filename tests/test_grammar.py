from chatfuzz.grammar import CATEGORIES, GRAMMAR, GrammarFuzzer


def test_generation_is_deterministic_for_a_seed():
    a = GrammarFuzzer(seed=7).generate(12, variants=2)
    b = GrammarFuzzer(seed=7).generate(12, variants=2)
    assert [c.prompt for c in a] == [c.prompt for c in b]


def test_variants_share_skeleton_and_differ_in_wording():
    cases = GrammarFuzzer(seed=1).generate(6, variants=3)
    by_group = {}
    for c in cases:
        by_group.setdefault(c.group_id, []).append(c)
    for group in by_group.values():
        assert len({c.prompt for c in group}) == len(group)
        assert len({str(c.expected) for c in group}) == 1


def test_expected_answers_match_values():
    fuzzer = GrammarFuzzer(seed=3)
    for case in fuzzer.generate(60, variants=1):
        v = case.values
        if case.category == "arith":
            assert case.expected == {"add": v["a"] + v["b"], "sub": v["a"] - v["b"],
                                     "mul": v["a"] * v["b"]}[v["op"]]
            assert str(v["a"]) in case.prompt and str(v["b"]) in case.prompt
        elif case.category == "count":
            assert case.expected == v["word"].count(v["letter"])
        elif case.category == "reverse":
            assert case.expected == v["token"][::-1]
        elif case.category == "echo":
            assert case.expected in case.prompt


def test_coverage_guidance_reaches_full_grammar():
    fuzzer = GrammarFuzzer(seed=0, coverage_bias=1.0)
    fuzzer.generate(len(CATEGORIES) * 8, variants=3)
    assert fuzzer.coverage() > 0.95


def test_every_category_has_a_rule():
    assert all(f"<{c}>" in GRAMMAR for c in CATEGORIES)
