from ahoum_assignment.models import RetrievalResult, RetrievalCandidate, RetrievalDiagnostics

def merge_retrieval_results(
    semantic_result: RetrievalResult,
    keyword_result: RetrievalResult,
    semantic_weight: float = 0.5,
    keyword_weight: float = 0.5,
    hybrid_threshold: float = 0.3,
    top_k: int = 25
) -> RetrievalResult:
    """
    Merges semantic and keyword candidates into a deterministic, ranked hybrid shortlist.
    Calculates a combined score, deduplicates overlapping facets, enforces thresholds, 
    and rigidly blocks unobservable items.
    """
    merged_cands = {}
    
    # Track paths for diagnostics and reasoning
    for c in semantic_result.candidates:
        merged_cands[c.facet_id] = {"semantic": c, "keyword": None}
        
    for c in keyword_result.candidates:
        if c.facet_id in merged_cands:
            merged_cands[c.facet_id]["keyword"] = c
        else:
            merged_cands[c.facet_id] = {"semantic": None, "keyword": c}
            
    final_candidates = []
    excluded_count = 0
    
    for fid, routes in merged_cands.items():
        sem_c = routes["semantic"]
        kw_c = routes["keyword"]
        
        sem_score = sem_c.semantic_score if sem_c and sem_c.semantic_score is not None else 0.0
        kw_score = kw_c.keyword_score if kw_c and kw_c.keyword_score is not None else 0.0
        
        hybrid_score = (semantic_weight * sem_score) + (keyword_weight * kw_score)
        
        if hybrid_score < hybrid_threshold:
            excluded_count += 1
            continue
            
        base_c = sem_c or kw_c
        
        # Final rigorous safety check (though prior layers should have already filtered)
        if base_c.conversation_observable != "true":
            excluded_count += 1
            continue
            
        matched_kws = kw_c.matched_keywords if kw_c else []
        matched_cats = kw_c.matched_categories if kw_c else []
        
        if sem_c and kw_c:
            reason = f"Retrieved via both paths. Semantic ({sem_score:.2f}) + Keyword ({kw_score:.2f})."
        elif sem_c:
            reason = f"Retrieved via semantic route only. Score ({sem_score:.2f})."
        else:
            reason = f"Retrieved via keyword route only. Score ({kw_score:.2f})."
            
        # Pydantic validation requires rank > 0 or an exclusion reason.
        # We append with dummy properties as dictionaries, then instantiate later to avoid 
        # validation ordering issues (as done in keyword_router).
        final_candidates.append({
            "facet_id": base_c.facet_id,
            "facet_raw": base_c.facet_raw,
            "facet_normalized": base_c.facet_normalized,
            "facet_category": base_c.facet_category,
            "conversation_observable": "true",
            "semantic_score": sem_c.semantic_score if sem_c else None,
            "keyword_score": kw_c.keyword_score if kw_c else None,
            "hybrid_score": hybrid_score,
            "matched_keywords": matched_kws,
            "matched_categories": matched_cats,
            "inclusion_reason": reason
        })
        
    # Sort descending by hybrid_score, break ties ascending by facet_id
    final_candidates.sort(key=lambda x: (-x["hybrid_score"], x["facet_id"]))
    
    # Cap at top_k
    if len(final_candidates) > top_k:
        excluded_count += len(final_candidates) - top_k
        final_candidates = final_candidates[:top_k]
        
    # Instantiate Pydantic models
    validated_candidates = []
    for rank, c_dict in enumerate(final_candidates, start=1):
        c_dict["rank"] = rank
        validated_candidates.append(RetrievalCandidate(**c_dict))
        
    overlap_count = sum(1 for r in merged_cands.values() if r["semantic"] and r["keyword"])
    
    # Construct diagnostics
    diag = RetrievalDiagnostics(
        semantic_candidate_count=semantic_result.candidate_count,
        keyword_candidate_count=keyword_result.candidate_count,
        merged_candidate_count=len(validated_candidates),
        excluded_non_observable_count=(
            (semantic_result.diagnostics.excluded_non_observable_count if semantic_result.diagnostics else 0) +
            (keyword_result.diagnostics.excluded_non_observable_count if keyword_result.diagnostics else 0)
        ),
        duplicate_candidate_count=overlap_count,
        fallback_behavior="none" if validated_candidates else "empty_list"
    )
    
    warnings_list = []
    if not validated_candidates:
        warnings_list.append("No candidates passed the hybrid threshold.")
        
    return RetrievalResult(
        conversation_id=semantic_result.conversation_id,
        candidate_count=len(validated_candidates),
        candidates=validated_candidates,
        excluded_count=excluded_count,
        retrieval_config_metadata={
            "semantic_weight": semantic_weight,
            "keyword_weight": keyword_weight,
            "hybrid_threshold": hybrid_threshold,
            "top_k": top_k
        },
        index_version="hybrid_v1",
        warnings=warnings_list,
        diagnostics=diag
    )
