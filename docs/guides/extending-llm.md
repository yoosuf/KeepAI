# Extending LLM Support

KeepAI uses a **Ports and Adapters** pattern for LLM integration, making it straightforward to add new LLM backends.

---

## LLMInterface (The Port)

All LLM interactions go through the `LLMInterface` abstract class at `src/core/interfaces/llm_interface.py`:

```python
class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str = "", **kwargs) -> dict:
        """Generate a response for a single prompt."""

    @abstractmethod
    async def chat(self, messages: list[dict], model: str = "", **kwargs) -> dict:
        """Generate a response for a multi-turn conversation."""

    @abstractmethod
    async def stream_generate(self, prompt: str, model: str = "", **kwargs):
        """Stream tokens for a single prompt. Yields strings."""

    @abstractmethod
    async def stream_chat(self, messages: list[dict], model: str = "", **kwargs):
        """Stream tokens for a conversation. Yields strings."""
```

---

## Adding a New Provider

### Step 1: Create the adapter

Create a new file in `src/infrastructure/llm/`, e.g., `openai_client.py`:

```python
from src.core.interfaces.llm_interface import LLMInterface

class OpenAIClient(LLMInterface):
    def __init__(self, base_url: str = "https://api.openai.com/v1"):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def generate(self, prompt: str, model: str = "gpt-4", **kwargs) -> dict:
        response = await self.client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
            },
        )
        response.raise_for_status()
        data = response.json()
        return {
            "response": data["choices"][0]["message"]["content"],
            "total_duration": 0,  # OpenAI doesn't provide this
        }

    async def chat(self, messages: list, model: str = "gpt-4", **kwargs) -> dict:
        # ... similar implementation
        pass

    async def stream_generate(self, prompt: str, model: str = "", **kwargs):
        # ... SSE streaming implementation
        pass

    async def stream_chat(self, messages: list, model: str = "", **kwargs):
        # ... SSE streaming implementation
        pass

    async def close(self):
        await self.client.aclose()
```

### Step 2: Register in `src/main.py`

```python
from src.infrastructure.llm.openai_client import OpenAIClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Choose provider based on env var
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "openai":
        app.state.llm_client = OpenAIClient()
    else:
        app.state.llm_client = OllamaClient(base_url=settings.OLLAMA_BASE_URL)
    yield
    await app.state.llm_client.close()
```

### Step 3: Add environment variables

Add to `backend/.env.example`:

```ini
# LLM Provider
LLM_PROVIDER=ollama
OPENAI_API_KEY=
```

### Step 4: Test

```bash
# Set provider
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Run tests
python -m pytest tests/services/test_prompt_service.py -v
```

---

## Model Routing

The `MODEL_ROUTING` env var maps task types to specific models:

```ini
MODEL_ROUTING='{"code": "codellama", "analysis": "llama3", "chat": "mistral"}'
```

When a request includes `"task_type": "code"`, the system routes it to `codellama` regardless of the default model. This works with any provider.

---

## Current Adapter: OllamaClient

The built-in `OllamaClient` (`src/infrastructure/llm/ollama_client.py`) connects to a local Ollama instance:

- **generate()** — calls `POST /api/generate`
- **chat()** — calls `POST /api/chat` with message history
- **stream_generate()** — streams from `/api/generate` with `stream: true`
- **stream_chat()** — streams from `/api/chat` with `stream: true`

---

## Related

- [Architecture](../architecture.md)
- [Configuration](configuration.md)
- [API Reference](../api/reference.md)
