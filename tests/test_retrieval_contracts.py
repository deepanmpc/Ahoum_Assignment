import pytest
from ahoum_assignment.models import (
    RetrievalCandidate, 
    RetrievalResult, 
    ConversationInput,
    RetrievalDiagnostics
)

def test_conversation_input():
    ci = ConversationInput(conversation_id="c1", text="Hello world")
    assert ci.language_hint is None
    assert ci.metadata == {}

def test_candidate_must_be_observable_if_ranked():
    with pytest.raises(ValueError, match="not marked conversation_observable=true"):
        RetrievalCandidate(
            facet_id="f1",
            facet_raw="raw",
            facet_normalized="norm",
            facet_category="cat",
            conversation_observable="false",
            hybrid_score=0.9,
            semantic_score=0.9,
            inclusion_reason="High semantic match",
            rank=1
        )

def test_candidate_must_have_inclusion_signal():
    with pytest.raises(ValueError, match="least one inclusion signal"):
        RetrievalCandidate(
            facet_id="f1",
            facet_raw="raw",
            facet_normalized="norm",
            facet_category="cat",
            conversation_observable="true",
            hybrid_score=0.0,
            inclusion_reason="Because",
            rank=1
        )

def test_candidate_must_have_reasons():
    with pytest.raises(ValueError, match="must have an inclusion_reason"):
        RetrievalCandidate(
            facet_id="f1",
            facet_raw="raw",
            facet_normalized="norm",
            facet_category="cat",
            conversation_observable="true",
            hybrid_score=0.9,
            semantic_score=0.9,
            rank=1
        )
        
    with pytest.raises(ValueError, match="must have an exclusion_reason"):
        RetrievalCandidate(
            facet_id="f2",
            facet_raw="raw",
            facet_normalized="norm",
            facet_category="cat",
            conversation_observable="false",
            hybrid_score=0.0,
            rank=0
        )

def test_result_rejects_duplicates():
    c1 = RetrievalCandidate(
        facet_id="f1", facet_raw="r1", facet_normalized="n1", facet_category="c1",
        conversation_observable="true", hybrid_score=0.9, semantic_score=0.9, 
        inclusion_reason="Match", rank=1
    )
    with pytest.raises(ValueError, match="duplicate facet ID"):
        RetrievalResult(
            conversation_id="conv1",
            candidate_count=2,
            candidates=[c1, c1],
            excluded_count=0,
            index_version="v1"
        )

def test_result_rejects_non_observable_and_invalid_ranks():
    # Invalid rank in result
    c_unranked = RetrievalCandidate(
        facet_id="f1", facet_raw="r1", facet_normalized="n1", facet_category="c1",
        conversation_observable="true", hybrid_score=0.9, semantic_score=0.9, 
        exclusion_reason="Not ranked", rank=0
    )
    with pytest.raises(ValueError, match="has rank < 1"):
        RetrievalResult(
            conversation_id="conv1",
            candidate_count=1,
            candidates=[c_unranked],
            excluded_count=0,
            index_version="v1"
        )

def test_valid_result_succeeds():
    c1 = RetrievalCandidate(
        facet_id="f1", facet_raw="r1", facet_normalized="n1", facet_category="c1",
        conversation_observable="true", hybrid_score=0.9, semantic_score=0.9, 
        inclusion_reason="Match", rank=1
    )
    res = RetrievalResult(
        conversation_id="conv1",
        candidate_count=1,
        candidates=[c1],
        excluded_count=0,
        index_version="v1",
        diagnostics=RetrievalDiagnostics(semantic_candidate_count=1)
    )
    assert res.candidates[0].facet_id == "f1"
    assert res.diagnostics.semantic_candidate_count == 1
