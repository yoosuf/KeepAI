# Extending LLM Providers

KeepAI's LLM backend is swappable by design. The `LLMInterface` abstract base class in `src/core/interfaces/llm_interface.py` defines the contract; `OllamaClient` is the default adapter. To use a different provider — OpenAI, Anthropic, Gemini, a self-hosted vLLM instance, or anything else — implement `LLMInterface` and inject it in the prompt router.

---

## The Interface

```python
# src/core/interfaces/llm_interface.py

class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Blocking generation.
        Must return: {"response_text": str, "processing_time_ms": int, "meta_data": dict}
        """

    @abstractmethod
    async def stream_generate(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Streaming generation.
        Must yield: raw text tokens (strings), one at a time.
        """
```

Both methods are required. If the provider doesn't support streaming, raise `NotImplementedError` in `stream_generate`.

---

## Step 1 — Create the Client

Create `src/infrastructure/llm/{provider}_client.py`. Here are complete examples for common providers.

### OpenAI

```python
# src/infrastructure/llm/openai_client.py
import time
from typing import Any, AsyncGenerator, Dict

from openai import AsyncOpenAI

from src.core.interfaces.llm_interface import LLMInterface


class OpenAIClient(LLMInterface):
    def __init__(self, api_key: str, default_model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model

    async def generate(self, prompt: str, model: str = "", **kwargs) -> Dict[str, Any]:
        model = model or self.default_model
        start = time.time()

        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        return {
            "response_text": response.choices[0].message.content or "",
            "processing_time_ms": int((time.time() - start) * 1000),
            "meta_data": {
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else {},
            },
        }

    async def stream_generate(self, prompt: str, model: str = "", **kwargs) -> AsyncGenerator[str, None]:
        model = model or self.default_model

        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token
```

**Install dependency**: `pip install openai`

### Anthropic (Claude)

```python
# src/infrastructure/llm/anthropic_client.py
import time
from typing import Any, AsyncGenerator, Dict

import anthropic

from src.core.interfaces.llm_interface import LLMInterface


class AnthropicClient(LLMInterface):
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    async def generate(self, prompt: str, model: str = "", **kwargs) -> Dict[str, Any]:
        model = model or self.default_model
        start = time.time()

        message = await self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        return {
            "response_text": message.content[0].text if message.content else "",
            "processing_time_ms": int((time.time() - start) * 1000),
            "meta_data": {
                "model": message.model,
                "usage": {"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens},
            },
        }

    async def stream_generate(self, prompt: str, model: str = "", **kwargs) -> AsyncGenerator[str, None]:
        model = model or self.default_model

        async with self.client.messages.stream(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
```

**Install dependency**: `pip install anthropic`

### OpenAI-Compatible (vLLM, LM Studio, LiteLLM, etc.)

Any provider with an OpenAI-compatible API can reuse `OpenAIClient` by overriding `base_url`:

```python
from openai import AsyncOpenAI
from src.infrastructure.llm.openai_client import OpenAIClient

# vLLM running locally
client = OpenAIClient.__new__(OpenAIClient)
client.client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
client.default_model = "meta-llama/Llama-3-8B-Instruct"
```

Or subclass it:

```python
class VLLMClient(OpenAIClient):
    def __init__(self, base_url: str, model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key="not-needed")
        self.default_model = model
```

---

## Step 2 — Add Config

Add any new settings your provider needs to `src/core/config.py`:

```python
class Settings(BaseSettings):
    ...
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
```

Add the corresponding lines to `.env`:
```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

## Step 3 — Inject the Client

In `src/modules/prompts/router.py`, the `get_prompt_service` dependency factory creates the LLM client. Swap it here:

```python
# src/modules/prompts/router.py

from src.infrastructure.llm.openai_client import OpenAIClient
# or: from src.infrastructure.llm.anthropic_client import AnthropicClient

def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    llm_client = OpenAIClient(
        api_key=settings.OPENAI_API_KEY,
        default_model=settings.OPENAI_MODEL,
    )
    return PromptService(db=db, llm_client=llm_client)
```

No other changes needed — the service, router, and tests are all provider-agnostic.

---

## Step 4 — Update Tests

If you have tests for `PromptService`, they already use `AsyncMock` for the `llm_client` dependency, so they continue to pass unchanged. If you want provider-specific integration tests, see the [Testing Guide](../development/testing.md).

---

## Tips

### Structured JSON extraction

The `InvoiceAgent` uses Ollama's `format="json"` kwarg. For OpenAI, use `response_format={"type": "json_object"}`:

```python
# In PromptService.extract_invoice():
result = await self.llm_client.generate(
    prompt, model,
    response_format={"type": "json_object"},  # OpenAI
)
```

For Anthropic, instruct the model in the system prompt to output only JSON.

### Model name handling

Ollama uses names like `llama3`, `mistral`. OpenAI uses `gpt-4o-mini`. Anthropic uses `claude-sonnet-4-6`. The `model` parameter in the API request is passed directly to the client — the API caller supplies the appropriate name for the active provider.

### Multiple providers simultaneously

To support routing across providers, extend `get_prompt_service` to select a client based on the request's `model_name` prefix:

```python
def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    # Could also be driven by a "provider" request field
    if settings.ACTIVE_LLM_PROVIDER == "openai":
        llm_client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
    elif settings.ACTIVE_LLM_PROVIDER == "anthropic":
        llm_client = AnthropicClient(api_key=settings.ANTHROPIC_API_KEY)
    else:
        llm_client = OllamaClient(base_url=settings.OLLAMA_BASE_URL)
    return PromptService(db=db, llm_client=llm_client)
```

---

## Related

- [Architecture](../architecture.md) — LLM Interface in context
- [Configuration](configuration.md) — Adding new env vars
- [Testing Guide](../development/testing.md) — Mocking the LLM client
