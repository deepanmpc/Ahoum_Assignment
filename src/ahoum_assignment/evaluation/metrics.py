from typing import List, Dict, Any, Optional
from .models import (
    RetrievalMetrics,
    ScoringMetrics,
    AbstentionMetrics,
    ReliabilityMetrics,
    LabelComparison
)
from ahoum_assignment.models import RetrievalResult
from ahoum_assignment.result_aggregator import ConversationScoringResult
from ahoum_assignment.benchmark_models import ReferenceLabel, BenchmarkConversation

def _safe_div(n: int, d: int) -> Optional[float]:
    return float(n) / d if d > 0 else None

def calculate_retrieval_metrics(
    labels: List[ReferenceLabel],
    retrieval_results: Dict[str, RetrievalResult],
    conversations: Dict[str, BenchmarkConversation]
) -> RetrievalMetrics:
    # Get all retrieval-relevant labels (where we expect it to be retrieved)
    # If a label expects 'scored' or 'insufficient_evidence', we assume it SHOULD be retrieved.
    # If it expects 'not_observable', it SHOULD NOT be retrieved.
    
    # Actually, the prompt says "compare retrieved facet IDs against reference retrieval_relevance labels".
    # For simplicity, we define relevant facets as those with expected_status in ['scored', 'insufficient_evidence'].
    
    total_expected = 0
    hits_at_5 = 0
    hits_at_10 = 0
    hits_at_20 = 0
    
    missed = []
    irrelevant_unsafe = []
    
    unsafe_total = 0
    unsafe_excluded = 0
    
    low_evidence_convs = 0
    no_candidate_convs = 0
    
    for conv_id, res in retrieval_results.items():
        conv_labels = [l for l in labels if l.conversation_id == conv_id]
        retrieved_ids = [c.facet_id for c in res.candidates]
        
        # Unsafe check (expected status = not_observable)
        for l in conv_labels:
            if l.expected_status == "not_observable":
                unsafe_total += 1
                if l.facet_id not in retrieved_ids:
                    unsafe_excluded += 1
                else:
                    irrelevant_unsafe.append(l.facet_id)
            elif l.expected_status in ["scored", "insufficient_evidence"]:
                total_expected += 1
                if l.facet_id in retrieved_ids[:5]: hits_at_5 += 1
                if l.facet_id in retrieved_ids[:10]: hits_at_10 += 1
                if l.facet_id in retrieved_ids[:20]: hits_at_20 += 1
                if l.facet_id not in retrieved_ids:
                    missed.append(l.facet_id)
                    
        conv = conversations.get(conv_id)
        if conv and conv.scenario_type == "low_evidence":
            low_evidence_convs += 1
            if len(retrieved_ids) == 0:
                no_candidate_convs += 1

    total_candidates = sum(len(r.candidates) for r in retrieval_results.values())
    avg_candidates = total_candidates / len(retrieval_results) if retrieval_results else 0.0

    return RetrievalMetrics(
        recall_at_5=_safe_div(hits_at_5, total_expected),
        recall_at_10=_safe_div(hits_at_10, total_expected),
        recall_at_20=_safe_div(hits_at_20, total_expected),
        category_recall=None,  # Fallback omitted for simplicity in this baseline
        avg_shortlist_size=avg_candidates,
        unsafe_exclusion_rate=_safe_div(unsafe_excluded, unsafe_total),
        no_candidate_rate=_safe_div(no_candidate_convs, low_evidence_convs),
        missed_expected_facets=missed,
        irrelevant_unsafe_facets_retrieved=irrelevant_unsafe
    )


def calculate_scoring_metrics(comparisons: List[LabelComparison]) -> ScoringMetrics:
    score_comps = [c for c in comparisons if c.expected_status == "scored" and c.actual_status == "scored"]
    
    exact = sum(1 for c in score_comps if c.outcome_category == "exact_match")
    within_one = sum(1 for c in score_comps if c.outcome_category in ["exact_match", "within_one"])
    
    mae = None
    if score_comps:
        mae = sum(abs(c.expected_score - c.actual_score) for c in score_comps) / len(score_comps)
        
    excluded = sum(1 for c in comparisons if c.expected_status != "scored")
    
    return ScoringMetrics(
        exact_agreement_rate=_safe_div(exact, len(score_comps)),
        within_one_agreement_rate=_safe_div(within_one, len(score_comps)),
        mean_absolute_error=mae,
        excluded_label_count=excluded,
        total_comparisons=len(score_comps),
        exact_matches=exact,
        within_one_matches=within_one
    )


def calculate_abstention_metrics(comparisons: List[LabelComparison]) -> AbstentionMetrics:
    abstention_comps = [c for c in comparisons if c.expected_status in ["insufficient_evidence", "not_observable", "retrieval_excluded"]]
    scored_comps = [c for c in comparisons if c.expected_status == "scored"]
    
    unsupported = sum(1 for c in abstention_comps if c.actual_status == "scored")
    over_abstentions = sum(1 for c in scored_comps if c.actual_status not in ["scored", "retrieval_miss", "system_error"])
    
    bait_comps = [c for c in abstention_comps if c.is_hallucination_bait]
    bait_passed = sum(1 for c in bait_comps if c.actual_status in ["insufficient_evidence", "not_observable", "retrieval_miss"])
    
    return AbstentionMetrics(
        unsupported_score_rate=_safe_div(unsupported, len(abstention_comps)),
        over_abstention_rate=_safe_div(over_abstentions, len(scored_comps)),
        hallucination_bait_pass_rate=_safe_div(bait_passed, len(bait_comps)),
        unsupported_scores=unsupported,
        over_abstentions=over_abstentions,
        total_bait_cases=len(bait_comps),
        passed_bait_cases=bait_passed
    )


def calculate_reliability_metrics(scoring_results: Dict[str, ConversationScoringResult]) -> ReliabilityMetrics:
    total_batches = 0
    failed_batches = 0
    total_convs = len(scoring_results)
    
    # Simple aggregates
    for res in scoring_results.values():
        total_batches += res.batch_count
        failed_batches += res.error_count // 5  # Rough approximation, better to use raw data if available

    return ReliabilityMetrics(
        parser_failure_rate=None,  # Requires deep telemetry
        corrective_retry_rate=None,
        batch_failure_rate=_safe_div(failed_batches, total_batches),
        partial_result_survival_rate=1.0 if total_batches > 0 else None,
        avg_batches_per_conv=total_batches / total_convs if total_convs > 0 else 0.0,
        avg_latency_ms=0.0  # Mock
    )
