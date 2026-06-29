from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List


class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text from a prompt (blocking).

        Returns:
            {"response_text": str, "processing_time_ms": int, "meta_data": dict}
        """

    @abstractmethod
    async def stream_generate(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream generated tokens as they arrive.

        Yields raw text chunks; caller is responsible for SSE formatting.
        """

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Multi-turn chat with conversation history (blocking).

        messages: [{"role": "user"|"assistant"|"system", "content": str}, ...]
        Returns:
            {"response_text": str, "processing_time_ms": int, "meta_data": dict}
        """

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream tokens for a multi-turn chat.

        Yields raw text chunks.
        """
