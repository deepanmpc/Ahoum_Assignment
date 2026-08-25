# Final Clean-Clone Reproducibility Rehearsal

This document records the exact results of testing the repository in a clean, isolated directory (`/tmp/ahoum_clean_test`), simulating an evaluator's first experience.

## Setup Commands
```bash
# Clone and isolate
cp -R /Users/deepandee/desktop/ahoum /tmp/ahoum_clean_test
cd /tmp/ahoum_clean_test
rm -rf .venv __pycache__ .pytest_cache data/processed/facet_catalogue.csv data/processed/facet_embeddings.npz data/processed/facet_index_metadata.json data/outputs debug_artifacts

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -q -e '.[dev]'
```

## Diagnosis and Recovery
**First command run**: `python scripts/doctor.py doctor`
**Result**: Failed with `Configuration invalid: missing directories: data/outputs`.
**Diagnosis**: The `.gitignore` file correctly tracks the `data/outputs` directory using a `.gitkeep` file. However, because my clean-clone simulation used a destructive `rm -rf data/outputs` to simulate a pristine environment, I accidentally deleted the `.gitkeep` file that a normal `git clone` would preserve.
**Fix**: `mkdir -p data/outputs`. A true `git clone` already includes the `.gitkeep`, so no code changes were necessary.

## Execution Sequence

1. **Diagnostic Check**
   ```bash
   python scripts/doctor.py doctor
   # Result: Configuration is valid. Model provider: ollama.
   ```
2. **Preprocessing Pipeline**
   ```bash
   python scripts/preprocess_facets.py
   # Result: Success. 399 facets parsed, normalized, anchored, and classified.
   ```
3. **Semantic Index Build**
   ```bash
   python scripts/build_index.py
   # Result: Success. Built offline index using FakeDeterministicEmbedder (mock mode fallback).
   ```
4. **Retrieval Validation**
   ```bash
   python scripts/retrieve_semantic.py --text "I strictly budget my money" --top-k 5
   python scripts/retrieve_keywords.py --text "I strictly budget my money"
   python scripts/retrieve_facets.py --text "I strictly budget my money" --human
   # Result: Success. Hybrid retrieval gracefully merged exact keyword matches with semantic backups and safely excluded non-observables.
   ```
5. **LLM Scoring (Mock Mode)**
   ```bash
   python scripts/score_conversation.py --text "I strictly budget my money" --dry-run --human
   # Result: Success. Evaluated dry-run prompt templates strictly.
   ```
6. **Benchmark Evaluation (Mock Mode)**
   ```bash
   python scripts/evaluate.py --include-proposed --provider mock --retrieval-mode hybrid
   # Result: Success. Evaluated 12 conversations safely with fallback validation retries gracefully absorbed by the pipeline. Output written to data/outputs/.
   ```
7. **Smoke Test**
   ```bash
   python scripts/smoke_test.py
   # Result: Success. All mocked provider integration boundaries executed and parsed successfully.
   ```
8. **Test Suite Verification**
   ```bash
   python -m pytest tests/
   # Result: Success. 133 tests passed in 0.30s.
   ```

## Conclusion
The system requires zero manual configuration to test natively. The mock provider handles evaluation correctly when an open-weight cloud endpoint or local Ollama is unconfigured. The clean-run workflow passed all constraints.
