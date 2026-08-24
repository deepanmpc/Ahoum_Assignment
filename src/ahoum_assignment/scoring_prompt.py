"""Batched scoring prompt template and structured response contract."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator

from ahoum_assignment.models import RetrievalCandidate

# ---------------------------------------------------------------------------
# Response contract
# ---------------------------------------------------------------------------

class ScoringResponseItem(BaseModel):
    """One facet result inside a batch response."""

    facet_id: str
    status: str  # "scored" | "insufficient_evidence" | "not_observable"
    score_1_to_5: Optional[int] = None
    confidence_0_to_1: float
    evidence_quote: str = ""
    reason: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"scored", "insufficient_evidence", "not_observable"}
        if v not in allowed:
            raise ValueError(f"Invalid status '{v}'; must be one of {allowed}")
        return v

    @field_validator("confidence_0_to_1")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_0_to_1 must be in [0, 1]")
        return v

    @model_validator(mode="after")
    def validate_score_status_consistency(self) -> "ScoringResponseItem":
        if self.status == "scored":
            if self.score_1_to_5 is None:
                raise ValueError("scored status requires score_1_to_5")
            if not (1 <= self.score_1_to_5 <= 5):
                raise ValueError(f"score_1_to_5 must be 1–5, got {self.score_1_to_5}")
        else:
            if self.score_1_to_5 is not None:
                raise ValueError(
                    f"status '{self.status}' must have score_1_to_5 = null"
                )
        return self


class ScoringBatchResponse(BaseModel):
    """Top-level JSON returned by the model for one batch."""

    results: List[ScoringResponseItem]


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTIONS = """\
You are a behavioural-evidence scorer. You will receive a conversation \
transcript and a batch of personality/behaviour facets to assess.

RULES — read every one:
1.  Assess ONLY direct linguistic evidence present in the supplied \
conversation. Do NOT infer diagnoses, health conditions, lab values, \
private history, religion, occupation, socioeconomic status, real-world \
behaviour, or biographical facts not explicitly supported by text.
2.  Quoted speech, sarcasm, jokes, and statements about another person are \
NOT automatically evidence about the speaker.
3.  If evidence is absent, weak, contradictory, indirect, or ambiguous, \
return status "insufficient_evidence" — do NOT assign a numeric score.
4.  If the facet is inappropriate to assess from any conversation \
(e.g., medical, diagnostic, external-biography), return "not_observable".
5.  A score must be an integer from 1 to 5 ONLY when direct evidence supports it.
6.  "evidence_quote" must be ONE short EXACT quote copied from the \
conversation. NEVER paraphrase and NEVER quote text that does not appear \
in the input.
7.  Return EXACTLY one result for every requested facet_id — no more, no fewer.
8.  Do NOT mention or assess facets outside the batch.
9.  Output JSON ONLY. No markdown, prose, explanation, or code fences.

SCORING SCALE (use only when evidence exists):
  1 = strong evidence of the low end
  2 = some evidence of the low end
  3 = mixed, moderate, or limited but sufficient evidence
  4 = clear evidence of the high end
  5 = strong and repeated evidence of the high end

OUTPUT FORMAT — exactly this JSON structure, nothing else:
{
  "results": [
    {
      "facet_id": "string",
      "status": "scored | insufficient_evidence | not_observable",
      "score_1_to_5": <integer 1-5 or null>,
      "confidence_0_to_1": <float 0.0-1.0>,
      "evidence_quote": "<exact quote or empty string>",
      "reason": "<one concise evidence-based sentence>"
    }
  ]
}
"""


def build_batch_prompt(
    conversation_text: str,
    candidates: List[RetrievalCandidate],
    *,
    catalogue_rows: dict[str, dict] | None = None,
) -> str:
    """Build a complete scoring prompt for one batch of ≤5 facets.

    ``catalogue_rows`` maps facet_id → full catalogue row dict so that
    scoring definitions and anchors are included.
    """
    if len(candidates) > 5:
        raise ValueError(
            f"Batch must contain at most 5 facets, got {len(candidates)}"
        )
    if not candidates:
        raise ValueError("Batch must contain at least one facet")

    facet_lines: list[str] = []
    for c in candidates:
        row = (catalogue_rows or {}).get(c.facet_id, {})
        scoring_def = row.get("scoring_definition", "")
        anchor_1 = row.get("anchor_1", "")
        anchor_3 = row.get("anchor_3", "")
        anchor_5 = row.get("anchor_5", "")

        block = (
            f"- facet_id: {c.facet_id}\n"
            f"  name: {c.facet_normalized}\n"
            f"  scoring_definition: {scoring_def}\n"
            f"  anchor_1 (low): {anchor_1}\n"
            f"  anchor_3 (moderate): {anchor_3}\n"
            f"  anchor_5 (high): {anchor_5}"
        )
        facet_lines.append(block)

    facets_block = "\n\n".join(facet_lines)

    return (
        f"{_SYSTEM_INSTRUCTIONS}\n"
        f"--- CONVERSATION ---\n{conversation_text}\n--- END ---\n\n"
        f"--- FACETS TO ASSESS ({len(candidates)}) ---\n{facets_block}\n"
        f"--- END FACETS ---\n"
    )


def build_retry_prompt(
    original_prompt: str,
    failure_reasons: list[str],
) -> str:
    """Build a corrective retry prompt for a batch whose first attempt failed."""
    reasons_block = "\n".join(f"- {r}" for r in failure_reasons)
    return (
        f"{original_prompt}\n\n"
        f"YOUR PREVIOUS RESPONSE WAS INVALID. Fix these problems:\n"
        f"{reasons_block}\n\n"
        f"Return the corrected JSON ONLY."
    )
