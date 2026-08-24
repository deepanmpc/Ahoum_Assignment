import pytest
import numpy as np
import csv
import json
from pathlib import Path

from ahoum_assignment.embeddings import Embedder
from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates, load_cached_index, load_cached_catalogue

# A controlled embedder that returns exact vectors we want for the test
class FixedFakeEmbedder(Embedder):
    def __init__(self, expected_dim: int = 4):
        self.expected_dim = expected_dim
        # Hardcoded query embedding
        self.query_emb = np.array([1.0, 0.0, 0.0, 0.0])
        
    @property
    def model_id(self) -> str:
        return "fixed-fake-embedder"
        
    @property
    def dimension(self) -> int:
        return self.expected_dim
        
    def embed(self, texts: list[str]) -> np.ndarray:
        # Just return the same query embedding for all inputs
        res = []
        for _ in texts:
            res.append(self.query_emb)
        return np.array(res, dtype=np.float32)

@pytest.fixture
def index_setup(tmp_path: Path):
    cat_path = tmp_path / "cat.csv"
    npz_path = tmp_path / "emb.npz"
    meta_path = tmp_path / "meta.json"
    
    # We create a catalogue
    with open(cat_path, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["facet_id", "facet_raw", "facet_normalized", "facet_category", "conversation_observable"])
        writer.writeheader()
        # f1 is exactly equal to query
        writer.writerow({"facet_id": "f1", "facet_raw": "r1", "facet_normalized": "n1", "facet_category": "c1", "conversation_observable": "true"})
        # f2 is orthogonal (score 0.0)
        writer.writerow({"facet_id": "f2", "facet_raw": "r2", "facet_normalized": "n2", "facet_category": "c2", "conversation_observable": "true"})
        # f3 is partially aligned (score 0.5)
        writer.writerow({"facet_id": "f3", "facet_raw": "r3", "facet_normalized": "n3", "facet_category": "c3", "conversation_observable": "true"})
        # f4 is tie with f3 (score 0.5)
        writer.writerow({"facet_id": "f4", "facet_raw": "r4", "facet_normalized": "n4", "facet_category": "c4", "conversation_observable": "true"})
        
    # We construct the normalized embeddings
    embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],  # f1, score 1.0
        [0.0, 1.0, 0.0, 0.0],  # f2, score 0.0
        [0.5, 0.866025, 0.0, 0.0],  # f3, score 0.5
        [0.5, 0.866025, 0.0, 0.0],  # f4, score 0.5
    ], dtype=np.float32)
    
    meta = {
        "model_id": "fixed-fake-embedder",
        "catalogue_hash": "hash",
        "facet_ids": ["f1", "f2", "f3", "f4"]
    }
    
    np.savez_compressed(npz_path, embeddings=embeddings)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f)
        
    # Clear the lru_cache for isolated tests
    load_cached_index.cache_clear()
    load_cached_catalogue.cache_clear()
        
    return cat_path, npz_path, meta_path
    
def test_nearest_neighbor_ranking(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    # Threshold 0.0 ensures everyone gets in except maybe < 0, but all are >= 0
    res = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=10, threshold=0.0)
    
    assert res.candidate_count == 4
    assert res.candidates[0].facet_id == "f1"
    assert res.candidates[1].facet_id == "f3"
    assert res.candidates[2].facet_id == "f4"
    assert res.candidates[3].facet_id == "f2"
    
def test_top_k_behavior(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    res = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=2, threshold=0.0)
    
    assert res.candidate_count == 2
    assert res.candidates[0].facet_id == "f1"
    assert res.candidates[1].facet_id == "f3"

def test_threshold_filtering(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    # Threshold 0.6 should only allow f1 (1.0)
    res = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=10, threshold=0.6)
    
    assert res.candidate_count == 1
    assert res.candidates[0].facet_id == "f1"

def test_tie_breaking(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    res = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=10, threshold=0.4)
    # Both f3 and f4 have score 0.5. 'f3' string < 'f4' string, so f3 is rank 2, f4 is rank 3.
    assert res.candidates[1].facet_id == "f3"
    assert res.candidates[2].facet_id == "f4"

def test_no_result_case(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    res = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=10, threshold=2.0)
    
    assert res.candidate_count == 0
    assert len(res.candidates) == 0
    assert len(res.warnings) == 1
    assert "No semantic candidates cleared the threshold" in res.warnings[0]
    assert res.diagnostics.fallback_behavior == "empty_list"

def test_same_input_producing_same_result(index_setup):
    cat_path, npz_path, meta_path = index_setup
    embedder = FixedFakeEmbedder()
    
    res1 = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=2, threshold=0.0, conversation_id="conv-1")
    res2 = retrieve_semantic_candidates("Query", embedder, npz_path, meta_path, cat_path, top_k=2, threshold=0.0, conversation_id="conv-1")
    
    assert res1.model_dump() == res2.model_dump()

def test_missing_index_error(tmp_path: Path):
    embedder = FixedFakeEmbedder()
    with pytest.raises(FileNotFoundError, match="Missing semantic index files"):
        retrieve_semantic_candidates("Query", embedder, tmp_path / "bad.npz", tmp_path / "bad.json", tmp_path / "bad.csv")
