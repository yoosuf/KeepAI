import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List

import httpx

from src.core.config import settings
from src.core.interfaces.llm_interface import LLMInterface

logger = logging.getLogger(__name__)


class OllamaClient(LLMInterface):
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS)

    _OPTION_KEYS = {"temperature", "top_p", "top_k", "num_predict", "seed", "repeat_penalty", "num_ctx"}

    def _build_payload(self, base: dict, kwargs: dict) -> dict:
        options = {k: v for k, v in kwargs.items() if k in self._OPTION_KEYS}
        rest = {k: v for k, v in kwargs.items() if k not in self._OPTION_KEYS}
        payload = {**base, **rest}
        if options:
            payload["options"] = options
        return payload

    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = self._build_payload({"model": model, "prompt": prompt, "stream": False}, kwargs)

        start = time.time()
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            return {
                "response_text": data.get("response", ""),
                "processing_time_ms": int((time.time() - start) * 1000),
                "meta_data": {"raw_response": data},
            }
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Failed to communicate with LLM: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise

    async def stream_generate(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/generate"
        payload = self._build_payload({"model": model, "prompt": prompt, "stream": True}, kwargs)

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            logger.error(f"Ollama streaming error: {e}")
            raise Exception(f"LLM stream failed: {e}") from e

    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = self._build_payload({"model": model, "messages": messages, "stream": False}, kwargs)

        start = time.time()
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return {
                "response_text": data.get("message", {}).get("content", ""),
                "processing_time_ms": int((time.time() - start) * 1000),
                "meta_data": {"raw_response": data},
            }
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            raise Exception(f"Failed to communicate with LLM: {e}") from e

    async def stream_chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload = self._build_payload({"model": model, "messages": messages, "stream": True}, kwargs)

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            logger.error(f"Ollama stream_chat error: {e}")
            raise Exception(f"LLM stream failed: {e}") from e

    async def close(self):
        await self._client.aclose()
