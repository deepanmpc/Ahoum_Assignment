# Evaluation Protocol

This document defines the protocol for evaluating the Ahoum facet scoring system.

## Integrity Rules
- The reference set is sparse and intentionally small. This evaluation is designed for **diagnostic insight**, not academic-grade validity.
- Evaluation must clearly distinguish between **owner-reviewed** reference results and **proposed-label** (development) results. By default, metrics are only calculated against `reviewed_accepted` or `reviewed_changed` labels.
- Mock-provider tests and live-model results must be strictly differentiated in run outputs.
- Failures must not be hidden. System errors (like parser failures) are recorded and distinct from correct abstentions.

## Evaluation Layers
1. **Retrieval Evaluation**: Did routing retrieve facets expected to be relevant?
2. **Scoring Evaluation**: For retrieved labeled facets, did the system match the reference score?
3. **Abstention Evaluation**: Does the system abstain appropriately when evidence is absent or the facet is hallucination bait?
4. **Reliability Evaluation**: Are there parser/provider failures? What is the latency?

## Run Artifacts
Each evaluation run produces an immutable directory in `data/outputs/<run_id>/` containing:
- `run_metadata.json`: Provenance (commit hash, config, modes)
- `retrieval_outputs.jsonl`: Raw retrieval candidate lists
- `scoring_outputs.jsonl`: Aggregate pipeline scoring results
- `per_label_comparisons.jsonl`: Granular comparison of reference vs. actual
- `evaluation_summary.json`: Top-level aggregate metrics
- `evaluation_report.md`: Human-readable summary
