# Scoring Prompt Contract

## Prompt Structure

Each scoring request sent to the model contains:
1. **System instructions** — rules for evidence-based scoring and abstention
2. **Conversation text** — delimited by `--- CONVERSATION ---` / `--- END ---`
3. **Facet batch** — at most 5 facets, each with:
   - `facet_id`
   - `name` (normalized)
   - `scoring_definition`
   - `anchor_1` (low), `anchor_3` (moderate), `anchor_5` (high)

## Critical Instructions in the Prompt

- Assess ONLY direct evidence in the supplied conversation
- Do NOT infer diagnoses, health conditions, lab values, private history, religion, occupation, socioeconomic status, real-world behaviour, or biographical facts
- Quoted speech, sarcasm, jokes, and statements about others are NOT evidence about the speaker
- If evidence is absent/weak/contradictory → `insufficient_evidence`
- If the facet is inappropriate to assess → `not_observable`
- Evidence quote must be EXACT text from the conversation
- Output JSON ONLY — no markdown, prose, or code fences

## Response Schema

```json
{
  "results": [
    {
      "facet_id": "string",
      "status": "scored | insufficient_evidence | not_observable",
      "score_1_to_5": 1,
      "confidence_0_to_1": 0.0,
      "evidence_quote": "exact quote or empty string",
      "reason": "one concise evidence-based sentence"
    }
  ]
}
```

## Abstention Rules
- `score_1_to_5` must be `null` for non-scored statuses
- `evidence_quote` may be empty for abstentions
- `reason` must explain the evidence limitation
