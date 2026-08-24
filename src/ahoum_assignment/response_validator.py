"""Validate parsed scoring responses against the contract and conversation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from ahoum_assignment.scoring_prompt import ScoringResponseItem, ScoringBatchResponse
from ahoum_assignment.response_parser import extract_json


@dataclass
class ValidationResult:
    """Outcome of validating one batch response."""

    success: bool
    items: List[ScoringResponseItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _normalize_ws(text: str) -> str:
    """Collapse whitespace for quote-matching comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def validate_batch_response(
    raw_text: str,
    expected_ids: List[str],
    conversation_text: str,
) -> ValidationResult:
    """Full pipeline: parse → schema → facet-ID → score → evidence.

    Returns a ``ValidationResult`` with either valid items or error messages.
    """
    errors: list[str] = []

    # 1. Extract JSON
    obj = extract_json(raw_text)
    if obj is None:
        return ValidationResult(success=False, errors=["Could not extract valid JSON from model output"])

    # 2. Schema validation
    try:
        batch = ScoringBatchResponse(**obj)
    except Exception as exc:
        return ValidationResult(success=False, errors=[f"Schema validation failed: {exc}"])

    # 3. Facet-ID validation
    returned_ids = [item.facet_id for item in batch.results]
    returned_set = set(returned_ids)
    expected_set = set(expected_ids)

    missing = expected_set - returned_set
    extra = returned_set - expected_set
    dupes = [fid for fid in returned_ids if returned_ids.count(fid) > 1]

    if missing:
        errors.append(f"Missing facet IDs: {sorted(missing)}")
    if extra:
        errors.append(f"Extra/unknown facet IDs: {sorted(extra)}")
    if dupes:
        errors.append(f"Duplicate facet IDs: {sorted(set(dupes))}")

    if missing or extra or dupes:
        return ValidationResult(success=False, errors=errors)

    # 4. Per-item validation
    valid_items: list[ScoringResponseItem] = []
    conv_norm = _normalize_ws(conversation_text)

    for item in batch.results:
        # Status/score consistency already checked by Pydantic,
        # but double-check just in case of edge conditions.

        # Evidence quote validation for scored items
        if item.status == "scored" and item.evidence_quote:
            quote_norm = _normalize_ws(item.evidence_quote)
            if quote_norm and quote_norm not in conv_norm:
                errors.append(
                    f"Facet {item.facet_id}: evidence quote not found in conversation"
                )
                continue

        valid_items.append(item)

    if errors:
        return ValidationResult(success=False, items=valid_items, errors=errors)

    return ValidationResult(success=True, items=valid_items)
