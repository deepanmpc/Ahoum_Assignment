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

## 2026-08-25 — Phase B3 Taxonomy and Observability Logic (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Extend the deterministic preprocessing pipeline to include a controlled taxonomy, observability policy, and sensitivity policy using a rule-based system instead of an LLM.
- **Used:** Python regex mapping rules (`src/ahoum_assignment/taxonomy_rules.py`) with support for an editable `facet_overrides.csv`. Added test cases for medical, biographical, and religious facets. Accumulated classification statistics and updated `facet_audit.md`.
- **Deliberately not implemented:** Did not use an LLM for classification. Remaining facets that did not match strict rules were deterministically marked as "uncertain".
- **Verification command:** `.venv/bin/python scripts/preprocess_facets.py` and `.venv/bin/python -m pytest tests/`

## 2026-08-25 — Phase B4 Anchor and Scoring Definitions (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Extend preprocessing to generate deterministic scoring definitions and anchors (1, 3, 5) exclusively for `conversation_observable=true` facets, leaving non-observable items strictly unanchored with abstention reasons.
- **Used:** Implemented template-based generation logic (`src/ahoum_assignment/anchor_rules.py`) relying on facet types. Added support for `anchor_overrides.csv`. Added test cases verifying anchor application logic and override priority. Collected quality report stats during generation and appended to `facet_audit.md`.
- **Deliberately not implemented:** Did not manually edit the generated CSV output, relying fully on deterministic generation. Did not create fake scales for unobservable properties.
- **Verification command:** `.venv/bin/python -m pytest tests/` and `.venv/bin/python scripts/preprocess_facets.py`

## 2026-08-25 — Phase B Review and Correction (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Act as a skeptical reviewer for the Phase B catalogue generation. Sample generated rows to identify unsafe observables, weak anchors, broad taxonomy classifications, and unstable data.
- **Used:** Sampled the catalogue and identified false-positive medical and biographical classifications (e.g., "Subscription count" marked as `health_medical` due to the keyword "count"). Corrected the regex rules in `taxonomy_rules.py` by removing generic keywords (`count`, `level`, `participation`, `pain`).
- **Deliberately not implemented:** Did not manually edit generated CSV rows or use an LLM for remediation. All fixes were made to the deterministic rules.
- **Verification command:** Reran `.venv/bin/python scripts/preprocess_facets.py`, verified with `.venv/bin/python -m pytest tests/` (which includes new regression tests), and documented the defect in `DEBUGGING.md`.

## 2026-08-25 — Phase B Handoff Review (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Verify Phase B pipeline reproducibility and stability. Ensure raw values are preserved, malformed rows retained, IDs stable, observability states correct, unobservables unanchored, and rules inspectable. Update documentation with summaries and limitations.
- **Used:** Wrote a verification script simulating a dual-run state, comparing `data/processed/facet_catalogue.csv` outputs to guarantee byte-for-byte stability. Extracted summary statistics for the README update.
- **Deliberately not implemented:** Did not implement Phase C retrieval, embeddings, or LLM scoring.
- **Verification command:** Ran double-execution with `cmp` confirming deterministic hashing and generation outputs.

## 2026-08-25 — Phase C1 Hybrid Retrieval Contracts (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Define clear, typed Pydantic contracts for Phase C's retrieval system (without implementing actual embeddings or vector databases). Ensure strict invariants to filter out non-observable facets from final candidate lists.
- **Used:** Defined `ConversationInput`, `RetrievalCandidate`, `RetrievalDiagnostics`, and `RetrievalResult` in `src/ahoum_assignment/models.py`. Leveraged Pydantic's `@model_validator` to enforce inclusion/exclusion reasons, signal requirements, rank restrictions, and strict deduplication. Wrote `docs/retrieval_contracts.md` and `tests/test_retrieval_contracts.py`.
- **Deliberately not implemented:** No vector databases, LLM calls, or actual embedding dependencies were installed or coded.
- **Verification command:** `.venv/bin/python -m pytest tests/test_retrieval_contracts.py`

## 2026-08-25 — Phase C2 Offline Semantic Retrieval Index (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Implement the offline semantic retrieval index. Construct text documents strictly from observable facets, implement an embedding abstraction (without forcing heavy library downloads during tests), build L2-normalized embeddings into a numpy compressed file, and ensure index metadata tracks versions and hashes.
- **Used:** Wrote `src/ahoum_assignment/embeddings.py` featuring an abstract `Embedder` protocol, a `SentenceTransformerEmbedder` for real execution, and a `FakeDeterministicEmbedder` (md5-based) for unit testing. Created `src/ahoum_assignment/semantic_index.py` to enforce strict eligibility filtering (omitting medical/unobservable items) and compute cosine-ready `npz` files alongside JSON metadata. Appended instructions to `README.md`.
- **Deliberately not implemented:** Avoided heavyweight vector databases (e.g., Pinecone, Chroma) in favor of simple local numpy files. Did not hard-require PyTorch in unit tests; tests use the mock embedder ensuring they run fast offline.
- **Verification command:** `.venv/bin/python -m pytest tests/test_semantic_index.py` and `.venv/bin/python scripts/build_index.py`

## 2026-08-25 — Phase C3 Runtime Semantic Retrieval (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Implement runtime semantic retrieval taking a conversation text, calculating cosine similarity against the offline index, filtering by a configured threshold, and returning a strictly typed and ranked candidate list.
- **Used:** Wrote `src/ahoum_assignment/semantic_retriever.py` to embed incoming text dynamically and rank indexed vectors, utilizing `lru_cache` to keep the embedding index and catalogue lazily loaded in memory. Implemented `scripts/retrieve_semantic.py` for direct CLI testing with `--text`, `--file`, and JSON output flags.
- **Deliberately not implemented:** Did not send the raw conversation text to logs (unless explicitly requested by outputting the JSON manually), and strictly avoided LLM API calls.
- **Verification command:** `.venv/bin/python scripts/retrieve_semantic.py --text "I am feeling very happy today" --top-k 3` and `.venv/bin/python -m pytest tests/test_semantic_retriever.py`

## 2026-08-25 — Phase C4 Keyword and Category Routing (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Build a transparent, version-controlled keyword router to complement the semantic index. Map explicit phrases to categories, prevent false positives via boundary detection and negative keywords, score observable matches based on explicit configurable weights, and firmly exclude non-observable entries (like medical diagnoses) regardless of keyword overlap.
- **Used:** Wrote `config/routing_rules.toml` containing weights, positive/negative keywords, and multi-lingual examples. Wrote `src/ahoum_assignment/keyword_router.py` to compile highly specific word-boundary regular expressions and compute transparent, capped scoring based on matches. Wrote tests validating false-positive prevention, case insensitivity, deterministic ordering, and the guaranteed exclusion of medical terms. Created `docs/keyword_routing_rules.md` documenting the architecture. 
- **Deliberately not implemented:** Did not build a naive substring matcher (to avoid words inside other words). Avoided mapping ambiguous or weak keywords, deferring those strictly to the semantic engine.
- **Verification command:** `.venv/bin/python -m pytest tests/test_keyword_router.py`

## 2026-08-25 — Phase C5 Hybrid Facet Retrieval (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Implement hybrid retrieval merging semantic and keyword candidates. Apply configurable normalization weights, de-duplicate exact matched facets, enforce deterministic tie-breakers, and explicitly prevent the shortlist from returning arbitrary results when zero facets clear the threshold limits. Provide extensive JSON and human-readable output formats via a command-line script.
- **Used:** Wrote `src/ahoum_assignment/hybrid_retriever.py` to union the outputs of `semantic_retriever` and `keyword_router`, deduplicating via `facet_id` and calculating the configurable `hybrid_score`. Handled robust diagnostics aggregations mapping exact overlap numbers and exclusion reasons. Created `scripts/retrieve_facets.py` handling `--human` and `--output` flags natively. Added tests validating weight impacts, tie-breaking, empty shortlists, and cross-route duplications.
- **Verification command:** `.venv/bin/python scripts/retrieve_facets.py --text "I strictly budget my money." --human` and `.venv/bin/python -m pytest tests/test_hybrid_retriever.py`

## 2026-08-25 — Phase C Handoff and Review (Antigravity)

- **Tool/model:** Gemini 3.1 Pro (High)
- **Prompt summary:** Run a sanity check covering semantic, keyword, and hybrid retrieval across 5 varied development conversation queries. Ensure clear filtering of hallucination bait and non-observables, document findings, update limitations, and prepare the environment for the Phase D LLM scoring handoff.
- **Used:** Wrote `scripts/run_demo.py` and `data/examples/dev_conversations.json` containing the 5 required checks (emotional regulation, work/communication, money/risk, low evidence, and hallucination bait). Aligned hybrid threshold configurations to uniformly default to `0.3` across scripts for test consistency. Appended known limitations to `README.md`, recorded the hybrid architecture decision to `DECISIONS.md`, and logged a genuine debugging insight into `DEBUGGING.md` detailing how the observability filter safely and silently blocked valid `finance_risk` keywords from progressing into the LLM shortlist.
- **Verification command:** Ran `python scripts/run_demo.py` safely without an internet connection or external APIs using the offline FakeDeterministicEmbedder, confirming that the 20 hallucination bait facets were intercepted by the keyword router.

## 2026-08-25 — Phase D1–D6 Batched LLM Scoring (Antigravity)

### D1 — Provider Abstraction
- **Created:** `src/ahoum_assignment/providers/base.py` (BaseProvider protocol, ProviderError with secret redaction, ProviderResponse dataclass), `providers/ollama.py` (local Ollama adapter), `providers/openai_compatible.py` (cloud adapter for Groq/NVIDIA/OpenRouter), `providers/factory.py` (config-based routing).
- **Tests:** `tests/test_providers.py` — provider selection, missing-key errors, secret redaction, metadata capture.

### D2 — Scoring Prompt and Response Contract
- **Created:** `src/ahoum_assignment/scoring_prompt.py` containing the full evidence-grounded prompt template and `ScoringResponseItem`/`ScoringBatchResponse` Pydantic models.
- **Tests:** `tests/test_scoring_prompt.py` — batch limits, anchor inclusion, inference prohibition, facet-ID retention, retry prompt construction.

### D3 — Batch Orchestration
- **Created:** `src/ahoum_assignment/batching.py` (deterministic split), `src/ahoum_assignment/scoring_service.py` (orchestration with provider calls, retry, dry-run).
- **Created:** `scripts/score_conversation.py` CLI with --text, --file, --dry-run, --human, --output flags.
- **Tests:** `tests/test_scoring_pipeline.py` — 1/5/6/20+ facet batching, dry-run zero calls, mock scoring, partial failure, deterministic ordering.

### D4 — Response Parsing and Validation
- **Created:** `src/ahoum_assignment/response_parser.py` (three-stage JSON extraction), `src/ahoum_assignment/response_validator.py` (schema + facet-ID + evidence grounding).
- **Tests:** `tests/test_response_validation.py` — valid/fenced/prose JSON, malformed JSON, missing/duplicate/extra IDs, invalid scores, abstention-with-score, confidence range, invented evidence.

### D5 — Result Aggregation
- **Created:** `src/ahoum_assignment/result_aggregator.py` and `src/ahoum_assignment/result_renderer.py`.
- **Tests:** All success/partial failure/all failure/mixed/stable ordering/no-score-for-abstention tests in `test_scoring_pipeline.py`.

### D6 — Red-Team and Handoff
- **Created:** `tests/test_redteam.py` with 8 red-team tests covering: medical bait, biographical bait, external-behavior bait, malformed-then-fixed provider, invented evidence rejection, batch crash isolation, abstention-only provider, dry-run, and prompt key safety.
- **Verification:** `python -m pytest tests/` (116 tests, all pass). Full pipeline dry-run from preprocess through scoring verified.

### Deliberately not implemented
- No real LLM calls in tests. All provider interactions use mock classes.
- No API keys stored anywhere in the repository.

## 2026-08-25 — Phase E Benchmark Conversations and Human Reference Set
- **E1**: Designed benchmark schemas (`BenchmarkConversation`, `ReferenceLabel`) and documented annotation guidelines in `docs/benchmark_annotation_guide.md`.
- **E2**: Authored 12 short conversational snippets explicitly testing distinct safety and retrieval challenges, such as ambiguous wording, quoted speech, sarcasm, code-switching, financial decisions, and hallucination bait.
- **E3**: Extracted 25 representative facets across diverse observational dimensions. Manually authored sparse, proposed reference labels (8 labels) mapping scenarios directly to abstention or exact evidence text.
- **E4**: Created `scripts/review_labels.py` for project owners to traceably accept, edit, or reject labels, outputting to a separate `reference_labels_reviewed.jsonl`. Added this tool to the unified interactive CLI (`ahoum`).
- **E5/E6**: Confirmed benchmark dataset passes validation and tests constraints. Verified no proposed labels claim unearned human-approval.

