import pytest
from datetime import datetime
from ahoum_assignment.benchmark_models import ReferenceLabel

def test_reviewer_status_transition():
    # Initial state
    label = ReferenceLabel(
        conversation_id="c1",
        facet_id="f1",
        expected_status="insufficient_evidence",
        label_rationale="test",
        label_scope="abstention_reference",
        proposed_by="agent"
    )
    
    assert label.reviewer_status == "proposed"
    assert label.reviewer_name_or_alias is None
    
    # Transition to accepted
    label.reviewer_status = "reviewed_accepted"
    label.reviewer_name_or_alias = "deepan"
    label.review_date = datetime.now().isoformat()
    
    # Validate it passes Pydantic checks
    label2 = ReferenceLabel.model_validate(label.model_dump())
    assert label2.reviewer_status == "reviewed_accepted"
    assert label2.reviewer_name_or_alias == "deepan"
    assert label2.review_date is not None

def test_label_edit_validation():
    label = ReferenceLabel(
        conversation_id="c1",
        facet_id="f1",
        expected_status="insufficient_evidence",
        label_rationale="test",
        label_scope="abstention_reference",
        proposed_by="agent"
    )
    
    # Simulate an edit to "scored"
    label.expected_status = "scored"
    label.expected_score_1_to_5 = 4
    label.expected_evidence_quote = "hello"
    label.reviewer_status = "reviewed_changed"
    
    # Must be valid
    valid_label = ReferenceLabel.model_validate(label.model_dump())
    assert valid_label.expected_status == "scored"
