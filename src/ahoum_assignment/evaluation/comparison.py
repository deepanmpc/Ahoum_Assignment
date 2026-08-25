from typing import List, Dict, Optional
from ahoum_assignment.benchmark_models import ReferenceLabel, BenchmarkConversation
from ahoum_assignment.models import RetrievalResult
from ahoum_assignment.result_aggregator import ConversationScoringResult
from .models import LabelComparison

def compare_label(
    label: ReferenceLabel,
    scoring_result: ConversationScoringResult,
    is_bait: bool = False
) -> LabelComparison:
    """Compare a single reference label against the final scoring result."""
    # Find the corresponding facet in the scoring result
    facet_result = None
    for fs in scoring_result.facet_scores:
        if fs.facet_id == label.facet_id:
            facet_result = fs
            break
            
    if not facet_result:
        # It was never scored, likely excluded during retrieval
        return LabelComparison(
            conversation_id=label.conversation_id,
            facet_id=label.facet_id,
            expected_status=label.expected_status,
            actual_status="retrieval_miss",
            expected_score=label.expected_score_1_to_5,
            actual_score=None,
            is_hallucination_bait=is_bait,
            outcome_category="retrieval_miss"
        )
        
    actual_status = facet_result.status.value
    actual_score = facet_result.score_1_to_5
    
    # Error status
    if actual_status == "error":
        outcome = "system_error"
    # Abstention check
    elif label.expected_status in ["insufficient_evidence", "not_observable", "retrieval_excluded"]:
        if actual_status == "scored":
            outcome = "unsupported_score"
        else:
            outcome = "correct_abstention"
    # Scored check
    elif label.expected_status == "scored":
        if actual_status != "scored":
            outcome = "over_abstention"
        else:
            diff = abs((label.expected_score_1_to_5 or 0) - (actual_score or 0))
            if diff == 0:
                outcome = "exact_match"
            elif diff <= 1:
                outcome = "within_one"
            else:
                outcome = "score_mismatch"
    else:
        outcome = "unknown"
        
    return LabelComparison(
        conversation_id=label.conversation_id,
        facet_id=label.facet_id,
        expected_status=label.expected_status,
        actual_status=actual_status,
        expected_score=label.expected_score_1_to_5,
        actual_score=actual_score,
        is_hallucination_bait=is_bait,
        outcome_category=outcome
    )
