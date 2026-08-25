import pytest
import json
from ahoum_assignment.providers.base import BaseProvider, ProviderResponse, ProviderError
from ahoum_assignment.scoring_service import score_conversation
from ahoum_assignment.models import RetrievalResult, RetrievalCandidate, ScoreStatus

class FaultyMockProvider(BaseProvider):
    def __init__(self, failure_mode: str):
        self.failure_mode = failure_mode
        self.call_count = 0

    @property
    def provider_name(self) -> str: return "faulty-mock"
    @property
    def model_name(self) -> str: return "faulty-eval"

    def generate(self, prompt: str) -> ProviderResponse:
        self.call_count += 1
        
        if self.failure_mode == "timeout":
            raise ProviderError("Connection timed out", self.provider_name)
            
        if self.failure_mode == "malformed_json_survives_retry":
            if self.call_count == 1:
                return ProviderResponse(text="{ bad json", provider_name=self.provider_name, model_name=self.model_name, latency_ms=10)
            else:
                return self._good_response(prompt)
                
        if self.failure_mode == "missing_facet":
            # Return an empty list, missing everything
            return ProviderResponse(text='{"results": []}', provider_name=self.provider_name, model_name=self.model_name, latency_ms=10)

        return self._good_response(prompt)
        
    def _good_response(self, prompt: str) -> ProviderResponse:
        import re
        ids = re.findall(r"facet_id: (\S+)", prompt)
        results = [{
            "facet_id": fid,
            "status": "scored",
            "score_1_to_5": 3,
            "confidence_0_to_1": 0.9,
            "evidence_quote": "yes",
            "reason": "good reason"
        } for fid in ids]
        return ProviderResponse(
            text=json.dumps({"results": results}),
            provider_name=self.provider_name,
            model_name=self.model_name,
            latency_ms=10.0
        )

def get_dummy_retrieval() -> RetrievalResult:
    return RetrievalResult.model_construct(
        conversation_id="c1",
        candidate_count=1,
        candidates=[
            RetrievalCandidate(
                facet_id="f1", facet_raw="f1", facet_normalized="f1", facet_category="cat",
                conversation_observable="true", facet_type="conversational_trait", sensitivity="normal",
                scoring_definition="test def", anchor_1="", anchor_3="", anchor_5="", abstention_reason="",
                semantic_score=1.0, keyword_score=1.0, hybrid_score=1.0, inclusion_reason="test",
                rank=1, exclusion_reason=""
            )
        ],
        excluded_count=0,
        diagnostics=None,
        index_version="mock"
    )

def create_mock_catalogue(tmp_path) -> str:
    cat_path = tmp_path / "cat.csv"
    with open(cat_path, "w") as f:
        f.write("facet_id,facet_raw,facet_normalized,facet_category,facet_type,conversation_observable,sensitivity,scoring_definition,anchor_1,anchor_3,anchor_5,abstention_reason\n")
        f.write("f1,f1,f1,cat,conversational_trait,true,normal,def,a1,a3,a5,\n")
    return str(cat_path)

from ahoum_assignment.result_aggregator import aggregate_results

def test_timeout_yields_error_status(tmp_path):
    provider = FaultyMockProvider("timeout")
    ret = get_dummy_retrieval()
    cat_path = create_mock_catalogue(tmp_path)
    
    res = score_conversation("c1", "test text with yes", ret, provider, cat_path, 5, False)
    agg = aggregate_results(ret, res)
    scores = agg.facet_scores
    assert len(scores) == 1
    assert scores[0].status == ScoreStatus.ERROR
    assert "Provider error" in scores[0].reason
    assert provider.call_count == 1 # Network errors fail immediately without retry

def test_malformed_json_survives_retry(tmp_path):
    provider = FaultyMockProvider("malformed_json_survives_retry")
    ret = get_dummy_retrieval()
    cat_path = create_mock_catalogue(tmp_path)
    
    res = score_conversation("c1", "test text with yes", ret, provider, cat_path, 5, False)
    agg = aggregate_results(ret, res)
    scores = agg.facet_scores
    assert len(scores) == 1
    assert scores[0].status == ScoreStatus.SCORED
    assert scores[0].score_1_to_5 == 3
    assert provider.call_count == 2 # failed first, succeeded second

def test_missing_facet_yields_error_status(tmp_path):
    provider = FaultyMockProvider("missing_facet")
    ret = get_dummy_retrieval()
    cat_path = create_mock_catalogue(tmp_path)
    
    res = score_conversation("c1", "test text with yes", ret, provider, cat_path, 5, False)
    agg = aggregate_results(ret, res)
    scores = agg.facet_scores
    assert len(scores) == 1
    assert scores[0].status == ScoreStatus.ERROR
    assert "Missing facet IDs" in scores[0].reason
