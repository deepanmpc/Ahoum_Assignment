"""Configuration loading with environment-only overrides for provider settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True, slots=True)
class AppConfig:
    root_dir: Path
    raw_facets_csv: Path
    facet_catalogue_csv: Path
    embedding_index: Path
    examples_dir: Path
    outputs_dir: Path
    model_provider: str
    model_name: str
    model_base_url: str
    model_timeout_seconds: int
    model_max_retries: int
    retrieval_top_k: int
    retrieval_semantic_weight: float
    retrieval_keyword_weight: float
    scoring_batch_size: int
    scoring_minimum_confidence: float


def load_config(config_path: Path | str = "config.toml") -> AppConfig:
    """Load local configuration without contacting a model provider."""

    path = Path(config_path).resolve()
    with path.open("rb") as config_file:
        values = tomllib.load(config_file)

    root_dir = path.parent
    paths = values["paths"]
    model = values["model"]
    retrieval = values["retrieval"]
    scoring = values["scoring"]
    config = AppConfig(
        root_dir=root_dir,
        raw_facets_csv=root_dir / paths["raw_facets_csv"],
        facet_catalogue_csv=root_dir / paths["facet_catalogue_csv"],
        embedding_index=root_dir / paths["embedding_index"],
        examples_dir=root_dir / paths["examples_dir"],
        outputs_dir=root_dir / paths["outputs_dir"],
        model_provider=os.getenv("AHOUM_MODEL_PROVIDER", model["provider"]),
        model_name=os.getenv("AHOUM_MODEL_NAME", model["name"]),
        model_base_url=os.getenv("AHOUM_MODEL_BASE_URL", model["base_url"]),
        model_timeout_seconds=int(model["timeout_seconds"]),
        model_max_retries=int(model["max_retries"]),
        retrieval_top_k=int(retrieval["top_k"]),
        retrieval_semantic_weight=float(retrieval["semantic_weight"]),
        retrieval_keyword_weight=float(retrieval["keyword_weight"]),
        scoring_batch_size=int(scoring["batch_size"]),
        scoring_minimum_confidence=float(scoring["minimum_confidence"]),
    )

    if config.scoring_batch_size <= 0:
        raise ValueError("scoring_batch_size must be positive")
    if config.retrieval_top_k <= 0:
        raise ValueError("retrieval_top_k must be positive")
    if abs((config.retrieval_semantic_weight + config.retrieval_keyword_weight) - 1.0) > 1e-5:
        raise ValueError("retrieval weights must sum to 1.0")

    return config
