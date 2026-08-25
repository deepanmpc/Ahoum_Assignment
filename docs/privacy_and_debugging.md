# Privacy and Debugging

This pipeline processes potentially sensitive conversational data. 

## Default Logging
By default, the system operates in a privacy-safe mode:
- Raw conversation text is never logged to stdout/stderr.
- Raw LLM prompts and model outputs are not logged.
- API keys, authorization headers, and bearer tokens are never logged.
- Only aggregated metrics, batch processing progress, and error categories are logged.

## Debug Mode (`--debug` or equivalent)
When troubleshooting model failures or parser errors, you can enable debug mode. This will:
1. Increase log verbosity to `DEBUG`.
2. Write raw prompts and model responses to a local `debug_artifacts/<conversation_id>/` directory.

### Important Warnings
- **Conversation Data Leakage**: Debug files contain the complete text of the conversation and the model's exact response. Do not share these files if they contain PII or sensitive conversational traits.
- **Git Ignored**: The `debug_artifacts/` directory is automatically `.gitignore`d to prevent accidental commits of sensitive data.
- **Secrets Redacted**: Even in debug mode, common secrets (e.g., `Bearer` tokens, `Authorization` headers, explicit `api_key` JSON properties) are structurally redacted before writing to disk.

### Usage
To use debug mode, set `debug_mode=True` in `score_conversation` or pass `--debug` to CLI scripts if supported.
