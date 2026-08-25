from typing import Optional, List, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class BenchmarkConversation(BaseModel):
    conversation_id: str
    title: str
    text: str
    scenario_type: str
    language: str
    risk_tags: List[str]
    notes: str
    expected_retrieval_categories: List[str]
    author_status: Literal["proposed", "reviewed_accepted", "reviewed_changed", "rejected"] = "proposed"


class ReferenceLabel(BaseModel):
    conversation_id: str
    facet_id: str
    expected_status: Literal["scored", "insufficient_evidence", "not_observable", "retrieval_excluded"]
    expected_score_1_to_5: Optional[int] = None
    expected_evidence_quote: Optional[str] = None
    label_rationale: str
    label_scope: Literal["retrieval_relevance", "scoring_reference", "abstention_reference"]
    proposed_by: str = "agent"
    reviewer_status: Literal["proposed", "reviewed_accepted", "reviewed_changed", "rejected"] = "proposed"
    reviewer_name_or_alias: Optional[str] = None
    review_date: Optional[str] = None

    @model_validator(mode="after")
    def validate_score_and_evidence(self) -> "ReferenceLabel":
        if self.expected_status == "scored":
            if self.expected_score_1_to_5 is None:
                raise ValueError("expected_score_1_to_5 must be set when expected_status is 'scored'")
            if not self.expected_score_1_to_5 in (1, 2, 3, 4, 5):
                raise ValueError("expected_score_1_to_5 must be between 1 and 5")
            if not self.expected_evidence_quote:
                raise ValueError("expected_evidence_quote must be provided for scored labels")
        else:
            if self.expected_score_1_to_5 is not None:
                raise ValueError(f"expected_score_1_to_5 must be null when status is '{self.expected_status}'")
            
        return self
