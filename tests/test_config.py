from pathlib import Path

from ahoum_assignment.config import load_config


def test_load_config_uses_project_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config.toml")

    assert config.retrieval_top_k == 24
    assert config.scoring_batch_size == 5
    assert config.raw_facets_csv.name == "Facets Assignment.csv"
