# Hybrid Retrieval Contracts

This document outlines the strict typed contracts designed for Phase C's hybrid retrieval system. The goal of this system is to securely filter the catalog of facets down to a small, highly relevant, and strictly `conversation_observable` candidate list suitable for LLM batch scoring.

## Core Models

### 1. `ConversationInput`
Represents the incoming conversational text and metadata before any retrieval or scoring is performed.
- `conversation_id` (str): Unique identifier for the conversation.
- `text` (str): The raw text or transcript.
- `metadata` (dict): Optional conversational context.
- `language_hint` (str, optional): ISO language code hint.

### 2. `RetrievalCandidate`
Represents a single facet evaluated against the `ConversationInput`. 
**Crucial invariants:**
- **Observability**: A facet must have `conversation_observable=true` to be ranked > 0.
- **Signals**: An included candidate MUST have at least one inclusion signal (`semantic_score` or `keyword_score`).
- **Reasons**: Included candidates (rank > 0) must provide an `inclusion_reason`. Excluded candidates (rank == 0) must provide an `exclusion_reason`.

**Scoring Semantics:**
- `semantic_score`: A normalized float representing cosine similarity (or equivalent vector distance). Nullable if retrieved purely by keyword.
- `keyword_score`: A transparent, rule-based float representing exact or fuzzy keyword matches. Nullable if retrieved purely by semantic similarity.
- `hybrid_score`: The final configurable merged ranking score used to sort candidates.

### 3. `RetrievalResult`
The final payload emitted by the retrieval pipeline, ready to be passed to the LLM scoring layer.
- `conversation_id`: Connects the result back to the input.
- `candidates`: An ordered list of `RetrievalCandidate` objects. 
- **Invariants:**
  - `candidates` MUST NOT contain duplicate `facet_id`s.
  - `candidates` MUST NOT contain any facet where `conversation_observable != "true"`.
  - All candidates in the list must have `rank >= 1`.
- `retrieval_config_metadata`: Captures the configuration (e.g., weights, top_k) used for this specific retrieval run.
- `index_version`: Identifies the exact version of the embeddings/catalogue used.

### 4. `RetrievalDiagnostics`
Retains granular internal metrics explaining how the retrieval result was formed, ensuring complete transparency without bloating the primary candidate payload.
- `semantic_candidate_count`: Total facets matched purely by vector similarity.
- `keyword_candidate_count`: Total facets matched by keywords.
- `merged_candidate_count`: Total candidates after merging and deduplicating both streams.
- `excluded_non_observable_count`: Number of otherwise highly-ranked facets stripped out because they were non-observable.
- `duplicate_candidate_count`: Number of overlapping facets found by both semantic and keyword streams.
- `fallback_behavior`: String describing fallback routing if no primary candidates met the minimum threshold.

## Design Decisions
- **No Embeddings Yet**: These contracts are completely decoupled from any specific vector database or LLM provider.
- **Fail-Safe Observability**: Pydantic `@model_validator` methods ensure that it is fundamentally impossible to generate a `RetrievalResult` containing an unobservable facet. If the retrieval index accidentally surfaces a medical diagnosis, the contract validation will block it from ever reaching the LLM scorer.
