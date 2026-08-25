import pytest
from pathlib import Path
from ahoum_assignment.config import load_config
import tomllib
import os

def test_config_valid(tmp_path):
    config_content = """
[paths]
raw_facets_csv = "data/raw/facets.csv"
facet_catalogue_csv = "data/processed/facet_catalogue.csv"
embedding_index = "data/processed/facet_embeddings.npz"
examples_dir = "data/examples"
outputs_dir = "data/outputs"

[model]
provider = "mock"
name = "mock"
base_url = "http://localhost:11434"
timeout_seconds = 30
max_retries = 3

[retrieval]
top_k = 20
semantic_weight = 0.6
keyword_weight = 0.4

[scoring]
batch_size = 5
minimum_confidence = 0.6
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)
    
    cfg = load_config(config_path)
    assert cfg.scoring_batch_size == 5

def test_config_invalid_batch_size(tmp_path):
    config_content = """
[paths]
raw_facets_csv = "data/raw/facets.csv"
facet_catalogue_csv = "data/processed/facet_catalogue.csv"
embedding_index = "data/processed/facet_embeddings.npz"
examples_dir = "data/examples"
outputs_dir = "data/outputs"

[model]
provider = "mock"
name = "mock"
base_url = "http://localhost:11434"
timeout_seconds = 30
max_retries = 3

[retrieval]
top_k = 20
semantic_weight = 0.6
keyword_weight = 0.4

[scoring]
batch_size = -1
minimum_confidence = 0.6
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)
    
    with pytest.raises(ValueError, match="scoring_batch_size must be positive"):
        load_config(config_path)

def test_config_invalid_weights(tmp_path):
    config_content = """
[paths]
raw_facets_csv = "data/raw/facets.csv"
facet_catalogue_csv = "data/processed/facet_catalogue.csv"
embedding_index = "data/processed/facet_embeddings.npz"
examples_dir = "data/examples"
outputs_dir = "data/outputs"

[model]
provider = "mock"
name = "mock"
base_url = "http://localhost:11434"
timeout_seconds = 30
max_retries = 3

[retrieval]
top_k = 20
semantic_weight = 0.8
keyword_weight = 0.8

[scoring]
batch_size = 5
minimum_confidence = 0.6
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)
    
    with pytest.raises(ValueError, match="retrieval weights must sum to 1.0"):
        load_config(config_path)
