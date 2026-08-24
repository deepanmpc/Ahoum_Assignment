# Keyword Routing Rules

This document outlines the design, mapping logic, and extension principles for the taxonomy-based keyword router complementing the semantic retrieval engine.

## Purpose
While semantic similarity (cosine search over embeddings) excels at finding contextually related traits, it occasionally surfaces statistically proximate but logically incorrect behaviors. The keyword router acts as a transparent, high-precision counterpart. By explicitly matching phrases (e.g., "budgeting", "investment risk") to categorical domains (e.g., `finance_risk`), the router guarantees that unambiguous conversational signals route perfectly to their corresponding observable facets.

## Mapping Structure (`routing_rules.toml`)
The keyword router relies on a version-controlled TOML configuration.

### Attributes
- **`keywords`**: A list of highly explicit terms or phrases. Matched using word boundaries (`\b`) and case insensitivity to prevent naive substring errors (e.g., "asset" matching inside "cassette").
- **`negative_keywords`**: Phrases that explicitly cancel a match for that category within the same text.
- **`weight`**: The maximum hybrid/keyword score cap for this category.
- **`priority`**: Optional categorical ranking mechanism.

## Observability Safety Guarantee
The keyword router **strictly evaluates observability**.
If a conversation contains the phrase `"blood pressure"`, it will successfully trigger the `health_medical` routing rule. However, the router dynamically cross-references the `facet_catalogue.csv`. Since all medical facets are strictly tagged `conversation_observable=false`, they are **blocked** from entering the candidate list. They will instead correctly accrue to the `excluded_non_observable_count` diagnostic metric.

## Extension Guidelines
- **Multi-lingual**: If global code-switching is expected (e.g., Spanish `hablador` for "talkative"), append it directly to the category's `multilingual` sub-array to ensure it correctly routes to the `communication` domain.
- **Weak Matches**: Avoid single-character or highly overloaded terms (e.g., "good", "bad", "fast"). Rely on the semantic retrieval engine for fuzzy concepts, reserving the keyword router for unambiguous markers.
