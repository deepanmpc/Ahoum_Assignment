"""Tests for scoring prompt and response contract (D2)."""

import pytest

from ahoum_assignment.scoring_prompt import (
    ScoringResponseItem,
    ScoringBatchResponse,
    build_batch_prompt,
    build_retry_prompt,
)
from ahoum_assignment.models import RetrievalCandidate


def _make_candidate(fid: str) -> RetrievalCandidate:
    return RetrievalCandidate(
        facet_id=fid, facet_raw=f"r_{fid}", facet_normalized=f"n_{fid}",
        facet_category="cat", conversation_observable="true",
        semantic_score=0.9, hybrid_score=0.9,
        inclusion_reason="test", rank=1,
    )


def test_batch_max_five():
    cands = [_make_candidate(f"f{i}") for i in range(6)]
    with pytest.raises(ValueError, match="at most 5"):
        build_batch_prompt("text", cands)


def test_batch_empty():
    with pytest.raises(ValueError, match="at least one"):
        build_batch_prompt("text", [])


def test_prompt_contains_anchors_and_instructions():
    c = _make_candidate("f1")
    catalogue = {"f1": {
        "scoring_definition": "Measures patience",
        "anchor_1": "Very impatient",
        "anchor_3": "Somewhat patient",
        "anchor_5": "Extremely patient",
    }}
    prompt = build_batch_prompt("I waited calmly.", [c], catalogue_rows=catalogue)

    assert "f1" in prompt
    assert "Measures patience" in prompt
    assert "Very impatient" in prompt
    assert "Extremely patient" in prompt
    assert "Do not infer diagnoses" in prompt.lower() or "Do NOT infer diagnoses" in prompt
    assert "JSON ONLY" in prompt


def test_prompt_retains_facet_ids():
    cands = [_make_candidate(f"facet_{i}") for i in range(3)]
    prompt = build_batch_prompt("text", cands)
    for c in cands:
        assert c.facet_id in prompt


def test_prompt_prohibits_unsupported_inference():
    prompt = build_batch_prompt("text", [_make_candidate("f1")])
    lower = prompt.lower()
    for term in ["diagnos", "lab value", "religion", "biographical"]:
        assert term in lower


def test_response_item_scored_requires_score():
    with pytest.raises(Exception):
        ScoringResponseItem(
            facet_id="f1", status="scored", score_1_to_5=None,
            confidence_0_to_1=0.8, reason="r",
        )


def test_response_item_abstention_rejects_score():
    with pytest.raises(Exception):
        ScoringResponseItem(
            facet_id="f1", status="insufficient_evidence",
            score_1_to_5=3, confidence_0_to_1=0.5, reason="r",
        )


def test_response_item_invalid_score():
    with pytest.raises(Exception):
        ScoringResponseItem(
            facet_id="f1", status="scored", score_1_to_5=0,
            confidence_0_to_1=0.9, reason="r",
        )
    with pytest.raises(Exception):
        ScoringResponseItem(
            facet_id="f1", status="scored", score_1_to_5=6,
            confidence_0_to_1=0.9, reason="r",
        )


def test_response_item_confidence_range():
    with pytest.raises(Exception):
        ScoringResponseItem(
            facet_id="f1", status="scored", score_1_to_5=3,
            confidence_0_to_1=1.5, reason="r",
        )


def test_retry_prompt_includes_errors():
    p = build_retry_prompt("original prompt", ["missing facet f2", "bad JSON"])
    assert "missing facet f2" in p
    assert "INVALID" in p
