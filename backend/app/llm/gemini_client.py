"""Google Gemini client — used in deployment (LLM_PROVIDER=gemini)."""

from app import config


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

    def complete(self, prompt: str) -> str:
        """TODO: implement — call the Gemini generate-content API, return the text."""
        raise NotImplementedError
