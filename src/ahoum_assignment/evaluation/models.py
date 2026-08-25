from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class RetrievalMetrics(BaseModel):
    recall_at_5: Optional[float]
    recall_at_10: Optional[float]
    recall_at_20: Optional[float]
    category_recall: Optional[float]
    avg_shortlist_size: float
    unsafe_exclusion_rate: Optional[float]
    no_candidate_rate: Optional[float]
    missed_expected_facets: List[str]
    irrelevant_unsafe_facets_retrieved: List[str]

class ScoringMetrics(BaseModel):
    exact_agreement_rate: Optional[float]
    within_one_agreement_rate: Optional[float]
    mean_absolute_error: Optional[float]
    excluded_label_count: int
    # counts
    total_comparisons: int
    exact_matches: int
    within_one_matches: int

class AbstentionMetrics(BaseModel):
    unsupported_score_rate: Optional[float]
    over_abstention_rate: Optional[float]
    hallucination_bait_pass_rate: Optional[float]
    unsupported_scores: int
    over_abstentions: int
    total_bait_cases: int
    passed_bait_cases: int

class ReliabilityMetrics(BaseModel):
    parser_failure_rate: Optional[float]
    corrective_retry_rate: Optional[float]
    batch_failure_rate: Optional[float]
    partial_result_survival_rate: Optional[float]
    avg_batches_per_conv: float
    avg_latency_ms: float

class EvaluationResult(BaseModel):
    run_id: str
    timestamp: str
    commit_hash: Optional[str]
    config_snapshot: Dict[str, Any]
    retrieval_mode: str
    provider: str
    label_policy: str
    benchmark_version: str
    
    total_conversations: int
    total_labels_evaluated: int
    
    retrieval: RetrievalMetrics
    scoring: ScoringMetrics
    abstention: AbstentionMetrics
    reliability: ReliabilityMetrics

class LabelComparison(BaseModel):
    conversation_id: str
    facet_id: str
    expected_status: str
    actual_status: str
    expected_score: Optional[int]
    actual_score: Optional[int]
    is_hallucination_bait: bool
    outcome_category: str  # e.g., "exact_match", "within_one", "unsupported_score", "over_abstention", "retrieval_miss", "error"
