# Prompt log

This file records material AI-assisted work during the assignment. Entries are
added as work occurs, including what was retained, what was changed, and how it
was verified.

## 2026-08-24 — Phase A foundation

- **Tool/model:** Codex (GPT-5)
- **Prompt summary:** Create a reproducible repository foundation for a
  scalable, abstention-aware conversation facet scorer. Include configuration,
  stable result contracts, a no-network diagnostic command, tests, and a
  detailed Phase A agent-prompt document.
- **Used:** Repository structure, standard-library configuration loader,
  explicit score/abstention contract, and smoke-test design.
- **Changed/rejected:** A generic suggestion to use Pydantic was deferred.
  Phase A uses standard-library dataclasses so configuration and contract tests
  work without installing dependencies; a later phase may add Pydantic at the
  model-response boundary where it is useful.
- **Verification:** Run `python scripts/doctor.py doctor` and
  `python -m pytest` from the repository root.

## What AI got wrong / what I corrected

This section will contain at least two concrete corrections observed during
implementation and testing. The Phase A decision to avoid a premature runtime
dependency is recorded above; later entries will document test- or
model-observed corrections.

## 2026-08-24 — Phase A1 (Re-execution)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Create a clean, reproducible Python project foundation for the future conversation-to-facet scoring pipeline. Define typed contracts and strict validations.
- **Used:** `pydantic` for `FacetRecord` and `FacetScore` to provide robust validation. Updated `.gitignore`, `.env.example`, and directory structure per requirements.
- **Deliberately not implemented:** Facet classification, embeddings, LLM calls, provider SDKs, benchmarks, and fake output data.
- **Verification command:** `python -m pytest tests/`

## 2026-08-24 — Phase A2 (Re-execution)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Add central configuration for the future pipeline and a local diagnostic command, explicitly avoiding network calls or unimplemented features.
- **Used:** `.toml` config parsing using Python 3.11+ `tomllib`, dataclasses for schema `AppConfig`. Added `pytest` coverage for configuration overrides. 
- **Deliberately not implemented:** No provider integrations, embeddings, retrieval logic, scoring, API requests, or API key parsing.
- **Verification command:** `.venv/bin/python scripts/doctor.py doctor` and `.venv/bin/python -m pytest tests/test_config.py`

## 2026-08-24 — Phase A4 Review & Handoff (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Independent review of Phase A. Audit repository against 8 risks (abstention vs neutral, accidental network calls, overwriting raw data, accidental commits, config reproducibility, honest README, environment setup, model config logic). Final verify of all deliverables.
- **Used:** `git check-ignore`, `pytest`, `scripts/doctor.py`.
- **What was changed:** Updated `DECISIONS.md` to truthfully reflect the choice of `pydantic` over standard library `dataclasses`.
- **Verification:** All checklists passed cleanly.

## 2026-08-24 — Phase B1 Data Audit & Schema Definition (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Inspect raw CSV data without changing it, produce a reproducible audit, and define the enriched catalogue schema based on strict observational constraints.
- **Used:** Python scripting to run heuristics on the raw CSV. Discovered 399 total valid lines with numbering prefixes, trailing colons, CamelCase anomalies, and domain-specific facets (e.g., "FSH level", "Pilgrimage participation count"). Drafted schema in `docs/facet_catalogue_schema.md`.
- **Deliberately not implemented:** Did not manually label the 399 facets or generate the final `.csv`. The prompt strictly requested evidence and schema definitions only.
- **Verification command:** Checked outputs in `data/processed/facet_audit.json`, `data/processed/facet_audit.md`, and `docs/facet_catalogue_schema.md`.

## 2026-08-25 — Phase B2 Facet Preprocessing Pipeline (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Implement deterministic, repeatable pipeline (`scripts/preprocess_facets.py`) to build `facet_catalogue.csv`. Perform normalization (whitespace, trailing colons, numbering prefixes) and malformed value detection without invoking LLMs.
- **Used:** Python `csv` module, regex heuristics for normalization and string quality checks. Implemented MD5-based stable ID generation leveraging row index and raw values. Added tests covering all string mutation and preservation constraints.
- **Deliberately not implemented:** No API calls or LLM usage for categorization. Placeholders were used for observable and classification labels.
- **Verification command:** `.venv/bin/python -m pytest tests/test_preprocessing.py` and `.venv/bin/python scripts/preprocess_facets.py`
