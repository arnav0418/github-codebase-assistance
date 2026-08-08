"""LLM provider switch. The only place that branches on LLM_PROVIDER."""

from app import config
from app.llm.base import LLMClient


def get_llm_client() -> LLMClient:
    if config.LLM_PROVIDER == "ollama":
        from app.llm.ollama_client import OllamaClient

        return OllamaClient()
    if config.LLM_PROVIDER == "gemini":
        from app.llm.gemini_client import GeminiClient

        return GeminiClient()
    raise ValueError(
        f"Unknown LLM_PROVIDER {config.LLM_PROVIDER!r} (expected 'ollama' or 'gemini')"
    )
