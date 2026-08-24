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
