"""Testa o cliente da API contra uma sessão HTTP falsa (sem rede)."""

import pytest
import requests

from chatfuzz.clients import APIClient, make_client


class FakeResponse:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def ok(text):
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("chatfuzz.clients.time.sleep", lambda s: None)


def test_success_sends_openai_compatible_request():
    session = FakeSession([ok("hi")])
    client = APIClient("org/model", token="t", session=session)
    resp = client.chat("hello")
    assert resp.text == "hi" and resp.error is None and resp.model == "api:org/model"
    call = session.calls[0]
    assert call["url"].endswith("/chat/completions")
    assert call["json"]["model"] == "org/model"
    assert call["json"]["messages"] == [{"role": "user", "content": "hello"}]
    assert call["headers"]["Authorization"] == "Bearer t"
    assert resp.truncated is False


def test_finish_reason_length_marks_truncation():
    reply = FakeResponse(200, {"choices": [{"message": {"content": "long"}, "finish_reason": "length"}]})
    assert APIClient("m", token="t", session=FakeSession([reply])).chat("x").truncated is True


def test_retries_transient_errors_then_succeeds():
    session = FakeSession([FakeResponse(503), requests.Timeout(), ok("done")])
    resp = APIClient("m", token="t", session=session, max_retries=3).chat("x")
    assert resp.text == "done" and len(session.calls) == 3


def test_client_errors_are_not_retried_and_become_data():
    session = FakeSession([FakeResponse(401)])
    resp = APIClient("m", token="t", session=session).chat("x")
    assert resp.error == "http_401" and len(session.calls) == 1


def test_malformed_response():
    resp = APIClient("m", token="t", session=FakeSession([FakeResponse(200, {"x": 1})])).chat("x")
    assert resp.error == "malformed_response"


def test_make_client_rejects_unknown_backend():
    with pytest.raises(ValueError):
        make_client("openai:gpt")
