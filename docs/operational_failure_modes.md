# Operational Failure Modes

This document describes the failure modes the system handles, how each is
detected, and what recovery looks like.

---

## 1. Provider Connection Failures

**Symptom**: `ProviderError: Connection timed out` or `Connection refused`.

**System behavior**: The affected batch immediately fails with status `error`.
No retry is attempted for network-level failures (timeouts, refused connections,
auth failures). Other batches continue normally.

**Recovery**: Check that Ollama is running (`ollama list`) or that cloud API
credentials are set in `.env`. Use `ahoum doctor` to validate configuration.

---

## 2. Malformed JSON from LLM

**Symptom**: The LLM returns prose, markdown-fenced JSON, or syntactically
broken JSON.

**System behavior**: The 3-stage parser (`response_parser.py`) attempts:
1. Direct `json.loads()`.
2. Extract content from markdown fences (` ```json ... ``` `).
3. Find the outermost `{...}` braces.

If all three fail, a corrective retry prompt is sent once, including the
specific validation errors. If the retry also fails, the batch is marked as
`error` for all its facets. Successful batches are never re-sent.

**Recovery**: Switch to a larger model (e.g., 7B) that produces more reliable
JSON, or use a cloud provider with better JSON compliance.

---

## 3. Missing or Extra Facet IDs in LLM Response

**Symptom**: The LLM omits one or more `facet_id` values from its response, or
invents IDs not present in the batch.

**System behavior**: `response_validator.py` cross-checks returned `facet_id`
values against the expected batch. Missing IDs trigger a corrective retry. Extra
IDs are silently ignored. If the retry also has missing IDs, the batch fails.

**Recovery**: Strengthen the prompt template to emphasize returning all IDs.
Consider reducing batch size from 5 to 3 for unreliable models.

---

## 4. Evidence Quote Not Found in Conversation

**Symptom**: The LLM provides a quote that does not appear as a substring in
the conversation text.

**System behavior**: The batch validation fails with an evidence grounding
error. A corrective retry is attempted once. If the retry also fails, the batch
is marked as `error`.

**Note**: This check is strict — paraphrased but semantically correct quotes
are rejected. See `DECISIONS.md: D7` for the rationale.

---

## 5. Partial Batch Failure

**Symptom**: One batch fails (provider error, validation failure) while others
succeed.

**System behavior**: Failed batches produce `ScoreStatus.ERROR` for their
facets. Successful batches are aggregated normally. The final
`ConversationScoringResult` reports `error_count` alongside `scored_count`.
The pipeline never crashes due to a single failed batch.

**Tested by**: `tests/integration/test_fault_injection.py`.

---

## 6. Stale Embedding Index

**Symptom**: The embedding index was built from an older version of the
catalogue. New or modified facets are not retrieved.

**System behavior**: `semantic_index.py:check_index_freshness` compares the
catalogue file hash stored in `facet_index_metadata.json` against the current
catalogue. If they differ, a warning is emitted.

**Recovery**: Re-run `python scripts/build_index.py` after any catalogue change.

---

## 7. Missing Configuration or Invalid Values

**Symptom**: `config.toml` is missing, has invalid TOML syntax, or contains
invalid values (e.g., `batch_size = -1`).

**System behavior**: `config.py:load_config` raises `ValueError` with a
specific message (e.g., `"scoring_batch_size must be positive"`). This fails
before any provider call or data processing.

**Tested by**: `tests/test_config.py`.

---

## 8. Debug Mode

Debug mode is **opt-in only** (pass `debug_mode=True` to `score_conversation`).
When enabled:
- Raw prompts and LLM responses are written to `debug_artifacts/<conversation_id>/`.
- A warning is emitted: "debug_artifacts/ may contain conversation data."
- The `debug_artifacts/` directory is automatically `.gitignore`d.
- Even in debug mode, API keys and bearer tokens are structurally redacted before
  writing to disk.

See `docs/privacy_and_debugging.md` for details.
