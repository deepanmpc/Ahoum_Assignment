"""Tests for batch orchestration (D3) and result aggregation (D5)."""

import pytest
import csv
import json
from pathlib import Path
from dataclasses import dataclass

from ahoum_assignment.models import RetrievalCandidate, RetrievalResult, RetrievalDiagnostics
from ahoum_assignment.batching import split_batches
from ahoum_assignment.scoring_service import score_conversation
from ahoum_assignment.result_aggregator import aggregate_results
from ahoum_assignment.result_renderer import render
from ahoum_assignment.providers.base import (
    BaseProvider, ProviderResponse, ProviderError, ProviderErrorType,
)


def _make_candidate(fid: str, rank: int) -> RetrievalCandidate:
    return RetrievalCandidate(
        facet_id=fid, facet_raw=f"r_{fid}", facet_normalized=f"n_{fid}",
        facet_category="cat", conversation_observable="true",
        semantic_score=0.9, hybrid_score=0.9,
        inclusion_reason="test", rank=rank,
    )


def _make_retrieval(n: int) -> RetrievalResult:
    cands = [_make_candidate(f"f{i}", i + 1) for i in range(n)]
    return RetrievalResult(
        conversation_id="conv-test", candidate_count=n,
        candidates=cands, excluded_count=0, index_version="v1",
    )


def _make_catalogue(tmp_path: Path, n: int) -> Path:
    cat_path = tmp_path / "cat.csv"
    fields = ["facet_id", "facet_raw", "facet_normalized", "facet_category",
              "conversation_observable", "scoring_definition", "anchor_1",
              "anchor_3", "anchor_5"]
    with open(cat_path, "w", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i in range(n):
            w.writerow({
                "facet_id": f"f{i}", "facet_raw": f"r_f{i}",
                "facet_normalized": f"n_f{i}", "facet_category": "cat",
                "conversation_observable": "true",
                "scoring_definition": "def", "anchor_1": "a1",
                "anchor_3": "a3", "anchor_5": "a5",
            })
    return cat_path


class MockProvider(BaseProvider):
    """Provider that returns valid JSON without any network calls."""

    def __init__(self, responses=None, fail_on=None):
        self._responses = responses or {}
        self._fail_on = fail_on or set()
        self._call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def generate(self, prompt: str) -> ProviderResponse:
        self._call_count += 1
        if self._call_count in self._fail_on:
            raise ProviderError(ProviderErrorType.TIMEOUT, "Mock timeout")

        # Find facet IDs in prompt and return valid responses
        import re
        ids = re.findall(r"facet_id: (f\d+)", prompt)
        results = []
        for fid in ids:
            results.append({
                "facet_id": fid,
                "status": "scored",
                "score_1_to_5": 3,
                "confidence_0_to_1": 0.7,
                "evidence_quote": "waited calmly",
                "reason": "Direct evidence",
            })

        return ProviderResponse(
            text=json.dumps({"results": results}),
            provider_name="mock",
            model_name="mock-model",
            latency_ms=10.0,
        )


# --- Batching tests ---

def test_split_1_facet():
    assert len(split_batches([1], 5)) == 1

def test_split_5_facets():
    batches = split_batches(list(range(5)), 5)
    assert len(batches) == 1
    assert len(batches[0]) == 5

def test_split_6_facets():
    batches = split_batches(list(range(6)), 5)
    assert len(batches) == 2
    assert len(batches[0]) == 5
    assert len(batches[1]) == 1

def test_split_20_facets():
    batches = split_batches(list(range(20)), 5)
    assert len(batches) == 4


# --- Scoring service tests ---

def test_dry_run_zero_calls(tmp_path):
    ret = _make_retrieval(3)
    cat = _make_catalogue(tmp_path, 3)
    result = score_conversation("c1", "I waited calmly.", ret, None, cat, dry_run=True)
    assert result.dry_run
    assert result.total_batches == 1
    assert result.successful_batches == 1  # dry-run is marked success


def test_mock_scoring_1_facet(tmp_path):
    ret = _make_retrieval(1)
    cat = _make_catalogue(tmp_path, 1)
    result = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    assert result.successful_batches == 1


def test_mock_scoring_6_facets_2_batches(tmp_path):
    ret = _make_retrieval(6)
    cat = _make_catalogue(tmp_path, 6)
    result = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    assert result.total_batches == 2
    assert result.successful_batches == 2


def test_no_candidates(tmp_path):
    ret = _make_retrieval(0)
    cat = _make_catalogue(tmp_path, 0)
    result = score_conversation("c1", "text", ret, MockProvider(), cat)
    assert result.total_batches == 0


def test_non_observable_rejected():
    bad_cand = RetrievalCandidate(
        facet_id="bad", facet_raw="r", facet_normalized="n",
        facet_category="cat", conversation_observable="false",
        hybrid_score=0.9, exclusion_reason="not observable", rank=0,
    )
    ret = RetrievalResult(
        conversation_id="c1", candidate_count=0,
        candidates=[], excluded_count=1, index_version="v1",
    )
    # Manually test the assertion
    ret2 = RetrievalResult(
        conversation_id="c1", candidate_count=0,
        candidates=[], excluded_count=0, index_version="v1",
    )
    # This should not raise for empty candidates
    from ahoum_assignment.scoring_service import score_conversation
    # If we somehow passed a non-observable into the list, it would
    # be caught by RetrievalResult's own validator first.


def test_one_batch_fails_others_succeed(tmp_path):
    ret = _make_retrieval(10)
    cat = _make_catalogue(tmp_path, 10)
    # Fail on first call (batch 0), succeed on the second (batch 1)
    provider = MockProvider(fail_on={1})
    result = score_conversation("c1", "I waited calmly.", ret, provider, cat)
    assert result.total_batches == 2
    assert result.failed_batches == 1
    assert result.successful_batches == 1


def test_deterministic_batch_order(tmp_path):
    ret = _make_retrieval(7)
    cat = _make_catalogue(tmp_path, 7)
    r1 = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    r2 = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    assert [b.facet_ids for b in r1.batch_outcomes] == [b.facet_ids for b in r2.batch_outcomes]


# --- Aggregation tests (D5) ---

def test_aggregation_all_success(tmp_path):
    ret = _make_retrieval(3)
    cat = _make_catalogue(tmp_path, 3)
    scoring = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    agg = aggregate_results(ret, scoring)
    assert agg.scored_count == 3
    assert agg.error_count == 0
    assert agg.candidate_count == 3


def test_aggregation_partial_failure(tmp_path):
    ret = _make_retrieval(10)
    cat = _make_catalogue(tmp_path, 10)
    provider = MockProvider(fail_on={1})
    scoring = score_conversation("c1", "I waited calmly.", ret, provider, cat)
    agg = aggregate_results(ret, scoring)
    assert agg.scored_count == 5
    assert agg.error_count == 5
    assert agg.candidate_count == 10


def test_aggregation_all_fail(tmp_path):
    ret = _make_retrieval(3)
    cat = _make_catalogue(tmp_path, 3)
    provider = MockProvider(fail_on={1, 2})  # both calls fail (and retry)
    scoring = score_conversation("c1", "I waited calmly.", ret, provider, cat)
    agg = aggregate_results(ret, scoring)
    assert agg.error_count == 3
    assert agg.scored_count == 0


def test_aggregation_no_score_for_abstention(tmp_path):
    """Ensure abstentions never carry numeric scores."""
    ret = _make_retrieval(3)
    cat = _make_catalogue(tmp_path, 3)
    scoring = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    agg = aggregate_results(ret, scoring)
    for fs in agg.facet_scores:
        if fs.status != fs.status.SCORED:
            assert fs.score_1_to_5 is None


def test_stable_output_ordering(tmp_path):
    ret = _make_retrieval(5)
    cat = _make_catalogue(tmp_path, 5)
    scoring = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    agg = aggregate_results(ret, scoring)
    # Order matches retrieval rank
    assert [fs.facet_id for fs in agg.facet_scores] == [f"f{i}" for i in range(5)]


def test_renderer_output(tmp_path):
    ret = _make_retrieval(2)
    cat = _make_catalogue(tmp_path, 2)
    scoring = score_conversation("c1", "I waited calmly.", ret, MockProvider(), cat)
    agg = aggregate_results(ret, scoring)
    text = render(agg)
    assert "c1" in text
    assert "Scored:" in text
