"""Scoring orchestration — batches, calls provider, validates, retries."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from ahoum_assignment.batching import split_batches
from ahoum_assignment.models import RetrievalResult, ScoreStatus
from ahoum_assignment.providers.base import BaseProvider, ProviderError, ProviderResponse
from ahoum_assignment.scoring_prompt import (
    ScoringResponseItem,
    build_batch_prompt,
    build_retry_prompt,
)
from ahoum_assignment.response_validator import validate_batch_response


@dataclass
class BatchOutcome:
    """Result of processing one batch."""

    batch_index: int
    facet_ids: List[str]
    success: bool = False
    items: List[ScoringResponseItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    provider_name: str = ""
    model_name: str = ""
    latency_ms: float = 0.0
    attempts: int = 0
    raw_response_text: str = ""  # stored separately for debug only


@dataclass
class ScoringResult:
    """Aggregated result of scoring all batches for one conversation."""

    conversation_id: str
    batch_outcomes: List[BatchOutcome]
    dry_run: bool = False

    @property
    def total_batches(self) -> int:
        return len(self.batch_outcomes)

    @property
    def successful_batches(self) -> int:
        return sum(1 for b in self.batch_outcomes if b.success)

    @property
    def failed_batches(self) -> int:
        return sum(1 for b in self.batch_outcomes if not b.success)


def load_catalogue_rows(catalogue_path: Path) -> Dict[str, dict]:
    """Load the full catalogue into a dict keyed by facet_id."""
    rows: Dict[str, dict] = {}
    with open(catalogue_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows[row["facet_id"]] = row
    return rows


def score_conversation(
    conversation_id: str,
    conversation_text: str,
    retrieval_result: RetrievalResult,
    provider: Optional[BaseProvider],
    catalogue_path: Path,
    batch_size: int = 5,
    dry_run: bool = False,
) -> ScoringResult:
    """Run the full scoring pipeline for one conversation.

    If *dry_run* is True, prompts are built but no provider call is made.
    """
    # Assert all candidates are observable
    for c in retrieval_result.candidates:
        if c.conversation_observable != "true":
            raise ValueError(
                f"Non-observable facet {c.facet_id} passed to scorer"
            )

    catalogue_rows = load_catalogue_rows(catalogue_path)
    batches = split_batches(retrieval_result.candidates, batch_size)

    outcomes: List[BatchOutcome] = []

    for idx, batch in enumerate(batches):
        facet_ids = [c.facet_id for c in batch]
        outcome = BatchOutcome(
            batch_index=idx,
            facet_ids=facet_ids,
        )

        prompt = build_batch_prompt(
            conversation_text, batch, catalogue_rows=catalogue_rows
        )

        if dry_run:
            outcome.success = True
            outcome.attempts = 0
            outcomes.append(outcome)
            continue

        if provider is None:
            outcome.success = False
            outcome.errors = ["No provider configured"]
            outcomes.append(outcome)
            continue

        # --- Attempt 1 ---
        try:
            resp: ProviderResponse = provider.generate(prompt)
        except ProviderError as exc:
            outcome.success = False
            outcome.errors = [f"Provider error: {exc.safe_message}"]
            outcome.provider_name = provider.provider_name
            outcome.model_name = provider.model_name
            outcome.attempts = 1
            outcomes.append(outcome)
            continue

        outcome.provider_name = resp.provider_name
        outcome.model_name = resp.model_name
        outcome.latency_ms = resp.latency_ms
        outcome.raw_response_text = resp.text
        outcome.attempts = 1

        validation = validate_batch_response(
            resp.text, facet_ids, conversation_text
        )

        if validation.success:
            outcome.success = True
            outcome.items = validation.items
            outcomes.append(outcome)
            continue

        # --- Corrective Retry (once) ---
        retry_prompt = build_retry_prompt(prompt, validation.errors)
        try:
            resp2 = provider.generate(retry_prompt)
        except ProviderError as exc:
            outcome.success = False
            outcome.errors = validation.errors + [
                f"Retry provider error: {exc.safe_message}"
            ]
            outcome.attempts = 2
            outcomes.append(outcome)
            continue

        outcome.latency_ms += resp2.latency_ms
        outcome.raw_response_text = resp2.text
        outcome.attempts = 2

        validation2 = validate_batch_response(
            resp2.text, facet_ids, conversation_text
        )

        if validation2.success:
            outcome.success = True
            outcome.items = validation2.items
        else:
            outcome.success = False
            outcome.errors = validation2.errors

        outcomes.append(outcome)

    return ScoringResult(
        conversation_id=conversation_id,
        batch_outcomes=outcomes,
        dry_run=dry_run,
    )
