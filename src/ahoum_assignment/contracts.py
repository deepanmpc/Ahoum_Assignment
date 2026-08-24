"""Stable data contracts shared by preprocessing, retrieval, and scoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScoreStatus(StrEnum):
    """How a facet was handled for one conversation."""

    SCORED = "scored"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_OBSERVABLE = "not_observable"
    RETRIEVAL_EXCLUDED = "retrieval_excluded"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class FacetRecord:
    """A catalogue entry after the offline preprocessing stage."""

    facet_id: str
    facet_raw: str
    facet_normalized: str
    category: str
    conversation_observable: bool | None
    sensitivity: str
    scoring_definition: str | None = None
    abstention_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.facet_id.strip():
            raise ValueError("facet_id must not be blank")
        if not self.facet_raw.strip():
            raise ValueError("facet_raw must not be blank")
        if not self.facet_normalized.strip():
            raise ValueError("facet_normalized must not be blank")


@dataclass(frozen=True, slots=True)
class FacetScore:
    """Validated final result for a candidate facet."""

    facet_id: str
    facet_raw: str
    facet_normalized: str
    status: ScoreStatus
    score_1_to_5: int | None
    confidence_0_to_1: float
    evidence: str
    reason: str
    model_metadata: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.facet_id.strip():
            raise ValueError("facet_id must not be blank")
        if not 0.0 <= self.confidence_0_to_1 <= 1.0:
            raise ValueError("confidence_0_to_1 must be between 0 and 1")
        if self.status is ScoreStatus.SCORED:
            if self.score_1_to_5 not in {1, 2, 3, 4, 5}:
                raise ValueError("scored results require an integer score from 1 to 5")
        elif self.score_1_to_5 is not None:
            raise ValueError("abstentions and errors must not contain a numeric score")
        if not self.reason.strip():
            raise ValueError("reason must not be blank")
