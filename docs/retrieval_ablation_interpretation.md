# Retrieval Ablation Interpretation

This document interprets the retrieval ablation results comparing semantic, keyword, and hybrid approaches.

## Honest Findings

1. **Semantic Only**: Tends to retrieve broadly across categories but can sometimes pull in hallucination-bait (e.g., retrieving medical facets for casual mentions of ibuprofen) due to embedding proximity without rigid boundary checking.
2. **Keyword Only**: Very high precision and extremely safe (zero unsafe facets retrieved when rules are strict). However, it frequently misses nuanced behavioral language that doesn't explicitly match dictionary terms.
3. **Hybrid (The Trade-off)**: Achieves the best overall recall by letting semantic search handle nuance, while applying strict filtering and keyword exact-matches to boost the most obvious signals. The shortlist is slightly larger, but it remains bounded by the top-K limit.

### Qualitative Examples
*   **Semantic Advantage**: A user saying "I always double-check my work" will not match "meticulous" exactly via keyword rules, but semantic retrieval easily captures it as related to work habits.
*   **Keyword Safety Advantage**: A user saying "I invest strictly" might semantically trigger "financial_risk" facets. Keyword routing with negative constraints can explicitly suppress irrelevant hits in a way semantic search cannot natively control.
