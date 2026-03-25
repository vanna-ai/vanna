# Groq Integration

The Groq integration lets Vanna use Groq-hosted LLMs through GroqLlmService.

## Features

- Non-streaming request/response support
- Streaming token output
- Tool calling and tool call parsing

## Setup

Install the Groq extra:

```bash
pip install "vanna[groq]"
```

Set your API key:

- Environment variable: GROQ_API_KEY
- Or pass api_key directly when constructing the service

Optional environment variables:

- GROQ_MODEL (default model if not passed)
- GROQ_BASE_URL (for custom API endpoint)

## Example Usage

```python
from vanna.integrations.groq import GroqLlmService

llm = GroqLlmService(
	api_key="your_api_key",
	model="llama-3.3-70b-versatile",
)
```

Use llm with your Vanna Agent as the configured LLM service.
