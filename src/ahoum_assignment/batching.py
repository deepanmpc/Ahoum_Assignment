"""Deterministic batch splitting for scoring."""

from __future__ import annotations

from typing import List

from ahoum_assignment.models import RetrievalCandidate


def split_batches(
    candidates: List[RetrievalCandidate],
    batch_size: int = 5,
) -> List[List[RetrievalCandidate]]:
    """Split candidates into deterministic batches of at most *batch_size*.

    The ordering of candidates is preserved exactly as given.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    return [
        candidates[i : i + batch_size]
        for i in range(0, len(candidates), batch_size)
    ]
