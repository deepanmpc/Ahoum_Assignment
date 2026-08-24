"""OpenAI-compatible chat-completions adapter for Groq, NVIDIA NIM, OpenRouter."""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Optional

from .base import (
    BaseProvider,
    ProviderError,
    ProviderErrorType,
    ProviderResponse,
)

# Maps provider name -> (env var for key, default base URL)
_CLOUD_REGISTRY: dict[str, tuple[str, str]] = {
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1"),
    "nvidia": ("NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1"),
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
}


class OpenAICompatibleProvider(BaseProvider):
    """Provider for any OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        provider: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        self._provider = provider.lower()
        self._model = model
        self._timeout = timeout

        if self._provider in _CLOUD_REGISTRY:
            env_var, default_url = _CLOUD_REGISTRY[self._provider]
            self._api_key = os.environ.get(env_var, "")
            self._base_url = (base_url or default_url).rstrip("/")
        else:
            # Generic OpenAI-compatible endpoint
            self._api_key = os.environ.get("OPENAI_API_KEY", "")
            self._base_url = (base_url or "http://localhost:8000/v1").rstrip("/")

        if not self._api_key:
            raise ProviderError(
                ProviderErrorType.AUTH,
                f"Missing API key for provider '{self._provider}'. "
                f"Set the appropriate environment variable.",
            )

    @property
    def provider_name(self) -> str:
        return self._provider

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str) -> ProviderResponse:
        url = f"{self._base_url}/chat/completions"
        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 2048,
        }).encode()

        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

        def _do_request():
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                status = exc.code
                if status == 401:
                    raise ProviderError(ProviderErrorType.AUTH,
                                        f"Authentication failed for {self._provider}")
                if status == 429:
                    raise ProviderError(ProviderErrorType.RATE_LIMIT,
                                        f"Rate limited by {self._provider}")
                raise ProviderError(ProviderErrorType.PROVIDER_ERROR,
                                    f"{self._provider} returned HTTP {status}")
            except urllib.error.URLError as exc:
                if "timed out" in str(exc).lower():
                    raise ProviderError(ProviderErrorType.TIMEOUT,
                                        f"Request to {self._provider} timed out")
                raise ProviderError(ProviderErrorType.CONNECTION,
                                    f"Cannot reach {self._provider}: {exc}")
            except json.JSONDecodeError:
                raise ProviderError(ProviderErrorType.MALFORMED_RESPONSE,
                                    f"{self._provider} returned non-JSON response")

        body, latency = self._timed_call(_do_request)

        choices = body.get("choices", [])
        text = choices[0]["message"]["content"] if choices else ""
        usage = body.get("usage", {})

        return ProviderResponse(
            text=text,
            provider_name=self.provider_name,
            model_name=self.model_name,
            request_id=body.get("id", ""),
            latency_ms=latency,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
