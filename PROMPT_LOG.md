# Prompt Log

This file records material AI-assisted work during the assignment. Entries are
added as work occurs, including what was retained, what was changed, and how it
was verified.

---

## Phase A — Foundation (2026-08-24)

- **Tool/model**: Gemini 3.1 Pro
- **Prompt**: Create a reproducible repository foundation for a scalable,
  abstention-aware conversation facet scorer. Include configuration, stable
  result contracts, a no-network diagnostic command, and tests.
- **Artifacts produced**: Repository scaffold, `config.toml`, `models.py`
  (Pydantic contracts for `FacetRecord`, `FacetScore`), `scripts/doctor.py`,
  `pyproject.toml`, `.gitignore`, `.env.example`.
- **Accepted**: Repository structure, TOML config loader, Pydantic contracts
  with strict `status` + nullable `score_1_to_5` abstention model.
- **Changed**: AI initially proposed standard-library `dataclasses` for
  contracts. Changed to Pydantic for field-level and model-level validation
  enforcement (e.g., preventing a scored result with no numeric score).
- **Verification**: `python scripts/doctor.py doctor`, `python -m pytest tests/`.
- **Commits**: Initial foundation commits.

---

## Phase B — Preprocessing & Taxonomy (2026-08-25)

### B1: Data Audit
- **Prompt**: Inspect raw CSV without changing it. Produce a reproducible audit
  and define the enriched catalogue schema.
- **Artifacts**: `data/processed/facet_audit.json`, `facet_audit.md`,
  `docs/facet_catalogue_schema.md`.
- **Accepted**: Schema definition with 17 columns including observability,
  sensitivity, and anchor fields.

### B2: Preprocessing Pipeline
- **Prompt**: Implement deterministic preprocessing. Normalize whitespace,
  remove numbering prefixes, detect malformed entries.
- **Artifacts**: `src/ahoum_assignment/preprocessing.py`,
  `scripts/preprocess_facets.py`.
- **Accepted**: MD5-based stable ID generation, regex normalization, malformed
  detection. No LLM usage for classification.
- **Verification**: `python scripts/preprocess_facets.py` produces identical
  output across runs (`cmp` verified).

### B3: Taxonomy & Observability
- **Prompt**: Build a rule-based taxonomy classifying facets into categories
  (health_medical, external_biographical, conversational_trait, etc.) with an
  editable override CSV.
- **Artifacts**: `src/ahoum_assignment/taxonomy_rules.py`,
  `data/raw/facet_overrides.csv`.
- **Changed**: AI's initial keyword set included generic words (`count`, `level`,
  `participation`, `pain`) that caused false positives. "Subscription count" was
  classified as `health_medical` due to the word "count." Removed these generic
  keywords and added regression tests.

### B4: Anchors & Scoring Definitions
- **Prompt**: Generate scoring anchors (1, 3, 5) for observable facets only.
  Non-observable facets must remain unanchored.
- **Artifacts**: `src/ahoum_assignment/anchor_rules.py`,
  `data/raw/anchor_overrides.csv`.
- **Accepted**: Template-based anchor generation by facet type. Override CSV for
  manual corrections.

### B5: Review & Handoff
- **What was changed**: Reviewed sampled catalogue rows. Found "Subscription
  count" incorrectly classified as medical. Fixed the regex rules, not the output
  CSV.
- **Verification**: `python -m pytest tests/` (all pass after fix).

---

## Phase C — Hybrid Retrieval (2026-08-25)

### C1: Retrieval Contracts
- **Prompt**: Define Pydantic models for `RetrievalCandidate`, `RetrievalResult`
  with strict invariants (no non-observable candidates, no duplicate IDs).
- **Artifacts**: Extended `models.py`, `docs/retrieval_contracts.md`.

### C2: Semantic Index
- **Prompt**: Build offline embedding index with abstract `Embedder` protocol.
- **Artifacts**: `semantic_index.py`, `embeddings.py` (with
  `FakeDeterministicEmbedder` for tests).
- **Changed**: AI suggested requiring `sentence-transformers` as a hard
  dependency. Moved to optional `[embeddings]` group to avoid 3GB PyTorch
  download in CI/test environments.

### C3: Runtime Semantic Retrieval
- **Artifacts**: `semantic_retriever.py`, `scripts/retrieve_semantic.py`.

### C4: Keyword Router
- **Prompt**: Build TOML-driven keyword router with word-boundary regex,
  negative exclusions, and category scoring.
- **Artifacts**: `keyword_router.py`, `config/routing_rules.toml`.

### C5: Hybrid Merge
- **Artifacts**: `hybrid_retriever.py`, `scripts/retrieve_facets.py`.
- **Verification**: Ablation study later confirmed hybrid > semantic-only >
  keyword-only on recall.

---

## Phase D — Batched LLM Scoring (2026-08-25)

### D1: Provider Abstraction
- **Artifacts**: `providers/base.py`, `providers/ollama.py`,
  `providers/openai_compatible.py`, `providers/factory.py`.
- **Key design**: `ProviderError.safe_message` strips API keys from error output.

### D2: Scoring Prompt
- **Artifacts**: `scoring_prompt.py` with `ScoringResponseItem` schema.
- **Changed**: AI's initial prompt template did not explicitly prohibit
  inference beyond the conversation text. Added strict prohibition clause:
  "Do NOT infer traits not directly observable in the text."

### D3: Batch Orchestration
- **Artifacts**: `batching.py`, `scoring_service.py`,
  `scripts/score_conversation.py`.

### D4: Response Parsing & Validation
- **Artifacts**: `response_parser.py` (3-stage JSON extraction),
  `response_validator.py` (schema + evidence grounding).

### D5: Result Aggregation
- **Artifacts**: `result_aggregator.py`, `result_renderer.py`.

### D6: Red-Team Testing
- **Artifacts**: `tests/test_redteam.py` — 8 tests covering medical bait,
  biographical bait, invented evidence rejection, batch crash isolation.
- **Verification**: `python -m pytest tests/test_redteam.py` (all pass).

---

## Phase E — Benchmark & Reference Labels (2026-08-25)

- **Prompt**: Create 10+ adversarial conversations, 20+ representative facets,
  sparse proposed labels.
- **Artifacts**: `data/examples/benchmark_conversations.jsonl` (12),
  `data/examples/representative_facets.csv` (25),
  `data/examples/reference_labels.jsonl` (8 proposed).
- **Tool**: `scripts/review_labels.py` for traceable human review.
- **Important**: Labels remain `proposed` status. No claim of human review.

---

## Phase F — Evaluation & Ablation (2026-08-25)

- **Artifacts**: `scripts/evaluate.py`, `scripts/run_ablation.py`,
  `scripts/generate_report.py`, `src/ahoum_assignment/evaluation/`.
- **Results**: Mock provider evaluation over 12 conversations, 8 labels.
  Retrieval ablation confirmed hybrid > semantic > keyword.
- **Verification**: `python scripts/evaluate.py --include-proposed --provider mock`.

---

## Phase G — Reliability & Release Hardening (2026-08-25)

- **G1**: `scripts/smoke_test.py` — deterministic end-to-end test (raw CSV →
  scored output, no network).
- **G2**: `config.py` validation — `batch_size > 0`, `top_k > 0`, weights sum
  to 1.0.
- **G3**: `tests/integration/test_fault_injection.py` — timeout, malformed JSON,
  missing facets.
- **G4**: `logging_utils.py` — secret redaction, git-ignored debug artifacts.
- **G5**: Two genuine debugging cases documented in `DEBUGGING.md`.
- **G6**: Release rehearsal — 133 tests pass.

---

## Phase H — Documentation & Submission (2026-08-25)

- **Tool/model**: Claude Opus 4.6
- **Prompt**: Rewrite all mandatory documentation for evaluator readability.
  Map every assignment requirement to code/artifact.
- **Artifacts**: Complete rewrite of `README.md`, `DECISIONS.md`,
  `PROMPT_LOG.md`, `docs/submission_evidence.md`,
  `docs/operational_failure_modes.md`.
- **Verification**: `python -m pytest tests/`, `python scripts/smoke_test.py`,
  verified all README commands.

---

## What AI Got Wrong / What I Corrected

### 1. Generic Taxonomy Keywords Caused False-Positive Medical Classification

**AI suggestion**: The initial `taxonomy_rules.py` keyword list included generic
words like `count`, `level`, `participation`, and `pain` as indicators of
`health_medical` facets.

**Why it was wrong**: "Subscription count" was classified as `health_medical`
because it contains the word "count." "Pain point analysis" (a business term)
would similarly be misclassified. These are false positives that would
incorrectly block legitimate conversational facets from scoring.

**Correction**: Removed generic keywords from the medical category. Added
word-boundary constraints and negative keyword exclusions. Added regression tests
in `tests/test_taxonomy.py` verifying that "Subscription count" is NOT classified
as medical.

**Verification**: `python -m pytest tests/test_taxonomy.py` — the specific
test case passes after the fix.

### 2. Mock Provider Evidence Quote Failed Grounding Validation

**AI suggestion**: The smoke test `SmokeMockProvider` returned
`"evidence_quote": "smoke test evidence"` as a hardcoded quote for every facet.

**Why it was wrong**: The `response_validator.py` checks that the evidence quote
is a substring of the actual conversation text. The string `"smoke test evidence"`
does not appear anywhere in the test conversation `"I am very careful when I work"`.
This caused all mock-scored facets to fail validation and be marked as `ERROR`
instead of `SCORED`, making the smoke test incorrectly report zero scored facets.

**Correction**: Changed the mock evidence quote to `"very careful"` — a substring
that actually appears in the test conversation text.

**Verification**: `python scripts/smoke_test.py` — now reports 3 scored facets
instead of 0 errors. The fix is visible in the commit history for
`scripts/smoke_test.py`.

## Phase I — Final Release Verification (2026-08-25)

- **Tool/model**: Gemini 3.1 Pro
- **Prompt I1**: Verify project reproducibility from a clean clone.
- **Action**: Cloned project to `/tmp/ahoum_clean_test`, executed the full data pipeline, retrieval scripts, and mock evaluation.
- **Correction**: `scripts/doctor.py` initially failed because my manual testing cleanup (`rm -rf data/outputs`) deleted the `.gitkeep` file. Confirmed that `.gitkeep` already exists in git, so a standard `git clone` will not suffer this issue. No code changes were needed.
- **Verification**: `docs/final_clean_run.md` proves 100% success on the full suite (133 tests).
