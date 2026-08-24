# Model Provider Setup

## Default: Local Ollama

The default configuration runs scoring through a local Ollama instance using a
small open-weight Qwen model (≤4B parameters).

### Prerequisites
1. Install [Ollama](https://ollama.ai)
2. Pull the default model:
   ```bash
   ollama pull qwen2.5:3b-instruct
   ```
3. Ensure Ollama is running (`ollama serve`)

### Configuration (`config.toml`)
```toml
[model]
provider = "ollama"
name = "qwen2.5:3b-instruct"
base_url = "http://localhost:11434"
timeout_seconds = 45
max_retries = 1
```

No API key is needed for local Ollama.

## Optional: Cloud Acceleration

Cloud providers are supported through OpenAI-compatible chat-completions APIs.
You must choose an **open-weight model within the assignment's ≤16B requirement**.
Model eligibility is a documented user/configuration responsibility.

### Groq
```bash
export AHOUM_MODEL_PROVIDER=groq
export AHOUM_MODEL_NAME=llama-3.1-8b-instant
export GROQ_API_KEY=your-key-here
```

### NVIDIA NIM
```bash
export AHOUM_MODEL_PROVIDER=nvidia
export AHOUM_MODEL_NAME=meta/llama-3.1-8b-instruct
export NVIDIA_API_KEY=your-key-here
```

### OpenRouter
```bash
export AHOUM_MODEL_PROVIDER=openrouter
export AHOUM_MODEL_NAME=qwen/qwen-2.5-7b-instruct
export OPENROUTER_API_KEY=your-key-here
```

> **Security**: API keys come exclusively from environment variables.
> They must never appear in config files, logs, Git history, or output JSON.

## Error Classification

Provider failures are classified as:
| Type | Meaning |
|------|---------|
| `timeout` | Request exceeded configured timeout |
| `auth` | Missing or invalid API key |
| `connection` | Cannot reach the provider endpoint |
| `rate_limit` | Provider throttling requests |
| `malformed_response` | Non-JSON or unparseable response |
| `provider_error` | Any other HTTP error |

All error messages are sanitised to never expose credentials.
