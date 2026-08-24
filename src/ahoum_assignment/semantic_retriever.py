import csv
import json
import uuid
import numpy as np
from pathlib import Path
from functools import lru_cache
from typing import Dict

from ahoum_assignment.models import (
    RetrievalCandidate, 
    RetrievalResult, 
    RetrievalDiagnostics
)
from ahoum_assignment.semantic_index import load_index
from ahoum_assignment.embeddings import Embedder


@lru_cache(maxsize=1)
def load_cached_index(npz_path: Path, meta_path: Path):
    """Lightweight in-memory caching for the loaded semantic index."""
    return load_index(npz_path, meta_path)


@lru_cache(maxsize=1)
def load_cached_catalogue(csv_path: Path) -> Dict[str, dict]:
    """Lightweight in-memory caching for the processed catalogue."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Catalogue not found at {csv_path}")
    cat = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat[row['facet_id']] = row
    return cat


def retrieve_semantic_candidates(
    text: str,
    embedder: Embedder,
    npz_path: Path,
    meta_path: Path,
    catalogue_path: Path,
    top_k: int = 20,
    threshold: float = 0.5,
    conversation_id: str = None
) -> RetrievalResult:
    """
    Perform runtime semantic retrieval against the offline index using cosine similarity.
    Conversation text is kept entirely within local memory boundaries.
    """
    if not npz_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Missing semantic index files. Run build_index.py first.")
        
    embeddings, meta = load_cached_index(npz_path, meta_path)
    catalogue = load_cached_catalogue(catalogue_path)
    
    # 1. Embed complete conversation exactly once per request
    q_emb = embedder.embed([text])[0]
    
    # L2 normalize the query to use dot product for cosine similarity
    q_norm = np.linalg.norm(q_emb)
    if q_norm == 0:
        q_emb_norm = q_emb
    else:
        q_emb_norm = q_emb / q_norm
        
    # 2. Compute cosine similarity against indexed facet vectors
    scores = np.dot(embeddings, q_emb_norm)
    
    # 3. Filter by semantic threshold and rank
    facet_ids = meta["facet_ids"]
    candidates_raw = []
    
    for i, score in enumerate(scores):
        if score >= threshold:
            candidates_raw.append((float(score), facet_ids[i]))
            
    # Sort descending by score. Tie-break ascending by facet_id for stability
    candidates_raw.sort(key=lambda x: (-x[0], x[1]))
    
    top_raw = candidates_raw[:top_k]
    
    warnings_list = []
    if not top_raw:
        # Do not fabricate a weak candidate if nothing clears threshold
        warnings_list.append(f"No semantic candidates cleared the threshold of {threshold}.")
        
    candidates = []
    for rank, (score, fid) in enumerate(top_raw, start=1):
        row = catalogue[fid]
        cand = RetrievalCandidate(
            facet_id=fid,
            facet_raw=row['facet_raw'],
            facet_normalized=row['facet_normalized'],
            facet_category=row['facet_category'],
            conversation_observable="true",
            semantic_score=score,
            hybrid_score=score,  # Falls back purely to semantic score here
            inclusion_reason=f"Semantic similarity score: {score:.4f} >= {threshold}",
            rank=rank
        )
        candidates.append(cand)
        
    diag = RetrievalDiagnostics(
        semantic_candidate_count=len(candidates),
        merged_candidate_count=len(candidates),
        excluded_non_observable_count=0, # The index naturally excludes non-observables
        fallback_behavior="none" if candidates else "empty_list"
    )
    
    res = RetrievalResult(
        conversation_id=conversation_id or str(uuid.uuid4()),
        candidate_count=len(candidates),
        candidates=candidates,
        excluded_count=len(scores) - len(candidates),
        retrieval_config_metadata={
            "top_k": top_k, 
            "threshold": threshold,
            "embedder_id": embedder.model_id
        },
        index_version=meta.get("catalogue_hash", "unknown"),
        warnings=warnings_list,
        diagnostics=diag
    )
    return res
