import pytest
from pydantic import ValidationError
from ahoum_assignment.benchmark_models import BenchmarkConversation, ReferenceLabel

def test_benchmark_conversation_valid():
    conv = BenchmarkConversation(
        conversation_id="test-1",
        title="Test",
        text="Hello world",
        scenario_type="clear_evidence",
        language="en",
        risk_tags=[],
        notes="A test",
        expected_retrieval_categories=["communication"]
    )
    assert conv.author_status == "proposed"

def test_reference_label_scored_valid():
    label = ReferenceLabel(
        conversation_id="test-1",
        facet_id="f-1",
        expected_status="scored",
        expected_score_1_to_5=4,
        expected_evidence_quote="Hello",
        label_rationale="Said hello",
        label_scope="scoring_reference"
    )
    assert label.expected_score_1_to_5 == 4

def test_reference_label_scored_missing_evidence():
    with pytest.raises(ValidationError):
        ReferenceLabel(
            conversation_id="test-1",
            facet_id="f-1",
            expected_status="scored",
            expected_score_1_to_5=4,
            label_rationale="Said hello",
            label_scope="scoring_reference"
        )

def test_reference_label_abstention_with_score_fails():
    with pytest.raises(ValidationError):
        ReferenceLabel(
            conversation_id="test-1",
            facet_id="f-1",
            expected_status="insufficient_evidence",
            expected_score_1_to_5=3,
            label_rationale="Not enough",
            label_scope="abstention_reference"
        )

import json
from pathlib import Path

def test_benchmark_conversations_file_valid():
    conv_file = Path("data/examples/benchmark_conversations.jsonl")
    assert conv_file.exists()
    
    with open(conv_file, "r") as f:
        lines = f.readlines()
        
    assert len(lines) >= 12
    
    conversations = [BenchmarkConversation.model_validate_json(line) for line in lines]
    ids = {c.conversation_id for c in conversations}
    assert len(ids) >= 12  # At least 12 unique IDs
    
    scenarios = {c.scenario_type for c in conversations}
    required_scenarios = {
        "clear_evidence", "ambiguous_evidence", "contradictory_evidence",
        "quoted_speech", "sarcasm", "code_switched", "low_evidence",
        "financial_risk", "communication_work_habit",
        "hallucination_bait_medical", "hallucination_bait_biographical",
        "hallucination_bait_external"
    }
    assert required_scenarios.issubset(scenarios)
    
    # Check code-switched notes
    code_switched = next(c for c in conversations if c.scenario_type == "code_switched")
    assert "English" in code_switched.notes or "means" in code_switched.notes
    
    # Check risk tags and retrieval categories
    for c in conversations:
        assert len(c.text) > 0
        assert isinstance(c.risk_tags, list)
        assert isinstance(c.expected_retrieval_categories, list)

def test_representative_facets_and_labels():
    rep_csv = Path("data/examples/representative_facets.csv")
    assert rep_csv.exists()
    
    with open(rep_csv, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 21  # 1 header + at least 20 facets
        
    labels_jsonl = Path("data/examples/reference_labels.jsonl")
    assert labels_jsonl.exists()
    
    with open(labels_jsonl, "r", encoding="utf-8") as f:
        labels = [ReferenceLabel.model_validate_json(line) for line in f]
        
    for label in labels:
        assert label.reviewer_status == "proposed"
        assert label.reviewer_name_or_alias is None
        
        if label.expected_status == "scored":
            assert label.expected_score_1_to_5 is not None
            assert label.expected_evidence_quote is not None
        else:
            assert label.expected_score_1_to_5 is None
            
