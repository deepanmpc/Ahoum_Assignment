# Structured Output Recovery

## Problem

LLMs frequently return malformed output: markdown fences around JSON, leading
prose, missing fields, hallucinated evidence quotes, or wrong facet IDs.

## Recovery Pipeline

1. **JSON Extraction** (`response_parser.py`)
   - Try direct `json.loads()`
   - Try extracting from ` ```json ``` ` fences
   - Try finding the outermost `{ ... }` braces
   - Return `None` if all fail

2. **Schema Validation** (`response_validator.py`)
   - Validate against `ScoringBatchResponse` Pydantic model
   - Check status/score consistency (scored requires 1–5; abstention requires null)
   - Check confidence is in [0, 1]

3. **Facet-ID Validation**
   - Every expected ID must appear exactly once
   - No extra/unknown IDs allowed
   - No duplicates allowed

4. **Evidence Grounding**
   - For scored items, the `evidence_quote` must appear verbatim in the conversation
   - Whitespace-normalised comparison (collapse spaces, case-insensitive)
   - Fabricated quotes fail validation

5. **Corrective Retry**
   - On any validation failure, one retry is issued
   - The retry prompt includes exact failure reasons
   - The same facet batch is repeated
   - If retry also fails → all facets in that batch get `error` status

## Safety Guarantees

- Invalid scores are never silently coerced
- Fabricated evidence is never accepted
- Unknown facet IDs are never injected
- One failed batch does not crash other batches
