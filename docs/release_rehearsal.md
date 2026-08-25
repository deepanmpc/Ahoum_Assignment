# Phase G Release Rehearsal

## Environment Initialization
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,embeddings]"
```

## Smoke Test (Raw CSV to Evaluated Output)
```bash
python scripts/smoke_test.py
# Result: Processed dummy raw file, built index, executed hybrid retrieval, ran mock batches, successfully asserted 3 scored facets.
```

## Unit & Integration Tests
```bash
pytest tests/ -v
# Result: 133 passed. Tests include taxonomy classification, semantic retrieval, keyword compilation, hybrid merging, Pydantic invariants, batching logic, parser error handling, and redaction safety.
```

## Benchmark Evaluation Mock Run
```bash
python scripts/evaluate.py --include-proposed --provider mock --retrieval-mode hybrid
# Result: Evaluated 12 conversations and 8 sparse labels safely. Output artifacts written to data/outputs/.
```

## Security & Privacy Checks
- `debug_artifacts/` is `.gitignore`d.
- `AHOUM_MODEL_PROVIDER` and other config API secrets are redacted in log files.
- Full conversation content is intentionally omitted from stdout metrics.

## Known Limitations Intentionally Unresolved
1. **Live LLM Reliance**: The benchmark evaluation currently defaults to `mock` because no open-weights cloud endpoint was explicitly provisioned in the CI context. An evaluator must provide a real API key (e.g., Groq) to evaluate actual model reasoning.
2. **Reviewer Status Bottleneck**: By default, `evaluate.py` will not score any labels unless they have been explicitly accepted via the `review_labels.py` UI tool, intentionally preventing proposed (unverified) LLM labels from polluting the ground truth.
3. **Keyword Rigidity**: The keyword router strictly requires exact regex boundaries; it currently ignores pluralizations not explicitly listed in the TOML rules.
