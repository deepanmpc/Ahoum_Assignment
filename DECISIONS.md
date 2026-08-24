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

## D3 — Deterministic taxonomy rules over unrestricted LLM labeling

- **Problem:** Facet classification (e.g., observability, sensitivity) needs to scale to thousands of heterogeneous records consistently, without hallucinating medical observability.
- **Options considered:** Use a zero-shot LLM prompt to dynamically assign categories and observability; or build a transparent, rule-based keyword mapping system with deterministic outputs and an explicit override list.
- **Choice:** Use a transparent, version-controlled rule engine based on regex keyword sets and an editable override CSV file.
- **Trade-off:** Manual rules require upfront effort to curate and maintain, and leave many edge cases classified as "uncertain". However, this ensures that high-risk medical or religious facets are never accidentally classified as "conversationally observable" due to LLM stochasticity.

## D4 — Transparent Keyword Routing Alongside Semantic Retrieval

- **Problem:** Pure semantic retrieval (cosine similarity) often hallucinates conceptual proximity, linking conversational idioms to unrelated behavioral facets. 
- **Options considered:** Rely solely on fine-tuning an embedding model, or build an independent, transparent rule-based keyword router to complement the semantic index.
- **Choice:** Implement a transparent keyword/category router (`src/ahoum_assignment/keyword_router.py`) configured via a version-controlled TOML file (`config/routing_rules.toml`).
- **Trade-off:** Maintaining regex-based keyword lists requires manual curation and doesn't scale perfectly to zero-shot linguistic nuance. However, it completely eliminates naive substring errors, supports explicit negative exclusions, and provides a deterministic bedrock for highly critical behavioral categories (like finance and emotional regulation) that must not be missed by fuzzy semantic models.

## D5 — Hybrid vs Single-Route Retrieval Trade-offs

- **Problem:** Semantic models provide excellent conceptual recall but lack precise boundaries, leading to false-positive clustering on weak evidence. Pure keyword systems offer 100% precision for defined phrases but terrible recall for the countless ways humans express traits.
- **Choice:** Implemented a unified `HybridRetriever` that merges both streams. 
- **Trade-off:** Operating two distinct retrieval paths incurs a slight compute and memory overhead compared to a single vector database query. However, by strictly decoupling the keyword safety net from the fuzzy semantic engine, we gain deterministic explainability (`inclusion_reason` clearly separates whether a facet was found via a hard rule match or a vector similarity calculation). This allows the system to easily block medical hallucination bait (via keywords) while gently surfacing nuanced emotional traits (via vectors).
