"""Local Ollama client — used for development (LLM_PROVIDER=ollama)."""

from app import config


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL

    def complete(self, prompt: str) -> str:
        """TODO: implement — POST {base_url}/api/generate with stream=False."""
        raise NotImplementedError
