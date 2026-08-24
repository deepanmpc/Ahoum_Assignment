"""Provider factory — selects the right backend from configuration."""

from __future__ import annotations

from ahoum_assignment.config import AppConfig
from .base import BaseProvider, ProviderError, ProviderErrorType
from .ollama import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider

_CLOUD_PROVIDERS = {"groq", "nvidia", "openrouter"}


def create_provider(config: AppConfig) -> BaseProvider:
    """Instantiate the correct provider from the active configuration.

    Raises ``ProviderError`` with a safe message if configuration is
    missing or invalid.
    """
    provider = config.model_provider.lower()

    if provider == "ollama":
        return OllamaProvider(
            model=config.model_name,
            base_url=config.model_base_url,
            timeout=config.model_timeout_seconds,
        )

    if provider in _CLOUD_PROVIDERS:
        return OpenAICompatibleProvider(
            provider=provider,
            model=config.model_name,
            base_url=config.model_base_url,
            timeout=config.model_timeout_seconds,
        )

    raise ProviderError(
        ProviderErrorType.PROVIDER_ERROR,
        f"Unknown provider '{provider}'. "
        f"Supported: ollama, groq, nvidia, openrouter.",
    )
