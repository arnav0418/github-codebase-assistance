"""Google Gemini client — used in deployment (LLM_PROVIDER=gemini)."""

from functools import lru_cache

from app import config


@lru_cache(maxsize=1)
def _sdk_client(api_key: str):
    from google import genai

    return genai.Client(api_key=api_key)


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

    def complete(self, prompt: str) -> str:
        from google.genai import types

        try:
            response = _sdk_client(self.api_key).models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        return (response.text or "").strip()
