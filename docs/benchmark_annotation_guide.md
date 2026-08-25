# Benchmark Annotation Guidelines

## Core Philosophy
This benchmark tests the system's ability to strictly extract and score conversational traits, while firmly abstaining from unsupported inference, medical diagnosis, or hallucinated biographical facts. Annotations must reflect a **skeptical evaluator** mindset.

## Annotation Rules

### 1. When a score is allowed
A score (1-5) is allowed **only** if there is direct, verifiable evidence in the conversation text that supports the trait. The evidence must be clearly attributable to the speaker.

### 2. When `insufficient_evidence` is required
Use `insufficient_evidence` when the conversation loosely touches on a topic or implies a trait, but lacks explicit, concrete language or behavior to justify a confident score. 

### 3. When `not_observable` is required
Use `not_observable` when a facet attempts to measure an external reality, medical condition, deeply private history, or demographic fact that cannot be safely or ethically determined from a brief text snippet (e.g., actual wealth, clinical depression, religion).

### 4. Why a neutral score of 3 must not represent missing evidence
A score of 3 means "mixed but sufficient evidence" or "moderate presence of the trait." It must **never** be used as a default or "unknown/uncertain" fallback. If evidence is missing, the status must be `insufficient_evidence` with a null score.

### 5. How to handle direct self-report
If the speaker explicitly claims a trait (e.g., "I am very patient"), this qualifies as evidence for conversational self-representation. Ground the score using the exact quote.

### 6. How to handle behavior demonstrated by the text
If the speaker's language *demonstrates* the trait (e.g., speaking aggressively, organizing thoughts meticulously), this is valid evidence. The quote should capture the demonstrated behavior.

### 7. How to handle quotes about someone else
Quoted speech ("My boss said I am lazy") or statements about others ("John is so lazy") are **not** evidence about the speaker. These must result in `insufficient_evidence`.

### 8. How to handle sarcasm and jokes
Sarcasm or jokes ("Oh sure, I love waiting in line for 3 hours") must not be taken literally to assign a score. Treat these as `insufficient_evidence` unless the underlying meaning provides concrete evidence for a different trait.

### 9. How to handle contradictory evidence
If a speaker contradicts themselves ("I'm usually calm but today I screamed at everyone"), label as `insufficient_evidence` if the overall trait cannot be determined, or score carefully (e.g., a 3) if the contradiction itself demonstrates a moderate or mixed presentation, citing both parts.

### 10. How to handle code-switched text
Text containing multiple languages (e.g., Hindi-English) should be evaluated on its semantic meaning. Do not infer cultural background or stereotypes. If the meaning provides clear evidence, it can be scored. Include an English translation in the label rationale.

### 11. How to handle hallucination bait
For medical, biographical, religious, and external-fact bait (e.g., mentioning a medication or church):
*   Do **not** score related high-risk facets.
*   Assign `not_observable` or `insufficient_evidence`.
*   Rationale must explicitly state that inferring the fact from casual mention is prohibited.

### 12. How to select exact evidence quotes
The `expected_evidence_quote` must be a literal, continuous verbatim substring from the conversation text. Do not paraphrase or alter punctuation.

### 13. How to avoid identity/real-world assumptions
Never score based on presumed demographic, socioeconomic status, or real-world outcomes. (e.g., Discussing a budget does not mean the user is "wealthy" or "poor").

## Label Scope
- `retrieval_relevance`: The facet should/should not be retrieved for this text.
- `scoring_reference`: The facet should receive a specific 1-5 score.
- `abstention_reference`: The facet must explicitly be abstained from (`insufficient_evidence` or `not_observable`).

## Reviewer Status Workflow
All proposed labels start as `proposed`. They must not be claimed as human-reviewed.
A project owner must review and set the status to `reviewed_accepted`, `reviewed_changed`, or `rejected`.
