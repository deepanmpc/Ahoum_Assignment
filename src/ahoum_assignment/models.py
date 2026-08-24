from enum import Enum
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class ScoreStatus(str, Enum):
    SCORED = "scored"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_OBSERVABLE = "not_observable"
    RETRIEVAL_EXCLUDED = "retrieval_excluded"
    ERROR = "error"


class FacetRecord(BaseModel):
    facet_id: str = Field(..., description="Stable ID for the facet")
    facet_raw: str = Field(..., description="Raw facet string from the source data")
    facet_normalized: str = Field(..., description="Normalized facet name")
    category: Optional[str] = None
    conversation_observable: Literal["true", "false", "uncertain"]
    sensitivity: Optional[str] = None
    scoring_definition: Optional[str] = None
    abstention_reason: Optional[str] = None

    @field_validator("facet_id", "facet_raw", "facet_normalized")
    @classmethod
    def check_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be blank")
        return v


class FacetScore(BaseModel):
    facet_id: str
    facet_raw: str
    facet_normalized: str
    status: ScoreStatus
    score_1_to_5: Optional[int] = None
    confidence_0_to_1: float
    evidence: Optional[str] = None
    reason: str
    model_metadata: Optional[Dict[str, Any]] = None

    @field_validator("facet_id", "facet_raw", "facet_normalized", "reason")
    @classmethod
    def check_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be blank")
        return v

    @field_validator("confidence_0_to_1")
    @classmethod
    def check_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return v

    @model_validator(mode="after")
    def validate_score_status(self) -> "FacetScore":
        if self.status == ScoreStatus.SCORED:
            if self.score_1_to_5 is None:
                raise ValueError("A scored result must have a score between 1 and 5")
            if not (1 <= self.score_1_to_5 <= 5):
                raise ValueError("Score must be between 1 and 5")
        else:
            if self.score_1_to_5 is not None:
                raise ValueError(f"Status '{self.status.value}' cannot have a numeric score")
        return self
