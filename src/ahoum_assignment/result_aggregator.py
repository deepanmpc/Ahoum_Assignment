"""Aggregate batch outcomes into a single conversation-level result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from ahoum_assignment.models import FacetScore, ScoreStatus, RetrievalResult
from ahoum_assignment.scoring_service import ScoringResult, BatchOutcome
from ahoum_assignment.scoring_prompt import ScoringResponseItem


@dataclass
class ConversationScoringResult:
    """Final, serialisable conversation-level result."""

    conversation_id: str
    candidate_count: int
    scored_count: int
    insufficient_evidence_count: int
    not_observable_count: int
    error_count: int
    retrieval_excluded_count: int
    batch_count: int
    total_latency_ms: float
    provider: str
    model: str
    facet_scores: List[FacetScore]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "candidate_count": self.candidate_count,
            "scored_count": self.scored_count,
            "insufficient_evidence_count": self.insufficient_evidence_count,
            "not_observable_count": self.not_observable_count,
            "error_count": self.error_count,
            "retrieval_excluded_count": self.retrieval_excluded_count,
            "batch_count": self.batch_count,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "provider": self.provider,
            "model": self.model,
            "warnings": self.warnings,
            "facet_scores": [fs.model_dump() for fs in self.facet_scores],
        }


def _status_from_str(s: str) -> ScoreStatus:
    mapping = {
        "scored": ScoreStatus.SCORED,
        "insufficient_evidence": ScoreStatus.INSUFFICIENT_EVIDENCE,
        "not_observable": ScoreStatus.NOT_OBSERVABLE,
    }
    return mapping.get(s, ScoreStatus.ERROR)


def aggregate_results(
    retrieval_result: RetrievalResult,
    scoring_result: ScoringResult,
) -> ConversationScoringResult:
    """Merge all batch outcomes into one deterministic conversation result."""

    # Build lookup from retrieval
    cand_lookup = {c.facet_id: c for c in retrieval_result.candidates}

    scored_items: Dict[str, FacetScore] = {}
    warnings: list[str] = []
    total_latency = 0.0
    provider_name = ""
    model_name = ""

    for outcome in scoring_result.batch_outcomes:
        total_latency += outcome.latency_ms
        if outcome.provider_name:
            provider_name = outcome.provider_name
        if outcome.model_name:
            model_name = outcome.model_name

        if outcome.success:
            for item in outcome.items:
                cand = cand_lookup.get(item.facet_id)
                if cand is None:
                    continue
                if item.facet_id in scored_items:
                    warnings.append(f"Duplicate result for {item.facet_id}")
                    continue

                status = _status_from_str(item.status)
                scored_items[item.facet_id] = FacetScore(
                    facet_id=item.facet_id,
                    facet_raw=cand.facet_raw,
                    facet_normalized=cand.facet_normalized,
                    status=status,
                    score_1_to_5=item.score_1_to_5,
                    confidence_0_to_1=item.confidence_0_to_1,
                    evidence=item.evidence_quote or None,
                    reason=item.reason,
                    model_metadata={
                        "provider": outcome.provider_name,
                        "model": outcome.model_name,
                        "batch_index": outcome.batch_index,
                        "attempts": outcome.attempts,
                    },
                )
        else:
            # Failed batch — mark each facet as error
            for fid in outcome.facet_ids:
                cand = cand_lookup.get(fid)
                if cand is None:
                    continue
                if fid in scored_items:
                    continue
                scored_items[fid] = FacetScore(
                    facet_id=fid,
                    facet_raw=cand.facet_raw,
                    facet_normalized=cand.facet_normalized,
                    status=ScoreStatus.ERROR,
                    confidence_0_to_1=0.0,
                    reason=f"Batch {outcome.batch_index} failed: "
                           + "; ".join(outcome.errors)[:200],
                    model_metadata={
                        "batch_index": outcome.batch_index,
                        "errors": outcome.errors,
                    },
                )

    # Build deterministic ordered list by original retrieval rank
    ordered: list[FacetScore] = []
    for cand in retrieval_result.candidates:
        if cand.facet_id in scored_items:
            ordered.append(scored_items[cand.facet_id])

    counts = {s: 0 for s in ScoreStatus}
    for fs in ordered:
        counts[fs.status] += 1

    return ConversationScoringResult(
        conversation_id=scoring_result.conversation_id,
        candidate_count=len(ordered),
        scored_count=counts[ScoreStatus.SCORED],
        insufficient_evidence_count=counts[ScoreStatus.INSUFFICIENT_EVIDENCE],
        not_observable_count=counts[ScoreStatus.NOT_OBSERVABLE],
        error_count=counts[ScoreStatus.ERROR],
        retrieval_excluded_count=retrieval_result.excluded_count,
        batch_count=scoring_result.total_batches,
        total_latency_ms=total_latency,
        provider=provider_name,
        model=model_name,
        facet_scores=ordered,
        warnings=warnings,
    )
