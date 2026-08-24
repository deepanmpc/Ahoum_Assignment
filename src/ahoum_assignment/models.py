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

class ConversationInput(BaseModel):
    conversation_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    language_hint: Optional[str] = None


class RetrievalCandidate(BaseModel):
    facet_id: str
    facet_raw: str
    facet_normalized: str
    facet_category: str
    conversation_observable: str
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    hybrid_score: float
    matched_keywords: list[str] = Field(default_factory=list)
    matched_categories: list[str] = Field(default_factory=list)
    inclusion_reason: str = ""
    exclusion_reason: str = ""
    rank: int = 0

    @model_validator(mode='after')
    def validate_candidate_invariants(self) -> "RetrievalCandidate":
        if self.rank > 0:
            if self.conversation_observable != "true":
                raise ValueError(f"Candidate {self.facet_id} ranked but not marked conversation_observable=true.")
            if not self.inclusion_reason:
                raise ValueError("Included candidate must have an inclusion_reason.")
            if self.semantic_score is None and self.keyword_score is None:
                raise ValueError("Included candidate must have at least one inclusion signal (semantic or keyword).")
        
        if self.rank == 0 and not self.exclusion_reason:
            raise ValueError("Excluded candidate must have an exclusion_reason.")
            
        return self


class RetrievalDiagnostics(BaseModel):
    semantic_candidate_count: int = 0
    keyword_candidate_count: int = 0
    merged_candidate_count: int = 0
    excluded_non_observable_count: int = 0
    duplicate_candidate_count: int = 0
    fallback_behavior: str = "none"


class RetrievalResult(BaseModel):
    conversation_id: str
    candidate_count: int
    candidates: list[RetrievalCandidate]
    excluded_count: int
    retrieval_config_metadata: Dict[str, Any] = Field(default_factory=dict)
    index_version: str
    warnings: list[str] = Field(default_factory=list)
    diagnostics: Optional[RetrievalDiagnostics] = None

    @model_validator(mode='after')
    def validate_result_invariants(self) -> "RetrievalResult":
        seen_ids = set()
        for cand in self.candidates:
            if cand.facet_id in seen_ids:
                raise ValueError(f"Candidate list contains duplicate facet ID: {cand.facet_id}")
            seen_ids.add(cand.facet_id)
            
            if cand.conversation_observable != "true":
                raise ValueError(f"Candidate list contains non-observable facet: {cand.facet_id}")
                
            if cand.rank < 1:
                raise ValueError(f"Candidate {cand.facet_id} is in the result but has rank < 1.")
                
        return self
