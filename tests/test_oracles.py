from chatfuzz.clients import ChatResponse
from chatfuzz.oracles import check, extract_int, normalize_text, parse_json_object


def resp(text, error=None):
    return ChatResponse(model="m", text=text, error=error)


def test_extract_int_takes_last_number_and_handles_separators():
    assert extract_int("3 + 4 = 7") == 7
    assert extract_int("The answer is 1,234.") == 1234
    assert extract_int("−12") == -12
    assert extract_int("no digits") is None


def test_normalize_text_strips_quotes_and_fences():
    assert normalize_text("```\ncba\n```") == "cba"
    assert normalize_text('"cba".') == "cba"


def test_parse_json_object():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object("[1, 2]") is None
    assert parse_json_object("Here: {") is None


def test_check_per_category():
    assert check("arith", 7, resp("7")).passed is True
    assert check("arith", 7, resp("8")).reason == "wrong_answer"
    assert check("count", 3, resp("three")).reason == "no_number"
    assert check("reverse", "cba", resp("'cba'")).passed is True
    assert check("json", ["age", "name"], resp('{"name": "x", "age": 1}')).passed is True
    assert check("json", ["age", "name"], resp('{"name": "x"}')).reason == "missing_keys"
    assert check("json", ["a"], resp("not json")).reason == "invalid_json"
    assert check("echo", "olá 👋", resp("Sure: olá 👋")).passed is True
    assert check("edge", None, resp("anything")).passed is None


def test_errors_and_empty_responses():
    assert check("arith", 1, resp("", error="http_500")).reason == "api_error"
    assert check("arith", 1, resp("   ")).reason == "empty"
