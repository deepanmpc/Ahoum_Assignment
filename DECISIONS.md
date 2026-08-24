# Engineering decisions

## D1 — Introduce Pydantic early for robust contract validation

- **Problem:** The system requires strict adherence to result contracts (e.g. nullable scores on abstention, confidence boundaries) to prevent downstream evaluation errors.
- **Options considered:** Use standard-library `dataclasses` and manual `__post_init__` checks, or adopt a validation library like `pydantic` early.
- **Choice:** Adopt `pydantic` in Phase A to define `FacetRecord` and `FacetScore` with strict field and model validators.
- **Trade-off:** Adds a third-party dependency early in the project before API integrations, but significantly increases trust in the data boundaries and prevents silent invalid states.

## D2 — Make abstention structurally different from a neutral score

- **Problem:** A score of 3 can be misread as “unknown,” encouraging invented
  assessments where the conversation supplies no evidence.
- **Options considered:** Always return 1–5; use a sentinel numeric value; or
  use an explicit status and nullable score.
- **Choice:** Use an explicit status enum and allow `score_1_to_5` only for
  `scored` results.
- **Trade-off:** Consumers must handle status fields, but unsupported facets
  cannot silently become a fabricated numeric result.
