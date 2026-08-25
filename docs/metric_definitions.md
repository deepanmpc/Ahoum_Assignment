# Metric Definitions

## 1. Retrieval Metrics
- **Recall@K (Facet-level)**: Percentage of explicitly labeled relevant facets (`retrieval_relevance` scope) that appear in the top-K retrieved candidates.
- **Category Recall@K**: If specific facet labels are unavailable but expected categories are defined, the percentage of expected categories present in the top-K.
- **Candidate Shortlist Size**: Average number of candidates returned per conversation.
- **Unsafe-Facet Exclusion Rate**: Percentage of non-observable facets correctly excluded from the final shortlist.
- **No-Candidate Rate**: Percentage of low-evidence conversations where the system correctly returns 0 candidates.

## 2. Scoring Metrics
Calculated *only* where both a reference label and system result exist.
- **Exact Ordinal Agreement**: Percentage of scored facets where system score exactly equals reference score (1-5).
- **Within-One-Level Agreement**: Percentage of scored facets where system score is within ±1 of reference score.
- **Mean Absolute Error (MAE)**: Average absolute difference between system and reference scores (computed only for overlapping scored items).
- **Excluded Label Count**: Count of labels not ordinally scored because the reference mandated an abstention.

## 3. Abstention Metrics
- **Abstention Precision**: When the system abstains, how often was it expected to abstain?
- **Abstention Recall**: When the reference requires abstention, how often does the system abstain?
- **Unsupported-Score Rate**: The model assigned a 1-5 score when the reference explicitly required abstention (`insufficient_evidence` or `not_observable`).
- **Over-Abstention Rate**: The model abstained when the reference expected a score.
- **Hallucination-Bait Pass Rate**: Percentage of explicit bait examples (medical, biographical, external) where the model successfully abstained.

## 4. Reliability Metrics
- **Parser Failure Rate**: Percentage of model responses that could not be parsed into JSON.
- **Corrective Retry Rate**: Percentage of validation failures that were successfully recovered on the second attempt.
- **Batch Failure Rate**: Percentage of LLM batches that completely failed and resulted in `error` status.
- **Average Latency**: End-to-end time taken per conversation (if using a live provider).
