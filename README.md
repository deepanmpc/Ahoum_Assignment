# Ahoum AI/ML Engineer Assignment

This is a scalable conversation-to-facet scoring baseline. It preprocesses a heterogeneous raw facet CSV into an enriched catalogue, safely filtering unobservable traits. At runtime, it uses hybrid retrieval (semantic embeddings plus keyword/taxonomy routing) to create a shortlist of relevant observable facets. Finally, it sends only this shortlist to the LLM in small batches, returning structurally validated scores or abstentions (with confidence and evidence grounding) for each facet.

## Architecture

```text
Raw facet CSV
  → preprocessing and facet catalogue enrichment
  → semantic embedding index + keyword/taxonomy routing
  → hybrid shortlist of relevant observable facets
  → batches of up to 5 facets
  → Qwen scoring provider
  → JSON validation, retry, evidence checking
  → aggregated results and evaluation
```

- The system does not send all 399 facets in one prompt.
- Only retrieved, conversation-observable facets are candidates for scoring.
- Unsupported evidence produces `insufficient_evidence` or `not_observable`, not a fabricated score.
- Default local model route is Ollama with an open-weight Qwen model <=4B.
- Optional cloud provider routing is configurable and requires environment keys.

## Repository Contents

- `data/raw/` — original facet CSV and manual override files.
- `data/processed/` — generated enriched catalogue, audit report, and semantic index artifacts.
- `data/examples/` — benchmark conversations, reference labels, and representative facets.
- `data/outputs/` — generated retrieval, scoring, and evaluation results.
- `scripts/` — runnable pipeline commands (preprocessing, indexing, retrieval, evaluation).
- `tests/` — 133 unit, integration, and smoke-test fixtures.
- `docs/` — architecture, decisions, debugging, failure modes, and submission evidence.

## Setup

```bash
git clone https://github.com/deepanmpc/Ahoum_Assignment.git
cd Ahoum_Assignment
python3 -m venv .venv
source .venv/bin/activate
pip install -q -e '.[dev]'
```

**Optional Provider Setup (for live models):**
```bash
cp .env.example .env
```
- `.env` is optional for mock mode.
- Never commit `.env`.
- Ollama/local or cloud credentials are needed only for configured live scoring.
- Mock mode works natively without API keys or external network requests.

## Quick Start

```bash
python scripts/smoke_test.py
```
This single command verifies preprocessing, semantic index building, hybrid retrieval, mock batched scoring, structured validation, and final aggregation without requiring a live model or API key.

## Full Verification Commands

```bash
python scripts/doctor.py doctor
python scripts/preprocess_facets.py
python scripts/build_index.py
python scripts/retrieve_semantic.py --text "I strictly budget my money" --top-k 5
python scripts/retrieve_keywords.py --text "I strictly budget my money"
python scripts/retrieve_facets.py --text "I strictly budget my money" --human
python scripts/score_conversation.py --text "I strictly budget my money" --dry-run
python scripts/evaluate.py --include-proposed --provider mock --retrieval-mode hybrid
python scripts/smoke_test.py
python -m pytest tests/ -v
```

*Command Purposes:*
- **doctor**: Diagnoses environment config and provider state.
- **preprocess_facets**: Deterministically converts raw CSV into the enriched catalogue.
- **build_index**: Builds the offline L2-normalized numpy embedding index.
- **retrieve_semantic**: Searches the index using cosine similarity.
- **retrieve_keywords**: Evaluates exact word-boundary taxonomy rules.
- **retrieve_facets**: Merges semantic and keyword routes, yielding an observable shortlist.
- **score_conversation**: Orchestrates batched LLM parsing over the shortlist.
- **evaluate**: Runs the entire pipeline over the 12-conversation benchmark.
- **smoke_test**: Validates all boundaries safely in-memory.
- **pytest**: Executes all 133 unit and integration tests.

## Generated Deliverables

The enriched facet catalogue is a mandatory output generated dynamically from the provided raw CSV. It preserves the raw facet value and is explicitly included in this repository:
- **Enriched Facet Catalogue**: [`data/processed/facet_catalogue.csv`](data/processed/facet_catalogue.csv)
- **Facet Audit Report**: [`data/processed/facet_audit.md`](data/processed/facet_audit.md)
- **Semantic Index Metadata**: [`data/processed/facet_index_metadata.json`](data/processed/facet_index_metadata.json)
- **Benchmark Conversations**: [`data/examples/benchmark_conversations.jsonl`](data/examples/benchmark_conversations.jsonl)
- **Representative Facets**: [`data/examples/representative_facets.csv`](data/examples/representative_facets.csv)
- **Reference Labels**: [`data/examples/reference_labels.jsonl`](data/examples/reference_labels.jsonl)
- **Sample Mock Scoring Output**: [`data/examples/sample_structured_scoring_output.mock.json`](data/examples/sample_structured_scoring_output.mock.json)
- **Hallucination-Bait Verification**: [`docs/hallucination_bait_verification.md`](docs/hallucination_bait_verification.md)
- **Submission Evidence Index**: [`docs/submission_evidence.md`](docs/submission_evidence.md)

*(Note: Live output runs create dynamic timestamped directories in the gitignored `data/outputs/` directory containing large structured JSON run artifacts)*.

## Model and Provider Configuration

- **Default Provider**: Local `ollama` running `qwen2.5:3b-instruct`.
- All supported models must be open-weight and <=16B parameters to comply with assignment guidelines.
- Optional hosted routes (`groq`, `nvidia`, `openrouter`) use standard environment keys (`GROQ_API_KEY`, etc.) configured in `.env`.
- Users must configure a compliant open-weight hosted model themselves in `.env` if bypassing Ollama.
- **Invariant**: The provider choice does not change retrieval logic, batching size, json schema validation, or the result aggregator.

## Evaluation Summary

All current metrics reflect the **Mock Provider** and **Proposed Reference Labels**. Live model evaluation requires a provisioned environment.
- **Scale**: 12 diverse conversations, 25 representative facets, 8 proposed sparse labels.
- **Retrieval Comparison**: The ablation study proves Semantic retrieval suffers from conceptual false-positives, Keyword retrieval suffers from 0% recall on paraphrased language, and Hybrid successfully merges both while protecting boundaries.
- **Abstention Behavior**: The mock pipeline successfully absorbs `insufficient_evidence` cases by nullifying the score struct.
- **Hallucination-Bait Verification**: 3 adversarial bait cases (medical, biographical, religious) were successfully neutralized by the retrieval engine *before* ever reaching the LLM batch prompt.

## Scaling to 5,000 Facets

The same architecture effortlessly scales to 5,000+ facets by cleanly separating offline/online responsibilities:
- **Offline Indexing**: Facet embedding/index creation happens exactly once during catalogue updates.
- **Top-K Retrieval**: The LLM only ever sees a bounded `top-k` shortlist (e.g., 20), rather than scoring all-facets.
- **Keyword Routing**: Acts as a low-latency complementary O(1)-like signal.
- **Batching**: The 20 items are sent in batches of 5 to protect context windows.
- **Caching**: Index files and models are loaded lazily and cached in RAM. Repeated conversation texts can bypass embeddings.
- **Bottlenecks**: The likely first bottleneck is model-call latency (which remains constant per conversation due to bounded top-K). At 50,000+ facets, the brute-force NumPy cosine search will become the secondary bottleneck, trivially resolved by swapping in a FAISS/ANN index.

## Known Limitations

- Short conversations often do not justify a valid behavioral score.
- The rule-based taxonomy requires manual review for highly ambiguous facets.
- Hybrid retrieval can still miss subtly relevant facets if embedding models misalign on domain-specific phrasing.
- Semantic retrieval is heavily dependent on the chosen embedding model quality.
- The small 12-conversation benchmark and sparse labels are a development demonstration, not an academic-grade evaluation suite.
- Cloud provider availability or model naming syntax may vary over time.
- Human-reviewed labels should always be preferred over AI-proposed labels for formal metric generation.

## What I Would Improve With Another Day

- Improve and manually review ambiguous taxonomy labels in the catalogue.
- Add confidence calibration testing to the scoring prompts.
- Build a larger owner-reviewed benchmark set (100+ conversations).
- Perform retrieval threshold tuning on held-out edge cases.
- Integrate FAISS `IndexFlatIP` as the default vector index to future-proof against larger catalogues.
- Add a provider latency and cost benchmarking matrix.
- Build an optional lightweight Streamlit UI or Jupyter Notebook report for human evaluators.

## Submission Evidence

- [PROMPT_LOG.md](PROMPT_LOG.md)
- [DECISIONS.md](DECISIONS.md)
- [DEBUGGING.md](DEBUGGING.md)
- [docs/submission_evidence.md](docs/submission_evidence.md)

**Mandatory Requirements Checked:**
- **A. Facet preprocessing**: `scripts/preprocess_facets.py`
- **B. Scalable architecture**: `scripts/retrieve_facets.py` & `src/ahoum_assignment/batching.py`
- **C. Batched scoring**: `scripts/score_conversation.py`
- **D. Benchmark and safety**: `data/examples/benchmark_conversations.jsonl`
- **E. Evaluation**: `scripts/evaluate.py`
- **F. Documentation**: All docs explicitly linked and verified above.
