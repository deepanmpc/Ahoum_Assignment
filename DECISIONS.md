# Engineering Decisions

This document records non-trivial architecture and design trade-offs made during
implementation. Each decision includes the problem, options considered, the
choice made, and what was traded away.

---

## D1 — Hybrid Retrieval: Semantic + Keyword vs. Single Route

**Problem**: Pure semantic retrieval (cosine similarity on sentence embeddings)
surfaces conceptually related facets but lacks precision — it cannot distinguish
"talks about money" from "takes financial risks." Pure keyword routing has
perfect precision for listed phrases but zero recall on paraphrased language.

**Options considered**:
1. Semantic-only retrieval with a high similarity threshold.
2. Keyword-only routing with extensive manually curated dictionaries.
3. Hybrid merge: union both candidate sets, deduplicate by `facet_id`, combine
   scores with configurable weights.

**Choice**: Option 3. Implemented in `hybrid_retriever.py`.

**Evidence**: The retrieval ablation (`scripts/run_ablation.py`) confirmed:
semantic-only achieved 0.4 Recall@5 on the benchmark; keyword-only achieved 0.0
because benchmark phrasing does not literally match routing keywords. Hybrid
matched semantic recall while preserving keyword safety constraints.

**Trade-off accepted**: Maintaining two retrieval paths doubles retrieval code
complexity and requires curating both embedding quality and keyword dictionaries.

**Revisit trigger**: If a single high-quality embedding model consistently
outperforms the hybrid on a larger benchmark (100+ labeled conversations), the
keyword path could be reduced to a safety filter rather than a full retrieval
route.

---

## D2 — Observability Policy: Strict Category-Based Exclusion

**Problem**: The 399-facet catalogue contains medical diagnoses ("FSH level"),
biographical facts ("Number of siblings"), religious practices ("Pilgrimage
participation count"), and genuinely conversation-observable traits ("Speaks
calmly"). Scoring a medical diagnosis from conversation text would be
hallucination.

**Options considered**:
1. Let the LLM decide observability at scoring time via prompt instructions.
2. Pre-classify all facets into observable/non-observable categories using
   deterministic rules, and structurally block non-observables from reaching the
   LLM entirely.

**Choice**: Option 2. `taxonomy_rules.py` classifies facets into categories
(`health_medical`, `external_biographical_fact`, `religious_or_cultural_practice`,
`conversational_trait`, `unclear`). Non-observable categories are excluded during
retrieval, before any LLM call.

**Evidence**: The `RetrievalResult` Pydantic model validator
(`models.py:validate_result_invariants`) raises a `ValueError` if any candidate
has `conversation_observable != "true"`. This is enforced at the contract level,
not just by convention.

**Trade-off accepted**: Rule-based classification leaves many borderline facets
as `uncertain` (requiring manual override via `facet_overrides.csv`). An LLM
might classify some of these correctly, but would also risk hallucinating
observability for genuinely private medical traits.

**Revisit trigger**: If the override CSV grows beyond ~50 manual entries, an
LLM-assisted classification step with human-in-the-loop approval would reduce
curation burden.

---

## D3 — Explicit Abstention: Status Enum + Nullable Score

**Problem**: If a facet reaches the LLM but the conversation provides no
evidence, a score of 3/5 ("neutral") might be interpreted as a real assessment.
This silently converts "no evidence" into a fabricated data point.

**Options considered**:
1. Always return a 1–5 score; treat 3 as "insufficient."
2. Return a sentinel score (e.g., -1 or 0) for abstention.
3. Use an explicit `status` enum (`scored`, `insufficient_evidence`,
   `not_observable`, `error`) and allow `score_1_to_5` only when
   `status == scored`.

**Choice**: Option 3. Implemented via `ScoreStatus` enum and Pydantic
`@model_validator` in `models.py`.

**Evidence**: `FacetScore.validate_score_status` raises `ValueError` if a scored
result has no numeric score, or if a non-scored result has a numeric score. This
is enforced structurally — it is impossible to construct a valid `FacetScore`
that conflates abstention with a neutral assessment.

**Trade-off accepted**: Every consumer of `FacetScore` must handle status
branching. Simple numeric aggregation (mean score) requires filtering by status
first.

**Revisit trigger**: None foreseeable — this is a safety-critical invariant.

---

## D4 — Model/Provider Strategy: Local Ollama Default + Optional Cloud

**Problem**: The assignment requires an open-weight model ≤16B. Local inference
via Ollama is free, private, and reproducible but slow (~2–5s per batch on CPU).
Cloud providers (Groq, NVIDIA NIM) offer 10–50× speedup but require API keys,
introduce network dependency, and raise privacy questions for conversation data.

**Options considered**:
1. Cloud-only with mandatory API key.
2. Local-only via Ollama.
3. Local default with configurable cloud override via environment variables.

**Choice**: Option 3. `providers/factory.py` reads `AHOUM_MODEL_PROVIDER` from
environment (or `config.toml`) and routes to the appropriate adapter. Ollama
requires no key. Cloud providers require an API key in `.env` (which is
gitignored).

**Evidence**: `providers/base.py:ProviderError.safe_message` actively strips
API keys from error messages. The test `test_providers.py` verifies that a
missing Groq key produces `"Groq API key not set"` without leaking the key
variable name or value.

**Trade-off accepted**: Mock-mode evaluation does not test actual LLM reasoning
quality. An evaluator must install Ollama or provide a cloud key to assess real
model behavior.

**Revisit trigger**: If Ollama adds a batch API (sending multiple prompts in one
HTTP call), the local latency disadvantage would shrink significantly.

---

## D5 — Batch Size: 5 Facets Per LLM Call

**Problem**: With 20–25 shortlisted candidates, we need to decide how many
facets to include in each LLM prompt.

**Options considered**:
1. One facet per call (20–25 calls per conversation).
2. All candidates in one call (1 call, very long prompt).
3. Fixed batches of 5 (4–5 calls per conversation).

**Choice**: Option 3. `batching.py:split_batches` divides candidates into groups
of 5.

**Evidence**: Batches of 5 produce prompts of ~800–1200 tokens (well within
3B-model context windows of 4K–8K). One facet per call would multiply latency by
5×. All-at-once risks context-window overflow and degrades small-model JSON
compliance — early testing showed that 3B models reliably produce valid JSON for
5 items but frequently drop or duplicate items beyond 10.

**Trade-off accepted**: 4–5 sequential HTTP calls add ~10–25s total latency on
local Ollama. This is acceptable for a baseline; cloud providers reduce it to
~1–2s total.

**Revisit trigger**: If the shortlist grows beyond 50 candidates (unlikely with
top-K=24), batch size could increase to 8–10 with a larger model.

---

## D6 — Index Design: NumPy Cosine vs. Vector Database

**Problem**: The semantic index stores embeddings for all observable facets and
performs similarity search at query time.

**Options considered**:
1. Local NumPy `.npz` file with brute-force cosine similarity.
2. FAISS `IndexFlatIP` for exact search with SIMD acceleration.
3. A managed vector database (Pinecone, Chroma, Weaviate).

**Choice**: Option 1. `semantic_index.py` stores L2-normalized embeddings in a
compressed NumPy file and computes `query @ embeddings.T` for cosine similarity.

**Evidence**: With 399 facets × 384 dimensions, the index is ~600 KB. Brute-force
cosine on this size takes <1 ms. Adding FAISS or a database would introduce
dependencies without measurable benefit.

**Trade-off accepted**: Brute-force cosine is O(n) in catalogue size. At 50,000+
facets, query latency would grow to ~10–50 ms, which is still fast but no longer
negligible relative to LLM latency.

**Revisit trigger**: If the catalogue exceeds 10,000 facets, switch to FAISS
`IndexFlatIP` (drop-in replacement, same results, SIMD-accelerated). If it
exceeds 100,000, consider approximate nearest neighbors (FAISS IVF or HNSW).

---

## D7 — Evidence Validation: Exact Quote Substring Match

**Problem**: The LLM must provide an `evidence_quote` for every scored facet.
Should we verify that the quote actually appears in the conversation?

**Options considered**:
1. Trust the LLM's quote without verification.
2. Require exact substring match in the conversation text.
3. Use fuzzy/semantic matching to allow paraphrased quotes.

**Choice**: Option 2. `response_validator.py` checks that `evidence_quote` is a
substring of the conversation text (case-insensitive). If not, the entire batch
validation fails and triggers a corrective retry.

**Evidence**: During smoke testing, the mock provider initially returned
`"smoke test evidence"` as the quote, which was correctly rejected because that
string did not appear in the test conversation (`"I am very careful when I work"`).
This was documented as a genuine debugging insight — the evidence grounding check
caught fabricated evidence even from a mock provider.

**Trade-off accepted**: Legitimate paraphrased quotes are rejected. If the LLM
writes `"I remained calm"` but the conversation says `"I stayed calm"`, the
validation fails. This is intentionally strict — false negatives (rejecting good
quotes) are safer than false positives (accepting fabricated evidence).

**Revisit trigger**: If live model evaluation shows >30% of valid scores are
rejected due to minor paraphrasing, add a fuzzy match fallback with a high
similarity threshold (e.g., Levenshtein ratio > 0.85).
