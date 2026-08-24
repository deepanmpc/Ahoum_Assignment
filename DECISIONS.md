# Engineering decisions

## D1 — Start with a dependency-free project core

- **Problem:** The assignment needs reproducible setup, but early development
  should not be blocked by model downloads or a provider account.
- **Options considered:** Use a full dependency stack immediately; use only
  standard-library contracts/configuration until model integration; or build
  directly inside a notebook.
- **Choice:** Use a `src/` Python package, TOML configuration, dataclasses, and
  a no-network diagnostic command in Phase A.
- **Trade-off:** Response parsing will gain a richer validation library later;
  in return, the foundation and CI smoke tests remain lightweight and reliable.

## D2 — Make abstention structurally different from a neutral score

- **Problem:** A score of 3 can be misread as “unknown,” encouraging invented
  assessments where the conversation supplies no evidence.
- **Options considered:** Always return 1–5; use a sentinel numeric value; or
  use an explicit status and nullable score.
- **Choice:** Use an explicit status enum and allow `score_1_to_5` only for
  `scored` results.
- **Trade-off:** Consumers must handle status fields, but unsupported facets
  cannot silently become a fabricated numeric result.
