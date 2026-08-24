from pathlib import Path
import os
import pytest

from ahoum_assignment.config import load_config


def test_load_config_uses_project_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config.toml")

    assert config.retrieval_top_k == 24
    assert config.retrieval_semantic_weight == 0.70
    assert config.retrieval_keyword_weight == 0.30
    assert config.scoring_batch_size == 5
    assert config.scoring_minimum_confidence == 0.55
    assert config.raw_facets_csv.name == "Facets Assignment.csv"


def test_load_config_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[1]
    
    monkeypatch.setenv("AHOUM_MODEL_PROVIDER", "mock_provider")
    monkeypatch.setenv("AHOUM_MODEL_NAME", "mock_model:latest")
    monkeypatch.setenv("AHOUM_MODEL_BASE_URL", "http://mock-url:1111")
    
    config = load_config(root / "config.toml")
    
    assert config.model_provider == "mock_provider"
    assert config.model_name == "mock_model:latest"
    assert config.model_base_url == "http://mock-url:1111"
