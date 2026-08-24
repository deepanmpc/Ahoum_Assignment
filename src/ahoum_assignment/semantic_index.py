import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np

from ahoum_assignment.embeddings import Embedder


def is_eligible(row: dict) -> bool:
    """Check if a facet is fully eligible for the scoring index."""
    if row.get("conversation_observable") != "true":
        return False
    if row.get("is_malformed") == "true":
        return False
    # If it's strictly flagged as requiring human review over scoring
    if row.get("review_required") == "true":
        return False
    if not row.get("scoring_definition") or not row.get("anchor_1") or not row.get("anchor_5"):
        return False
    return True


def build_semantic_document(row: dict) -> str:
    """Construct a dense semantic document from a single facet record."""
    parts = [
        f"Facet: {row.get('facet_normalized', '')}",
        f"Category: {row.get('facet_category', '')}",
        f"Type: {row.get('facet_type', '')}",
        f"Definition: {row.get('scoring_definition', '')}",
        f"Low Evidence: {row.get('anchor_1', '')}",
        f"Moderate Evidence: {row.get('anchor_3', '')}",
        f"Strong Evidence: {row.get('anchor_5', '')}"
    ]
    return "\n".join(parts)


def compute_catalogue_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def build_index(catalogue_path: Path, npz_path: Path, meta_path: Path, embedder: Embedder) -> None:
    if not catalogue_path.exists():
        raise FileNotFoundError(f"Catalogue not found at {catalogue_path}")
        
    cat_hash = compute_catalogue_hash(catalogue_path)
    
    with open(catalogue_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        
    eligible = [r for r in reader if is_eligible(r)]
    if not eligible:
        raise ValueError("Catalogue contains no valid observable facets for indexing.")
        
    # Ensure stable ordering
    eligible.sort(key=lambda x: x['facet_id'])
    
    ids = []
    docs = []
    for r in eligible:
        ids.append(r['facet_id'])
        docs.append(build_semantic_document(r))
        
    # Generate embeddings
    raw_embeddings = embedder.embed(docs)
    
    # L2 Normalize for cosine similarity via dot product
    norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10  # Avoid division by zero
    normalized_embeddings = raw_embeddings / norms
    
    preprocessing_version = eligible[0].get("preprocessing_version", "unknown") if eligible else "unknown"
    
    metadata = {
        "model_id": embedder.model_id,
        "catalogue_preprocessing_version": preprocessing_version,
        "creation_time": datetime.now(timezone.utc).isoformat(),
        "catalogue_hash": cat_hash,
        "vector_dimension": embedder.dimension,
        "num_facets": len(eligible),
        "facet_ids": ids,
        "facet_texts": docs
    }
    
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save outputs
    np.savez_compressed(npz_path, embeddings=normalized_embeddings)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


def load_index(npz_path: Path, meta_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load the normalized embeddings array and the JSON metadata."""
    if not npz_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Index files not found. Please run the build script.")
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        
    data = np.load(npz_path)
    embeddings = data['embeddings']
    return embeddings, meta


def check_index_freshness(catalogue_path: Path, meta_path: Path, model_id: str) -> bool:
    """Check if the index needs to be rebuilt based on catalogue hash and model ID."""
    if not meta_path.exists():
        return False
        
    cat_hash = compute_catalogue_hash(catalogue_path)
    with open(meta_path, 'r', encoding='utf-8') as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError:
            return False
            
    if meta.get("catalogue_hash") != cat_hash:
        return False
    if meta.get("model_id") != model_id:
        return False
        
    return True
