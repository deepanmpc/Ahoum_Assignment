# Ahoum AI/ML Engineer Assignment

An abstention-aware baseline for evaluating conversation text against a large,
heterogeneous facet catalogue.

## Current status

Phase A is complete: repository structure, stable result contracts,
configuration, a no-network diagnostic command, and tests are in place.
Preprocessing, retrieval, model scoring, and evaluation are implemented in
subsequent phases.

## Architecture target

```text
raw facet CSV -> enriched catalogue -> hybrid retrieval -> small LLM batches
                                               |              |
                                   semantic + keywords   score or abstain
```

Only a small set of relevant, conversation-observable facets will be sent to
the scorer. The system will never send all facets in one prompt.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/doctor.py doctor
python -m pytest
```

`doctor` validates local configuration only. It does not contact Ollama,
Groq, NVIDIA NIM, OpenRouter, or any other model provider.

## Configuration and secrets

Copy `.env.example` to `.env` only when a future phase needs a hosted provider.
Never commit `.env` or provider API keys. The default configuration names a
Qwen model through Ollama; Phase A makes no model calls.

## Planned commands

Later phases will add reproducible commands for preprocessing, index building,
retrieval, scoring, and evaluation.

## Mandatory evidence

- [PROMPT_LOG.md](PROMPT_LOG.md)
- [DECISIONS.md](DECISIONS.md)
- [DEBUGGING.md](DEBUGGING.md)
- `data/processed/facet_catalogue.csv` (generated in Phase B)
- benchmark conversations, reference labels, and generated results (later phases)
