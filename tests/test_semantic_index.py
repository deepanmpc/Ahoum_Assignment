import pytest
import csv
import numpy as np
from pathlib import Path

from ahoum_assignment.embeddings import FakeDeterministicEmbedder
from ahoum_assignment.semantic_index import (
    is_eligible,
    build_index,
    load_index,
    check_index_freshness
)

def test_eligible_facets():
    valid = {
        "conversation_observable": "true",
        "is_malformed": "false",
        "review_required": "false",
        "scoring_definition": "Def",
        "anchor_1": "A1",
        "anchor_5": "A5"
    }
    assert is_eligible(valid) is True
    
    # Missing anchor
    invalid1 = dict(valid, anchor_1="")
    assert is_eligible(invalid1) is False
    
    # Non-observable
    invalid2 = dict(valid, conversation_observable="false")
    assert is_eligible(invalid2) is False
    
    # Review required
    invalid3 = dict(valid, review_required="true")
    assert is_eligible(invalid3) is False

def test_empty_failure(tmp_path: Path):
    cat_path = tmp_path / "cat.csv"
    npz_path = tmp_path / "emb.npz"
    meta_path = tmp_path / "meta.json"
    
    cat_path.write_text("facet_id,conversation_observable\n1,false")
    
    embedder = FakeDeterministicEmbedder(dim=4)
    with pytest.raises(ValueError, match="no valid observable facets"):
        build_index(cat_path, npz_path, meta_path, embedder)

def test_vector_normalization_and_metadata(tmp_path: Path):
    cat_path = tmp_path / "cat.csv"
    npz_path = tmp_path / "emb.npz"
    meta_path = tmp_path / "meta.json"
    
    fields = ["facet_id", "conversation_observable", "is_malformed", "review_required", "scoring_definition", "anchor_1", "anchor_5", "facet_normalized", "facet_category", "facet_type"]
    
    with open(cat_path, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "facet_id": "f2", "conversation_observable": "true", "is_malformed": "false", "review_required": "false",
            "scoring_definition": "Def2", "anchor_1": "A1_2", "anchor_5": "A5_2", "facet_normalized": "norm2",
            "facet_category": "cat2", "facet_type": "type2"
        })
        writer.writerow({
            "facet_id": "f1", "conversation_observable": "true", "is_malformed": "false", "review_required": "false",
            "scoring_definition": "Def1", "anchor_1": "A1_1", "anchor_5": "A5_1", "facet_normalized": "norm1",
            "facet_category": "cat1", "facet_type": "type1"
        })
        
    embedder = FakeDeterministicEmbedder(dim=4)
    build_index(cat_path, npz_path, meta_path, embedder)
    
    embeddings, meta = load_index(npz_path, meta_path)
    
    assert meta["num_facets"] == 2
    assert meta["vector_dimension"] == 4
    # Check stable order (sorted by facet_id)
    assert meta["facet_ids"] == ["f1", "f2"]
    
    # Check vector normalization
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, np.ones(2), rtol=1e-5)

def test_mismatch_detection(tmp_path: Path):
    cat_path = tmp_path / "cat.csv"
    npz_path = tmp_path / "emb.npz"
    meta_path = tmp_path / "meta.json"
    
    fields = ["facet_id", "conversation_observable", "is_malformed", "review_required", "scoring_definition", "anchor_1", "anchor_5"]
    with open(cat_path, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "facet_id": "f1", "conversation_observable": "true", "is_malformed": "false", "review_required": "false",
            "scoring_definition": "Def", "anchor_1": "A1", "anchor_5": "A5"
        })
        
    embedder = FakeDeterministicEmbedder(dim=4)
    build_index(cat_path, npz_path, meta_path, embedder)
    
    assert check_index_freshness(cat_path, meta_path, embedder.model_id) is True
    
    # Mismatch model
    assert check_index_freshness(cat_path, meta_path, "different_model") is False
    
    # Mismatch content
    with open(cat_path, 'a', encoding='utf-8') as f:
        f.write("\n2,true,false,false,Def2,A1_2,A5_2")
    assert check_index_freshness(cat_path, meta_path, embedder.model_id) is False
