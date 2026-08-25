# Ahoum — Abstention-Aware Conversation Facet Scorer

This system evaluates short conversation text against a large, heterogeneous
facet catalogue (~400 entries, architected for 5,000+). It retrieves only
relevant, conversation-observable facets via hybrid semantic + keyword routing,
scores them in small LLM batches of five, enforces structured JSON output with
evidence grounding, and abstains rather than fabricating scores when the
conversation provides no evidence. The default model is an open-weight
Qwen 2.5 3B-Instruct (≤4B) served locally through Ollama.

## Assignment Constraints Addressed

| Constraint | Implementation |
|---|---|
| Open-weight model ≤16B | Default: `qwen2.5:3b-instruct` via Ollama (3B). Cloud alternatives via Groq/NVIDIA NIM use ≤16B open-weight models only. |
| No one-shot prompt over all facets | Hybrid retrieval shortlists ~20–25 candidates; LLM sees batches of 5, never all 399. |
| Scalable to 5,000 facets | Offline embedding index + top-K retrieval. LLM call count scales with shortlist, not catalogue size. |
| Abstention behavior | Explicit `insufficient_evidence` status with `null` score. A score of 3 is never used as a proxy for "unknown." |
| Hallucination-bait testing | 3+ benchmark conversations containing medical, biographical, and religious bait. Non-observable facets are excluded before LLM scoring. |

## Architecture

```text
raw CSV (399 facets)
  → enriched catalogue (normalize, classify, anchor)
    → semantic index (offline embeddings, cosine similarity)
    + keyword router (TOML rules, word-boundary regex)
      → hybrid shortlist (~20–25 observable candidates)
        → batches of 5
          → LLM call (structured JSON prompt)
            → 3-stage JSON parser + schema validation
              → evidence-quote grounding check
                → retry once if malformed
                  → aggregation (score / abstain / error per facet)
                    → evaluation metrics + Markdown report
```

## Repository Layout

```
├── config.toml                  # Model, retrieval, scoring parameters
├── config/routing_rules.toml    # Keyword routing rules
├── data/
│   ├── raw/                     # Untouched source CSV + override files
│   ├── processed/               # Generated catalogue, index (gitignored)
│   ├── examples/                # Benchmark conversations, labels, facets
│   └── outputs/                 # Evaluation run artifacts (gitignored)
├── src/ahoum_assignment/        # Core library
│   ├── preprocessing.py         # Normalize, classify, anchor
│   ├── taxonomy_rules.py        # Rule-based category assignment
│   ├── semantic_index.py        # Offline embedding index builder
│   ├── semantic_retriever.py    # Runtime cosine retrieval
│   ├── keyword_router.py        # TOML-driven keyword matching
│   ├── hybrid_retriever.py      # Merge semantic + keyword candidates
│   ├── scoring_service.py       # Batch orchestration + retry
│   ├── response_parser.py       # 3-stage JSON extraction
│   ├── response_validator.py    # Schema + evidence grounding
│   ├── result_aggregator.py     # Final scored/abstained/error rollup
│   ├── providers/               # Ollama, Groq, NVIDIA NIM, OpenRouter
│   ├── evaluation/              # Metrics, comparison, models
│   └── logging_utils.py         # Privacy-safe redaction
├── scripts/                     # CLI entry points
├── tests/                       # 133 unit + integration tests
├── docs/                        # Architecture, protocol, contracts
├── README.md
├── PROMPT_LOG.md                # AI supervision evidence
├── DECISIONS.md                 # Engineering trade-offs
└── DEBUGGING.md                 # Real defects found and fixed
```

## Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (dev tools included)
pip install -e ".[dev]"

# 3. (Optional) Install sentence-transformers for real embeddings
pip install -e ".[embeddings]"
# Without this, the system uses FakeDeterministicEmbedder for testing.

# 4. (Optional) Cloud provider — copy and edit .env.example
cp .env.example .env
# Set AHOUM_MODEL_PROVIDER, AHOUM_MODEL_NAME, and the relevant API key.

# 5. (Optional) Local Ollama
# Install Ollama (https://ollama.ai), then:
ollama pull qwen2.5:3b-instruct
```

**No-key mock mode:** Every command below works without Ollama, cloud keys, or
`sentence-transformers` installed. The system falls back to
`FakeDeterministicEmbedder` and `--provider mock` automatically.

## Run Instructions

```bash
# Interactive menu (all operations)
ahoum

# --- Individual commands ---

# Preprocessing (raw CSV → enriched catalogue)
python scripts/preprocess_facets.py

# Semantic index build
python scripts/build_index.py

# Semantic retrieval
python scripts/retrieve_semantic.py --text "I am very careful with my work" --top-k 5

# Keyword retrieval
python scripts/retrieve_keywords.py --text "I budget strictly every month"

# Hybrid retrieval (recommended)
python scripts/retrieve_facets.py --text "I stayed calm during the argument" --human

# Mock scoring (no LLM needed)
python scripts/score_conversation.py --text "I stayed calm during the argument" --dry-run --human

# Live scoring (requires Ollama or cloud provider)
python scripts/score_conversation.py --text "I stayed calm during the argument" --human

# Benchmark evaluation (mock provider)
python scripts/evaluate.py --include-proposed --provider mock --retrieval-mode hybrid

# Retrieval ablation study
python scripts/run_ablation.py

# Evaluation report generation
python scripts/generate_report.py --run-dir data/outputs/<run_id>

# Full test suite (133 tests)
python -m pytest tests/ -v

# Deterministic smoke test (raw CSV → scored output, no network)
python scripts/smoke_test.py
```

## Example Output

A sanitized structured result from a single conversation scoring:

```json
{
  "conversation_id": "conv-demo",
  "scored_count": 1,
  "insufficient_evidence_count": 1,
  "error_count": 0,
  "facet_scores": [
    {
      "facet_id": "a1b2c3d4e5f6",
      "facet_normalized": "speaks calmly under pressure",
      "status": "scored",
      "score_1_to_5": 4,
      "confidence_0_to_1": 0.85,
      "evidence": "I stayed calm during the argument",
      "reason": "Direct behavioral evidence of composure"
    },
    {
      "facet_id": "f6e5d4c3b2a1",
      "facet_normalized": "prefers written communication",
      "status": "insufficient_evidence",
      "score_1_to_5": null,
      "confidence_0_to_1": 0.0,
      "evidence": null,
      "reason": "No evidence of communication preference in text"
    }
  ]
}
```

Non-observable facets (e.g., "Has asthma", "Blood type") are excluded during
retrieval and never reach the LLM. Their exclusion is recorded in
`RetrievalResult.diagnostics`.

## Evaluation Summary

- **Benchmark size**: 12 conversations, 25 representative facets, 8 sparse
  proposed labels.
- **Label-review status**: Labels are proposed (AI-generated). The owner review
  tool (`scripts/review_labels.py`) exists but labels have not been formally
  accepted. Metrics computed with `--include-proposed` are development-only.
- **Retrieval ablation** (`scripts/run_ablation.py`):
  - Semantic-only Recall@5: 0.4 | Keyword-only: 0.0 | Hybrid: 0.4
  - Keyword-only achieved 0% recall because benchmark phrasing does not
    literally match routing-rule keywords. This confirms the need for semantic
    retrieval alongside explicit rules.
- **Abstention/hallucination-bait**: Non-observable facets (medical, biographical,
  religious) are structurally excluded before LLM scoring. The system never
  scores what it cannot observe.
- **All evaluation artifacts** are stored in `data/outputs/<run_id>/` as
  immutable JSON.

> **Note**: All results shown above use a mock provider. Live model results
> require a running Ollama instance or cloud API key. Mock and live results are
> never mixed in the same evaluation run.

## Scaling to 5,000 Facets

The architecture separates offline work (done once) from online work (done per
conversation):

| Component | Current (399) | At 5,000 | Bottleneck? |
|---|---|---|---|
| Preprocessing | ~1s | ~10s | No |
| Embedding index build | ~5s (fake) / ~60s (real) | ~10 min | No (offline, one-time) |
| Index load | NumPy in-memory | NumPy in-memory | No (5K × 384 float32 ≈ 7 MB) |
| Retrieval | Brute-force cosine | Still viable; FAISS/Annoy for 50K+ | **First bottleneck at ~50K** |
| Shortlist size | 20–25 | 20–25 (unchanged) | No (top-K is fixed) |
| LLM batches | 4–5 calls | 4–5 calls (unchanged) | No |
| LLM latency | ~2s/batch (3B local) | Same | **Primary wall-clock cost** |

**Practical next optimizations:**
1. Replace NumPy cosine with FAISS `IndexFlatIP` (drop-in, sub-millisecond at
   50K vectors).
2. Cache embeddings for repeated conversations.
3. Use Groq/NVIDIA NIM for 10–50× faster inference than local Ollama.

## Known Limitations

1. **Taxonomy rigidity**: Rule-based classification leaves many facets as
   `uncertain`. Manual curation of `facet_overrides.csv` is required for
   domain-specific terms.
2. **Keyword recall**: The keyword router requires exact word-boundary matches.
   Pluralizations, synonyms, and slang are missed unless explicitly listed.
3. **Sparse benchmark**: 12 conversations and 8 labels are insufficient for
   statistical validity. Results are development demonstrations, not benchmarks.
4. **Proposed labels**: No labels have undergone formal human review. Do not
   treat evaluation metrics as ground-truth performance.
5. **Evidence grounding**: Quote validation uses simple substring matching. A
   paraphrased but semantically correct quote is rejected.
6. **Single-language**: No multilingual embedding or routing support beyond
   basic English.

## Submission Checklist

| Requirement | Location |
|---|---|
| Reproducible preprocessing | `scripts/preprocess_facets.py` → `data/processed/facet_catalogue.csv` |
| Raw data preserved | `data/raw/Facets Assignment.csv` (never modified) |
| Enriched catalogue | `data/processed/facet_catalogue.csv` (generated) |
| Observability/sensitivity | `src/ahoum_assignment/taxonomy_rules.py`, `facet_overrides.csv` |
| Scalable retrieval | `semantic_retriever.py`, `keyword_router.py`, `hybrid_retriever.py` |
| No all-facet one-shot | `batching.py` enforces max 5 per call |
| Batch scoring | `scoring_service.py` |
| Structured output validation | `response_parser.py`, `response_validator.py` |
| Abstention handling | `ScoreStatus.INSUFFICIENT_EVIDENCE` with `null` score |
| 10+ conversations | `data/examples/benchmark_conversations.jsonl` (12) |
| 20+ facets | `data/examples/representative_facets.csv` (25) |
| 3+ hallucination-bait | Conversations `bm-10`, `bm-11`, `bm-12` |
| Reference labels | `data/examples/reference_labels.jsonl` (8 proposed) |
| Evaluation/failure analysis | `scripts/evaluate.py`, `scripts/run_ablation.py`, `docs/failure_analysis_template.md` |
| 5,000-facet scaling | See "Scaling to 5,000 Facets" section above |
| PROMPT_LOG.md | [PROMPT_LOG.md](PROMPT_LOG.md) |
| DECISIONS.md | [DECISIONS.md](DECISIONS.md) |
| DEBUGGING.md | [DEBUGGING.md](DEBUGGING.md) |
| Incremental commits | `git log --oneline` shows 20+ focused commits across phases A–H |
| Setup/reproducibility | See "Setup" and "Run Instructions" above |

## Mandatory Evidence

- [PROMPT_LOG.md](PROMPT_LOG.md) — AI supervision and correction evidence
- [DECISIONS.md](DECISIONS.md) — Engineering trade-offs
- [DEBUGGING.md](DEBUGGING.md) — Real defects found and fixed
- [docs/submission_evidence.md](docs/submission_evidence.md) — Requirement-to-artifact mapping
