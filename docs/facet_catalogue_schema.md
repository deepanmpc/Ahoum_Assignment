# Facet Catalogue Schema

This document defines the schema for the enriched facet catalogue, which will be generated and saved to `data/processed/facet_catalogue.csv`.

## Required Output Columns

1. **`facet_id`** (String): A stable, unique identifier for the facet across repeated runs. Best generated via a deterministic hash (e.g., MD5) of the `facet_normalized` string.
2. **`facet_raw`** (String): The facet exactly as it appeared in the raw CSV data, preserving all original whitespace, punctuation, and capitalization.
3. **`facet_normalized`** (String): A cleaned, lowercased, and standardized version of the facet (removing trailing colons, numbering prefixes, etc.).
4. **`is_malformed`** (Boolean): Indicates whether the facet is a header artifact, completely unparseable, or otherwise unusable.
5. **`malformed_reason`** (String): A brief explanation if `is_malformed` is true. Empty otherwise.
6. **`facet_category`** (String): The high-level domain or psychological category for the facet (e.g., "Personality", "Clinical", "Professional").
7. **`facet_type`** (String): The type of the trait (e.g., "State", "Trait", "Behavior").
8. **`conversation_observable`** (String): Must strictly be `true`, `false`, or `uncertain`. Indicates if this facet can reasonably be evaluated and scored from a short text conversation.
9. **`observability_reason`** (String): The rationale for the `conversation_observable` classification.
10. **`sensitivity`** (String): Notes on whether scoring this facet involves sensitive information (e.g., medical diagnoses, protected attributes). Empty if none.
11. **`scoring_definition`** (String): A brief, precise definition of what the facet represents, to be used later in LLM prompts.
12. **`anchor_1`** (String): Behavioral description for a score of 1. MUST remain empty if the facet is non-observable or malformed.
13. **`anchor_3`** (String): Behavioral description for a neutral/middle score of 3. MUST remain empty if non-observable or malformed.
14. **`anchor_5`** (String): Behavioral description for a maximum score of 5. MUST remain empty if non-observable or malformed.
15. **`abstention_reason`** (String): Explains why a facet should not be scored from a short conversation (e.g., "Requires long-term observation," "Clinical biomarker").
16. **`review_required`** (Boolean): Flag indicating if human review is needed due to unclear, borderline, or risky classifications.
17. **`preprocessing_version`** (String): Identifier or timestamp representing the pipeline run that generated this record.

## Strict Requirements
* `facet_raw` must be copied directly from the source without alteration.
* `facet_id` must not rely on random UUIDs that change between pipeline runs.
* `conversation_observable` must be exactly one of: `true`, `false`, `uncertain`.
* All scoring anchors (`anchor_1`, `anchor_3`, `anchor_5`) must be completely empty when `conversation_observable` is not `true` or when `is_malformed` is `true`.
* `abstention_reason` is required for all facets where `conversation_observable` is `false` or `uncertain`.
