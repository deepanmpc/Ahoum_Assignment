# Ahoum AI/ML Engineer Assignment

An abstention-aware baseline for evaluating conversation text against a large,
heterogeneous facet catalogue.

## Current status

Phase A is complete: repository structure, stable result contracts, configuration, a no-network diagnostic command, and tests are in place.

Phase A does not yet implement:
- preprocessing
- embeddings
- retrieval
- LLM scoring
- benchmark evaluation

## Architecture target

```text
raw facet CSV -> enriched catalogue -> hybrid retrieval -> small LLM batches
                                               |              |
                                   semantic + keywords   score or abstain
```

Only a small set of relevant, conversation-observable facets will be sent to
the scorer. The system will never send all facets in one prompt.

## Data Preprocessing & Catalogue Generation

Run the deterministic preprocessing pipeline to normalize and classify the raw data:
```bash
python scripts/preprocess_facets.py
```
**Output Locations:**
- Catalogue: `data/processed/facet_catalogue.csv`
- Audit Report: `data/processed/facet_audit.md`
- Semantic Vectors: `data/processed/facet_embeddings.npz`
- Index Metadata: `data/processed/facet_index_metadata.json`

Once the catalogue is generated, build the semantic search index:
```bash
python scripts/build_index.py
```

### Phase C: Hybrid Retrieval

Run the unified hybrid retriever combining semantic vectors and keyword routing to produce a highly relevant shortlist of observable traits for scoring:
```bash
python scripts/retrieve_facets.py --text "I strictly budget my money." --human
```

The output conforms to the strictly typed `RetrievalResult` Pydantic model (JSON by default, or `--human` for debugging):
```json
{
  "conversation_id": "uuid",
  "candidate_count": 1,
  "candidates": [
    {
      "facet_id": "...",
      "hybrid_score": 0.82,
      "inclusion_reason": "Retrieved via both paths...",
      "...": "..."
    }
  ],
  "diagnostics": {
    "semantic_candidate_count": 1,
    "keyword_candidate_count": 1,
    "duplicate_candidate_count": 1
  }
}
```

**Catalogue Summary:**
- Total raw entries processed: 399
- Output enriched entries: 399 (Malformed entries are flagged and retained, never silently dropped)
- Observability logic strictly filters external, medical, and sensitive traits from conversational scoring, keeping 31 conversational traits anchored securely and delegating edge cases to human review.

**Known Limitations:**
- The Phase B taxonomy relies on a strict, rule-based keyword matching system rather than LLM interpretation. While this guarantees safe default behavior (e.g., rejecting ambiguous facets as `uncertain`), it requires manual review and overrides via `data/raw/facet_overrides.csv` for advanced edge cases and highly domain-specific terms.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/doctor.py doctor
python scripts/preprocess_facets.py
python -m pytest
```

`doctor` validates local configuration only. It does not contact Ollama,
Groq, NVIDIA NIM, OpenRouter, or any other model provider.

## Configuration and secrets

Copy `.env.example` to `.env` only when a future phase needs a hosted provider.
Never commit `.env` or provider API keys. The default configuration names a
Qwen model through Ollama; Phase A makes no model calls.

## Planned commands

Later phases will add reproducible commands for preprocessing, index building,
retrieval, scoring, and evaluation.

## Mandatory evidence

- [PROMPT_LOG.md](PROMPT_LOG.md)
- [DECISIONS.md](DECISIONS.md)
- [DEBUGGING.md](DEBUGGING.md)
- `data/processed/facet_catalogue.csv` (generated in Phase B)
- benchmark conversations, reference labels, and generated results (later phases)

## Phase D Prerequisites
- Ensure the offline embedding index is rebuilt (`scripts/build_index.py`) if the catalogue or configuration changes.
- The pipeline expects `scripts/retrieve_facets.py` to yield a strict, bounded JSON list of eligible facets ready for LLM batch scoring.

## Known Limitations

- **Taxonomy Stringency**: Many high-risk or external domains (like `finance_risk` or `health_medical`) are strictly restricted via deterministic observability rules. Perfectly clear text about budgeting will still not surface finance facets if they are universally marked `uncertain` in the catalogue.
- **Rule Curation**: The keyword router requires manual curation of `routing_rules.toml` to capture domain-specific jargon effectively.
- **Offline Index Size**: The semantic index currently loads fully into RAM. For a catalogue of < 10,000 facets, this is completely trivial, but may require a dedicated vector database if the catalogue scales to millions of traits.
