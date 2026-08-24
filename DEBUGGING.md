# Debugging record

Real issues, failed assumptions, diagnoses, fixes, and verification evidence
are recorded here as they arise. Phase A establishes this format; later phases
will add at least two reproducible debugging entries.

## Overly Broad Medical and Biography Keywords

- **Symptom:** During the Phase B review, several non-medical facets like "Subscription count" and "Pilgrimage participation count" were incorrectly classified as `health_medical` with a `high_risk` sensitivity. Similarly, "Encouraging participation" was marked as `biography_external`.
- **Diagnosis:** The regex patterns for medical facets included highly generic words like `count`, `level`, and `pain` without contextual bounds. The biographical pattern included `participation` and `attendance`.
- **Root cause:** Naive keyword matching prioritizing broad string inclusion over strict domain terminology.
- **Fix:** Removed broad terms (`count`, `level`, `pain`, `participation`, `attendance`) from the regex rules in `taxonomy_rules.py`, forcing these entries to safely fall back to `uncertain` (or match a more appropriate rule, like `knowledge` -> `skills` or `pilgrimage` -> `religion_culture`). Added regression tests in `test_taxonomy.py`.
- **Verification:** Ran `.venv/bin/python -m pytest tests/` confirming the regression tests passed, and inspected the generated catalogue to confirm "Subscription count" correctly fell back to `unclear`.
