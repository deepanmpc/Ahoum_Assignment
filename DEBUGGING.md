# Debugging Log

This document records genuine defects, failed assumptions, and boundary
conditions discovered during implementation and hardening. Each entry includes
a reproducible symptom, root cause, fix, and verification.

---

## 1. Pydantic Validator Strictness on Excluded Candidates

**Phase**: G (Reliability Hardening)
**Date**: 2026-08-25

**Symptom**: Integration tests (`test_fault_injection.py`) failed with:
```
pydantic_core.ValidationError: 1 validation error for RetrievalCandidate
  Value error, Excluded candidate must have an exclusion_reason.
```

**Reproduction steps**:
```python
from ahoum_assignment.models import RetrievalCandidate
# This crashes — rank defaults to 0, triggering the exclusion invariant
RetrievalCandidate(
    facet_id="f1", facet_raw="f1", facet_normalized="f1",
    facet_category="cat", conversation_observable="true",
    semantic_score=1.0, keyword_score=1.0, hybrid_score=1.0,
    inclusion_reason="test"
)
```

**Diagnosis**: The `@model_validator` on `RetrievalCandidate` enforces: if
`rank == 0` (default), the candidate is treated as excluded and must have an
`exclusion_reason`. But the test intended this as an included candidate and
did not set `rank=1`.

**Root cause**: The Pydantic model's default `rank=0` silently triggers the
exclusion branch of the validator. Any test creating an "included" candidate
must explicitly set `rank >= 1`.

**Fix**: Updated `test_fault_injection.py:get_dummy_retrieval` to set
`rank=1` and `exclusion_reason=""` when mocking included candidates.

**Regression test**: `tests/integration/test_fault_injection.py` — all three
fault-injection tests now construct candidates correctly.

**Verification**:
```bash
python -m pytest tests/integration/test_fault_injection.py -v
# Result: 3 passed
```

**Remaining limitation**: Any new test creating `RetrievalCandidate` instances
must remember to set `rank >= 1` for included candidates. This is by design —
the validator exists to prevent accidental unranked candidates from reaching
the scorer.

---

## 2. API Key Regex Redaction Failed on Quoted JSON Keys

**Phase**: G (Reliability Hardening)
**Date**: 2026-08-25

**Symptom**: `test_redact_secrets` failed:
```
assert "sk-12345" not in safe_text_3
AssertionError: 'sk-12345' is contained here:
  {"api_key": "sk-1234567890abcdef"}
```

**Reproduction steps**:
```python
from ahoum_assignment.logging_utils import redact_secrets
result = redact_secrets('{"api_key": "sk-1234567890abcdef"}')
# Expected: {"api_key": "[REDACTED]"}
# Actual:   {"api_key": "sk-1234567890abcdef"}  (unchanged)
```

**Diagnosis**: The regex pattern `r'(?i)(api_key[\s=:]+)...'` expected the
separator between key and value to be whitespace, `=`, or `:`. In JSON, the
actual separator is `": "` (colon + space + quote). The quote character `"`
was not in the character class, so the regex did not match.

**Root cause**: The separator character class `[\s=:]+` was too restrictive
for JSON syntax where values are enclosed in double quotes.

**Fix**: Changed the regex to `[\s=:"]+` in `src/ahoum_assignment/logging_utils.py`,
allowing the quote character in the separator.

**Regression test**: `tests/test_logging.py::test_redact_secrets` — contains
the exact JSON string that originally failed.

**Verification**:
```bash
python -m pytest tests/test_logging.py -v
# Result: 2 passed
```

**Remaining limitation**: The regex is intentionally simple. It handles
`api_key` in JSON, TOML, and environment-variable formats but will not catch
arbitrarily named secret fields (e.g., `"secret_token": "..."`). Adding more
patterns is straightforward but risks false-positive redaction.
