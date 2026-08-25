# Submission Evidence Index

This document maps each assignment requirement to the implementing code,
generated artifacts, tests, commands, and documentation.

---

## Requirement Mapping

| # | Requirement | Implementation | Artifact | Test | Command | Docs |
|---|---|---|---|---|---|---|
| 1 | Reproducible preprocessing | `preprocessing.py`, `taxonomy_rules.py`, `anchor_rules.py` | `data/processed/facet_catalogue.csv` | `test_preprocessing.py`, `test_taxonomy.py`, `test_anchors.py` | `python scripts/preprocess_facets.py` | `docs/facet_catalogue_schema.md` |
| 2 | Raw facet preservation | `data/raw/Facets Assignment.csv` | File unchanged since initial commit | — | `git log data/raw/` | README §Setup |
| 3 | Enriched catalogue | `preprocessing.py` → 17-column CSV | `data/processed/facet_catalogue.csv` | `test_preprocessing.py` | `python scripts/preprocess_facets.py` | `docs/facet_catalogue_schema.md` |
| 4 | Observability/sensitivity | `taxonomy_rules.py`, `facet_overrides.csv` | `conversation_observable` column | `test_taxonomy.py`, `test_retrieval_contracts.py` | — | `DECISIONS.md: D2` |
| 5 | Scalable retrieval/routing | `semantic_retriever.py`, `keyword_router.py`, `hybrid_retriever.py` | — | `test_semantic_retriever.py`, `test_keyword_router.py`, `test_hybrid_retriever.py` | `python scripts/retrieve_facets.py --text "..." --human` | `docs/retrieval_contracts.md` |
| 6 | No all-facet one-shot | `batching.py` (max 5 per batch) | — | `test_scoring_pipeline.py` | — | `DECISIONS.md: D5` |
| 7 | Batch scoring | `scoring_service.py` | — | `test_scoring_pipeline.py`, `test_fault_injection.py` | `python scripts/score_conversation.py --text "..." --human` | `docs/scoring_prompt_contract.md` |
| 8 | Structured output validation | `response_parser.py`, `response_validator.py` | — | `test_response_validation.py` | — | `docs/structured_output_recovery.md` |
| 9 | Abstention handling | `ScoreStatus` enum, `FacetScore` validator | — | `test_models.py`, `test_redteam.py` | — | `DECISIONS.md: D3` |
| 10 | 10+ benchmark conversations | — | `data/examples/benchmark_conversations.jsonl` (12) | `test_benchmark_schema.py` | — | `docs/benchmark_annotation_guide.md` |
| 11 | 20+ representative facets | — | `data/examples/representative_facets.csv` (25) | — | — | — |
| 12 | 3+ hallucination-bait cases | — | Conversations `bm-10`, `bm-11`, `bm-12` | `test_redteam.py` | — | `docs/benchmark_annotation_guide.md` |
| 13 | Reference labels + reviewer status | `benchmark_models.py` | `data/examples/reference_labels.jsonl` (8 proposed) | `test_review_workflow.py` | `python scripts/review_labels.py` | `docs/reference_label_review.md` |
| 14 | Evaluation/failure analysis | `evaluation/`, `scripts/evaluate.py` | `data/outputs/<run_id>/evaluation_summary.json` | `test_evaluation_metrics.py` | `python scripts/evaluate.py --include-proposed --provider mock` | `docs/evaluation_protocol.md`, `docs/failure_analysis_template.md` |
| 15 | 5,000-facet scale discussion | — | — | — | — | `README.md: "Scaling to 5,000 Facets"`, `DECISIONS.md: D6` |
| 16 | PROMPT_LOG.md | — | `PROMPT_LOG.md` | — | — | — |
| 17 | DECISIONS.md | — | `DECISIONS.md` | — | — | — |
| 18 | DEBUGGING.md | — | `DEBUGGING.md` | — | — | — |
| 19 | Incremental commit history | — | `git log --oneline` (20+ commits) | — | `git log --oneline` | — |
| 20 | Setup/reproducibility | `pyproject.toml`, `config.toml` | — | 133 tests | `python -m pytest tests/`, `python scripts/smoke_test.py` | `README.md: Setup` |

---

## Repository State Audit

> **📂 Note on Results Location**: All dynamic outputs (such as live evaluation reports, batch-scoring payloads, and diagnostic logs) are generated and saved strictly inside the `data/outputs/` folder in timestamped subdirectories. This folder is gitignored to prevent commit bloat, but evaluators can find all generated artifacts there immediately after running `scripts/evaluate.py`.

| Check | Status |
|---|---|
| Raw input present and unchanged | ✅ `data/raw/Facets Assignment.csv` tracked, never modified |
| Generated outputs for demo included | ✅ `data/processed/facet_audit.json`, `facet_audit.md` tracked |
| Temporary/debug outputs ignored | ✅ `data/outputs/*` and `debug_artifacts/` gitignored |
| No `.env` or secrets tracked | ✅ Only `.env.example` tracked; `.env` gitignored |
| No large model artifacts committed | ✅ `facet_embeddings.npz` gitignored; index is regenerated |
| README commands refer to real scripts | ✅ All scripts in `scripts/` exist and are executable |
| Markdown links work | ✅ All links reference existing files |
| Git history is incremental | ✅ 20+ commits with focused messages (feat/fix/test/docs) |
| No API keys in tracked files | ✅ Grep for common key patterns returns no matches |
| Mock vs live clearly distinguished | ✅ `--provider mock` is default; README states all shown results use mock |
| Proposed vs reviewed labels distinguished | ✅ `reviewer_status` field; `--include-proposed` flag required |
