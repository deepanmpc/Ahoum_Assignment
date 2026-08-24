"""Extract best-effort JSON from potentially messy model output."""

from __future__ import annotations

import json
import re
from typing import Optional


def extract_json(raw: str) -> Optional[dict]:
    """Try to extract a JSON object from model output.

    Handles: raw JSON, markdown fences, leading/trailing prose.
    Returns None if no valid JSON can be found.
    """
    # 1. Try direct parse
    text = raw.strip()
    parsed = _try_parse(text)
    if parsed is not None:
        return parsed

    # 2. Try inside markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        parsed = _try_parse(fence_match.group(1).strip())
        if parsed is not None:
            return parsed

    # 3. Try finding the outermost { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        parsed = _try_parse(text[brace_start : brace_end + 1])
        if parsed is not None:
            return parsed

    return None


def _try_parse(text: str) -> Optional[dict]:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, ValueError):
        pass
    return None
