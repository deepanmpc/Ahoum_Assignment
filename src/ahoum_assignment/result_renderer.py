"""Human-readable result renderer for local inspection."""

from __future__ import annotations

from ahoum_assignment.result_aggregator import ConversationScoringResult


def render(result: ConversationScoringResult) -> str:
    """Return a concise human-readable summary (no secrets, no raw text)."""
    lines = [
        f"=== Scoring Result: {result.conversation_id} ===",
        f"Provider: {result.provider or 'N/A'}  Model: {result.model or 'N/A'}",
        f"Batches: {result.batch_count}  Latency: {result.total_latency_ms:.0f}ms",
        f"Candidates: {result.candidate_count}  "
        f"Scored: {result.scored_count}  "
        f"Abstained: {result.insufficient_evidence_count}  "
        f"Not-Observable: {result.not_observable_count}  "
        f"Errors: {result.error_count}",
        f"Retrieval-Excluded: {result.retrieval_excluded_count}",
        "",
    ]

    for fs in result.facet_scores:
        score_str = str(fs.score_1_to_5) if fs.score_1_to_5 is not None else "—"
        lines.append(
            f"  [{fs.status.value:>24}] {fs.facet_normalized:<40} "
            f"Score: {score_str}  Conf: {fs.confidence_0_to_1:.2f}  "
            f"Reason: {fs.reason}"
        )

    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in result.warnings:
            lines.append(f"  ⚠ {w}")

    return "\n".join(lines)
