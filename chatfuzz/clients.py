"""Clientes de chatbot: modelos locais (baixados do Hugging Face) e a API do Hugging Face.

Um modelo é indicado por uma especificação com prefixo:

    local:Qwen/Qwen2.5-0.5B-Instruct                 baixa e roda na máquina (transformers)
    api:meta-llama/Llama-3.1-8B-Instruct             Hugging Face Inference Providers
    api:meta-llama/Llama-3.1-8B-Instruct:novita      idem, forçando um provedor

Todos devolvem um ChatResponse; erros viram dados (campo `error`), nunca exceções,
porque um erro da API também é um resultado do fuzzing.
"""

import os
import time
from dataclasses import dataclass

HF_ROUTER_URL = "https://router.huggingface.co/v1"
RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass
class ChatResponse:
    model: str
    text: str
    error: str | None = None
    status_code: int | None = None
    latency_s: float = 0.0
    truncated: bool = False   # a resposta parou no limite de tokens


class APIClient:
    """Endpoint compatível com OpenAI (/chat/completions). Por padrão, o roteador do Hugging Face."""

    def __init__(self, model, token=None, base_url=HF_ROUTER_URL, timeout=60, max_retries=3,
                 temperature=0.0, max_tokens=256, session=None):
        import requests
        self.spec = f"api:{model}"
        self.model = model
        self.token = token or os.environ.get("HF_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.session = session or requests.Session()
        self._requests = requests

    def chat(self, prompt):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature, "max_tokens": self.max_tokens}
        start = time.time()
        for attempt in range(self.max_retries + 1):
            try:
                r = self.session.post(f"{self.base_url}/chat/completions", json=body,
                                      headers=headers, timeout=self.timeout)
            except self._requests.Timeout:
                error, status = "timeout", None
            except self._requests.RequestException as e:
                error, status = f"connection_error: {type(e).__name__}", None
            else:
                status = r.status_code
                if status == 200:
                    try:
                        choice = r.json()["choices"][0]
                        text = choice["message"]["content"] or ""
                    except (ValueError, KeyError, IndexError, TypeError):
                        return ChatResponse(self.spec, "", "malformed_response", status, time.time() - start)
                    return ChatResponse(self.spec, text, None, status, time.time() - start,
                                        truncated=choice.get("finish_reason") == "length")
                error = f"http_{status}"
                if status not in RETRY_STATUS:
                    break
            if attempt < self.max_retries:
                time.sleep(min(2 ** attempt, 30))
        return ChatResponse(self.spec, "", error, status, time.time() - start)


class LocalClient:
    """Baixa o modelo do Hugging Face (fica no cache) e gera com decodificação gulosa."""

    def __init__(self, model, max_tokens=256, device=None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.spec = f"local:{model}"
        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(model).to(self.device).eval()
        self.model.generation_config.max_length = None  # vale só max_new_tokens
        self.max_tokens = max_tokens

    def chat(self, prompt):
        start = time.time()
        try:
            ids = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], add_generation_prompt=True,
                return_tensors="pt", return_dict=True)["input_ids"].to(self.device)
            with self.torch.no_grad():
                out = self.model.generate(ids, max_new_tokens=self.max_tokens, do_sample=False,
                                          pad_token_id=self.tokenizer.eos_token_id)
            new_tokens = out[0, ids.shape[1]:]
            text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            truncated = len(new_tokens) >= self.max_tokens and new_tokens[-1] != self.tokenizer.eos_token_id
            return ChatResponse(self.spec, text, None, None, time.time() - start, truncated=bool(truncated))
        except Exception as e:  # um crash do modelo é um achado, não deve parar o fuzzing
            return ChatResponse(self.spec, "", f"exception: {type(e).__name__}: {e}"[:300],
                                None, time.time() - start)


def make_client(spec, **kwargs):
    backend, _, model = spec.partition(":")
    if backend == "local":
        return LocalClient(model, max_tokens=kwargs.get("max_tokens", 256))
    if backend == "api":
        return APIClient(model, **kwargs)
    raise ValueError(f"especificação inválida '{spec}': use local:<modelo> ou api:<modelo>")
