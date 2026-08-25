# Failure Analysis Template

Use this template to categorize and document errors discovered in the evaluation report.

## Taxonomy of Failures

### 1. Retrieval Miss
- **Symptom**: Facet not in top-K.
- **Root Cause**: Poor semantic embedding alignment or missing routing keyword.
- **Fix Idea**: Add phrasing to routing rules.

### 2. Unsupported Score (Hallucination)
- **Symptom**: Model scored 1-5 when evidence was insufficient.
- **Root Cause**: LLM over-inferring or ignoring strict system prompt constraints.
- **Fix Idea**: Strengthen abstention prompt clauses.

### 3. Provider/Runtime Failure
- **Symptom**: JSON parse error or timeout.
- **Root Cause**: API instability or poor JSON generation from the LLM.
- **Fix Idea**: Adjust JSON recovery blocks or switch providers.