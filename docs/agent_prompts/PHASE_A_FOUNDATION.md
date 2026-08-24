# Phase A — Repository foundation and contracts

## Mission and time box

Complete this phase in **two to three hours**. Its job is to make the project
safe to build on: reproducible setup, clear data contracts, configuration, and
tests. It intentionally does **not** enrich the CSV, download models, call an
API, calculate embeddings, score a conversation, or claim benchmark results.

The finished system will eventually process a heterogeneous 399-row facet CSV,
retrieve a small relevant subset with semantic and keyword routing, then score
only that subset in batches with an explicit ability to abstain. Phase A should
make those later stages easy without pretending they already exist.

## Shared context for every Phase A agent

```text
Repository: Ahoum_Assignment
Task: an AI/ML take-home assignment that evaluates short conversations against
many facets without sending the entire catalogue to an LLM.

Final architecture:
raw CSV -> enriched facet catalogue -> hybrid retrieval -> candidate shortlist
-> batches of five facets -> structured score or abstention -> evaluation.

Primary model plan: a Qwen model of <=4B parameters via Ollama by default.
Later, the same provider interface may route to Groq, NVIDIA NIM, or OpenRouter.
No API key, model pull, network call, embedding download, or provider call is
allowed in Phase A.

Non-negotiable output rule: only status=\"scored\" may contain score 1–5.
The statuses insufficient_evidence, not_observable, retrieval_excluded, and
error must have a null score. A score of 3 is never a substitute for abstaining.

Work rules:
- Preserve raw inputs and unrelated user changes.
- Do not commit .env, keys, runtime outputs, or downloaded models.
- Use small modules with type hints and tests.
- Update PROMPT_LOG.md truthfully with this material AI assistance.
- Make focused commits; never use one catch-all final commit.
```

## Prompt A1 — Project skeleton and result contracts

```text
You own Prompt A1 of Phase A. Read the shared context in
docs/agent_prompts/PHASE_A_FOUNDATION.md before editing.

Create a clean Python project skeleton suitable for the later pipeline.

Deliverables:
1. Use a src-layout package, scripts/, tests/, docs/agent_prompts/, and these
   directories: data/raw, data/processed, data/examples, data/outputs.
2. Add package metadata for Python 3.11+ and a minimal development test setup.
3. Add .gitignore rules that preserve empty directory placeholders but prevent
   generated catalogues/results, virtual environments, caches, and .env from
   being committed.
4. Define typed facet and score data contracts. A facet record must preserve a
   raw name and support normalized name, category, observability, sensitivity,
   scoring definition, and abstention reason. A result must hold facet identity,
   status, nullable score, confidence, evidence, reason, and model metadata.
5. Validate all invariants. Reject blank IDs/names, confidence outside [0,1], a
   scored result missing a valid integer 1–5, and an abstention/error containing
   a score.
6. Add tests for a valid score and at least two invalid abstention cases.

Do not include a fake output file, manual facet classifications, retrieval code,
LLM client, or provider SDK. Keep dependencies to an absolute minimum so tests
can run before a model is installed.

Verification:
- run the test suite;
- inspect git status to ensure only intentional source/docs files changed;
- ensure output directories can exist but generated contents are ignored.

Update PROMPT_LOG.md with the exact kind of work performed, what you retained,
what you deliberately did not implement, and the command used to verify it.
Commit only this completed slice with a message similar to:
`chore: establish project foundation and result contracts`.
```

## Prompt A2 — Configuration and diagnostic command

```text
You own Prompt A2 of Phase A. Start from the existing repository state and
preserve all prior Phase A work. Read the shared context first.

Add central configuration for the future system but do not implement provider
requests.

Requirements:
1. Choose a simple human-readable, version-controlled config format. It must
   contain project-relative paths for raw CSV, processed catalogue, embedding
   index, examples, and output results.
2. Add a model section containing provider, model name, base URL, timeout, and
   retry limit. Default it to an Ollama-served Qwen model of <=4B parameters.
3. Add retrieval top-K plus semantic/keyword weighting, and scoring batch size
   plus a minimum confidence threshold. These values are configuration only.
4. Support environment-variable overrides for provider, model, and base URL.
   Keep API-key placeholders only in .env.example; no key may be hard-coded or
   read by this phase.
5. Implement a local diagnostic command, for example
   `python scripts/doctor.py doctor`, which checks config parsing and required
   local directories. Its output must explicitly say no model or network call
   was made.
6. Add tests that load the config and assert the important defaults. Tests must
   not require package installation, an internet connection, Ollama, or keys.
7. Update README with exact setup, diagnostic, and test commands, accurately
   calling later pipeline steps planned rather than complete.

Check edge cases: run the diagnostic from repository root, ensure all paths are
anchored to the config location rather than the current shell directory, and do
not accidentally parse .env or contact the configured base URL.

Update PROMPT_LOG.md with the prompt summary, implementation choices, and
verification. Commit as a focused configuration/diagnostic change.
```

## Prompt A3 — Independent quality and safety review

```text
You are the Phase A reviewer, not the Phase A feature builder. Read the shared
context and inspect all completed Phase A files before proposing edits.

Audit these evaluator-facing risks:

- Could any downstream user interpret an abstention as a middle score?
- Could tests, imports, configuration loading, or the diagnostic command call a
  cloud endpoint, Ollama, download a model, or require a secret?
- Could a future generated catalogue overwrite the raw assignment CSV?
- Are data paths and output paths project-relative and unambiguous?
- Are .env and generated runtime results ignored by Git?
- Is the README truthful about what exists today?
- Does a clean Python 3.11 environment have a reasonable setup path?

Run every documented Phase A command. Fix only concrete defects you find. Add
the smallest useful regression tests, especially around abstention safety and
config path behavior. Do not implement any B-or-later work merely because it is
mentioned in the README.

If you change code or docs, record:
- observed issue/symptom;
- cause;
- correction;
- verification command.

Use DEBUGGING.md only for real reproducible issues. Do not invent a bug to meet
future assignment requirements. Update PROMPT_LOG.md with the review details.
Create a small focused commit only when there are actual fixes.
```

## Prompt A4 — Process evidence and phase handoff

```text
You own the final Phase A handoff. Do not add any new product capability.

Verify the repository contains:
- README.md with truthful current status, architecture target, setup, diagnostic
  command, test command, and a clear statement that all facets will never be
  sent in one LLM prompt;
- PROMPT_LOG.md that records material prompts with tool/model, summary, what was
  used, what was changed/rejected, and verification;
- DECISIONS.md containing at least two genuine Phase A decisions in the form
  problem, options, choice, trade-off;
- DEBUGGING.md prepared for genuine later issues without fabricated entries;
- configuration, safe .env.example, contracts, and tests.

Run from the repository root:
1. the README diagnostic command;
2. the complete test suite;
3. git status;
4. a check that .env and a generated output file would be ignored.

Fix only release-blocking Phase A issues. Ensure the raw CSV is not included,
altered, or replaced by a generated file in this phase. Make the final focused
commit if needed. Return the commit hashes, commands run, and a short list of
Phase B prerequisites.
```

## Definition of done

- A clean clone can install development dependencies, run the local diagnostic,
  and run the unit tests without a model or API account.
- Raw input and generated output locations are separate.
- The result contract makes fabricated neutral scores structurally impossible.
- Future Ollama/cloud selection is configuration-ready but no provider client
  exists yet.
- Documentation is evidence-based and Git history consists of focused commits.

## Explicit non-goals

- Do not classify or enrich the 399 facets.
- Do not use LLMs, embeddings, Ollama, Groq, NVIDIA NIM, or OpenRouter.
- Do not write benchmark conversations, labels, metrics, or performance claims.
- Do not create a UI, notebook, Docker setup, or a vector database.
