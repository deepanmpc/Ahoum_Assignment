# Debugging Log

This document records genuine defects, failed assumptions, and boundary conditions discovered and fixed during the hardening phase (Phase G).

## 1. Pydantic Validator Strictness on Excluded Candidates
**Date**: 2026-08-25
**Symptom**: Integration tests (`test_fault_injection.py`) failed with `pydantic_core._pydantic_core.ValidationError: 1 validation error for RetrievalCandidate... Value error, Excluded candidate must have an exclusion_reason.`
**Reproduction steps**: Instantiate a `RetrievalCandidate` with valid inclusion fields but omit `rank` (which defaults to 0) and `exclusion_reason`.
**Diagnosis**: The `RetrievalCandidate` model uses a strict `@model_validator(mode='after')` that asserts: if `rank == 0` (meaning it was excluded from the top-K), an `exclusion_reason` must be explicitly provided. During testing, I provided a dummy candidate intending it to be an included candidate, but because I did not explicitly set `rank=1`, it defaulted to 0 and crashed.
**Root cause**: The model validator is strictly enforcing the domain invariant that any unranked facet must have a recorded reason for exclusion.
**Fix**: Updated the test fixture in `test_fault_injection.py` to explicitly set `rank=1` and `exclusion_reason=""` when mocking an included candidate, satisfying the Pydantic validator.
**Regression test added**: `tests/integration/test_fault_injection.py` relies on `get_dummy_retrieval` which now properly constructs the Pydantic models.
**Verification command and result**: `pytest tests/integration/test_fault_injection.py` now passes without Pydantic initialization errors.

## 2. API Key Regex Redaction Failed on Quoted JSON Keys
**Date**: 2026-08-25
**Symptom**: `test_redact_secrets` failed the assertion `assert "sk-12345" not in safe_text_3` for a dummy JSON string containing an API key.
**Reproduction steps**: Run `redact_secrets('{"api_key": "sk-1234567890abcdef"}')`.
**Diagnosis**: The string returned was exactly the input string. The regex `r'(?i)(api_key[\s=:]+)[A-Za-z0-9\-\._~+/]+=*'` was attempting to match the `api_key` literal followed by space, equals, or colon. However, in standard JSON, the key is enclosed in double quotes: `"api_key": "..."`. The regex did not allow for a quote character `"` between the key and the colon.
**Root cause**: The redaction regex `[\s=:]+` was too restrictive and failed to match JSON-formatted string literals.
**Fix**: Modified the regex in `src/ahoum_assignment/logging_utils.py` to include double quotes in the separator character class: `[\s=:"]+`.
**Regression test added**: `tests/test_logging.py::test_redact_secrets` contains the exact JSON string format that originally failed.
**Verification command and result**: `pytest tests/test_logging.py` now successfully asserts that the JSON string is redacted to `{"api_key": "[REDACTED]"}`.
