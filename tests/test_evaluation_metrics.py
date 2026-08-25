import pytest
from ahoum_assignment.benchmark_models import ReferenceLabel, BenchmarkConversation
from ahoum_assignment.models import ScoreStatus, RetrievalResult, RetrievalCandidate
from ahoum_assignment.result_aggregator import ConversationScoringResult, FacetScore
from ahoum_assignment.evaluation.comparison import compare_label
from ahoum_assignment.evaluation.metrics import calculate_scoring_metrics, calculate_abstention_metrics

def test_compare_label_exact_match():
    label = ReferenceLabel(
        conversation_id="c1",
        facet_id="f1",
        expected_status="scored",
        expected_score_1_to_5=4,
        expected_evidence_quote="yes",
        label_rationale="test",
        label_scope="scoring_reference",
        proposed_by="agent"
    )
    result = ConversationScoringResult(
        conversation_id="c1",
        candidate_count=1,
        scored_count=1,
        insufficient_evidence_count=0,
        not_observable_count=0,
        error_count=0,
        retrieval_excluded_count=0,
        batch_count=1,
        total_latency_ms=0,
        provider="mock",
        model="mock",
        warnings=[],
        facet_scores=[
            FacetScore(
                facet_id="f1",
                facet_raw="dummy",
                facet_normalized="dummy",
                status=ScoreStatus.SCORED,
                score_1_to_5=4,
                confidence_0_to_1=0.9,
                evidence="yes",
                reason="test",
                model_metadata={}
            )
        ]
    )
    
    comp = compare_label(label, result)
    assert comp.actual_status == "scored"
    assert comp.outcome_category == "exact_match"

def test_compare_label_unsupported_score():
    label = ReferenceLabel(
        conversation_id="c1",
        facet_id="f1",
        expected_status="insufficient_evidence",
        label_rationale="test",
        label_scope="abstention_reference",
        proposed_by="agent"
    )
    result = ConversationScoringResult(
        conversation_id="c1",
        candidate_count=1,
        scored_count=1,
        insufficient_evidence_count=0,
        not_observable_count=0,
        error_count=0,
        retrieval_excluded_count=0,
        batch_count=1,
        total_latency_ms=0,
        provider="mock",
        model="mock",
        warnings=[],
        facet_scores=[
            FacetScore(
                facet_id="f1",
                facet_raw="dummy",
                facet_normalized="dummy",
                status=ScoreStatus.SCORED,
                score_1_to_5=4,
                confidence_0_to_1=0.9,
                evidence="yes",
                reason="test",
                model_metadata={}
            )
        ]
    )
    
    comp = compare_label(label, result)
    assert comp.actual_status == "scored"
    assert comp.outcome_category == "unsupported_score"

def test_metrics_aggregation():
    # Assume 1 exact match, 1 unsupported score
    label1 = ReferenceLabel(
        conversation_id="c1",
        facet_id="f1",
        expected_status="scored",
        expected_score_1_to_5=4,
        expected_evidence_quote="yes",
        label_rationale="test",
        label_scope="scoring_reference",
        proposed_by="agent"
    )
    label2 = ReferenceLabel(
        conversation_id="c1",
        facet_id="f2",
        expected_status="insufficient_evidence",
        label_rationale="test",
        label_scope="abstention_reference",
        proposed_by="agent"
    )
    
    result = ConversationScoringResult(
        conversation_id="c1",
        candidate_count=2,
        scored_count=2,
        insufficient_evidence_count=0,
        not_observable_count=0,
        error_count=0,
        retrieval_excluded_count=0,
        batch_count=1,
        total_latency_ms=0,
        provider="mock",
        model="mock",
        warnings=[],
        facet_scores=[
            FacetScore(facet_id="f1", facet_raw="dummy", facet_normalized="dummy", status=ScoreStatus.SCORED, score_1_to_5=4, confidence_0_to_1=0.9, evidence="yes", reason="test", model_metadata={}),
            FacetScore(facet_id="f2", facet_raw="dummy", facet_normalized="dummy", status=ScoreStatus.SCORED, score_1_to_5=4, confidence_0_to_1=0.9, evidence="yes", reason="test", model_metadata={})
        ]
    )
    
    comp1 = compare_label(label1, result)
    comp2 = compare_label(label2, result)
    
    s_metrics = calculate_scoring_metrics([comp1, comp2])
    assert s_metrics.exact_agreement_rate == 1.0
    
    a_metrics = calculate_abstention_metrics([comp1, comp2])
    assert a_metrics.unsupported_score_rate == 1.0
