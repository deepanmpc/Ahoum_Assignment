# Final Result Schema

## `ConversationScoringResult`

The top-level aggregated result for one scored conversation.

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string | Unique conversation identifier |
| `candidate_count` | int | Total facets in the scored shortlist |
| `scored_count` | int | Facets that received a 1–5 score |
| `insufficient_evidence_count` | int | Facets abstained due to weak evidence |
| `not_observable_count` | int | Facets abstained as inappropriate to assess |
| `error_count` | int | Facets where scoring failed |
| `retrieval_excluded_count` | int | Facets excluded during retrieval (not sent to LLM) |
| `batch_count` | int | Number of LLM batches executed |
| `total_latency_ms` | float | Cumulative provider latency |
| `provider` | string | Provider name used |
| `model` | string | Model name used |
| `warnings` | list[string] | Diagnostic warnings |
| `facet_scores` | list[FacetScore] | Ordered per-facet results |

## `FacetScore`

| Field | Type | Description |
|-------|------|-------------|
| `facet_id` | string | Stable facet identifier |
| `facet_raw` | string | Original raw facet text |
| `facet_normalized` | string | Normalised facet name |
| `status` | ScoreStatus | scored / insufficient_evidence / not_observable / error |
| `score_1_to_5` | int or null | Only present when status=scored |
| `confidence_0_to_1` | float | Model confidence |
| `evidence` | string or null | Exact conversation quote |
| `reason` | string | One-sentence justification |
| `model_metadata` | dict | Provider, model, batch index, attempts |

## Invariant: Abstentions ≠ Neutral Scores

A status of `insufficient_evidence` means no score was possible.
It is **structurally different** from a score of 3 (which means
"mixed but sufficient evidence"). The Pydantic validator rejects
any attempt to assign `score_1_to_5` when status ≠ `scored`.
