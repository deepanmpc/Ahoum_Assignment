"""Ollama local provider adapter."""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from .base import (
    BaseProvider,
    ProviderError,
    ProviderErrorType,
    ProviderResponse,
)


class OllamaProvider(BaseProvider):
    def __init__(self, model: str, base_url: str = "http://localhost:11434",
                 timeout: int = 45):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str) -> ProviderResponse:
        url = f"{self._base_url}/api/generate"
        payload = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0},
        }).encode()

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )

        def _do_request():
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.URLError as exc:
                if "timed out" in str(exc).lower():
                    raise ProviderError(ProviderErrorType.TIMEOUT,
                                        f"Ollama request timed out after {self._timeout}s")
                raise ProviderError(ProviderErrorType.CONNECTION,
                                    f"Cannot reach Ollama at {self._base_url}: {exc}")
            except json.JSONDecodeError:
                raise ProviderError(ProviderErrorType.MALFORMED_RESPONSE,
                                    "Ollama returned non-JSON response")

        body, latency = self._timed_call(_do_request)

        return ProviderResponse(
            text=body.get("response", ""),
            provider_name=self.provider_name,
            model_name=self.model_name,
            latency_ms=latency,
            prompt_tokens=body.get("prompt_eval_count"),
            completion_tokens=body.get("eval_count"),
            total_tokens=(body.get("prompt_eval_count", 0)
                          + body.get("eval_count", 0)) or None,
        )
