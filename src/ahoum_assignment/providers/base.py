"""Base provider interface for structured LLM generation."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ProviderErrorType(str, Enum):
    TIMEOUT = "timeout"
    AUTH = "auth"
    CONNECTION = "connection"
    RATE_LIMIT = "rate_limit"
    MALFORMED_RESPONSE = "malformed_response"
    PROVIDER_ERROR = "provider_error"


class ProviderError(Exception):
    """Safe error that never exposes secrets."""

    def __init__(self, error_type: ProviderErrorType, message: str):
        self.error_type = error_type
        # Strip anything that looks like a key from the message
        safe_msg = message
        for prefix in ("sk-", "gsk_", "nvapi-", "Bearer "):
            if prefix in safe_msg:
                safe_msg = safe_msg.replace(
                    safe_msg[safe_msg.index(prefix):], "[REDACTED]"
                )
        super().__init__(safe_msg)
        self.safe_message = safe_msg


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """Immutable record of a single provider call."""

    text: str
    provider_name: str
    model_name: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency_ms: float = 0.0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def generate(self, prompt: str) -> ProviderResponse:
        """Send a prompt and return a structured response.

        Must raise ``ProviderError`` on failure, never leaking secrets.
        """
        ...

    def _timed_call(self, fn, *args, **kwargs):
        """Helper that measures wall-clock latency."""
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return result, elapsed_ms
