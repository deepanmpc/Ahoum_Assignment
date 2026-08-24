"""Tests for provider abstraction (D1)."""

import pytest
import os

from ahoum_assignment.providers.base import (
    ProviderError, ProviderErrorType, ProviderResponse, BaseProvider,
)
from ahoum_assignment.providers.ollama import OllamaProvider
from ahoum_assignment.providers.openai_compatible import OpenAICompatibleProvider
from ahoum_assignment.providers.factory import create_provider
from ahoum_assignment.config import AppConfig
from pathlib import Path


def test_provider_error_redacts_secrets():
    err = ProviderError(ProviderErrorType.AUTH, "Key sk-abc123xyz is invalid")
    assert "sk-abc123xyz" not in str(err)
    assert "[REDACTED]" in str(err)


def test_provider_error_types():
    for t in ProviderErrorType:
        err = ProviderError(t, f"test {t.value}")
        assert err.error_type == t


def test_ollama_provider_properties():
    p = OllamaProvider("qwen2.5:3b-instruct", "http://localhost:11434", 30)
    assert p.provider_name == "ollama"
    assert p.model_name == "qwen2.5:3b-instruct"


def test_openai_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderError) as exc_info:
        OpenAICompatibleProvider("groq", "some-model")
    assert exc_info.value.error_type == ProviderErrorType.AUTH
    assert "Missing API key" in str(exc_info.value)


def test_openai_with_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")
    p = OpenAICompatibleProvider("groq", "llama-3.1-8b")
    assert p.provider_name == "groq"
    assert p.model_name == "llama-3.1-8b"


def test_factory_creates_ollama(tmp_path):
    cfg = AppConfig(
        root_dir=tmp_path, raw_facets_csv=tmp_path / "r.csv",
        facet_catalogue_csv=tmp_path / "c.csv",
        embedding_index=tmp_path / "e.npz",
        examples_dir=tmp_path / "ex", outputs_dir=tmp_path / "out",
        model_provider="ollama", model_name="qwen2.5:3b-instruct",
        model_base_url="http://localhost:11434",
        model_timeout_seconds=30, model_max_retries=1,
        retrieval_top_k=20, retrieval_semantic_weight=0.6,
        retrieval_keyword_weight=0.4, scoring_batch_size=5,
        scoring_minimum_confidence=0.55,
    )
    provider = create_provider(cfg)
    assert provider.provider_name == "ollama"


def test_factory_rejects_unknown(tmp_path):
    cfg = AppConfig(
        root_dir=tmp_path, raw_facets_csv=tmp_path / "r.csv",
        facet_catalogue_csv=tmp_path / "c.csv",
        embedding_index=tmp_path / "e.npz",
        examples_dir=tmp_path / "ex", outputs_dir=tmp_path / "out",
        model_provider="unknown_provider", model_name="x",
        model_base_url="http://localhost:1234",
        model_timeout_seconds=30, model_max_retries=1,
        retrieval_top_k=20, retrieval_semantic_weight=0.6,
        retrieval_keyword_weight=0.4, scoring_batch_size=5,
        scoring_minimum_confidence=0.55,
    )
    with pytest.raises(ProviderError):
        create_provider(cfg)


def test_provider_response_metadata():
    r = ProviderResponse(
        text="hello", provider_name="ollama", model_name="qwen",
        latency_ms=42.5, prompt_tokens=10, completion_tokens=5,
        total_tokens=15,
    )
    assert r.total_tokens == 15
    assert r.latency_ms == 42.5
