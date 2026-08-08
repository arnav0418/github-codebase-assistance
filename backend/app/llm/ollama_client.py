"""Local Ollama client — used for development (LLM_PROVIDER=ollama)."""

import httpx

from app import config

TIMEOUT = 180.0  # local models on CPU are slow


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or config.OLLAMA_MODEL

    def complete(self, prompt: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self.base_url}. Is `ollama serve` running?"
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()[:300]
            raise RuntimeError(f"Ollama returned {exc.response.status_code}: {detail}") from exc

        return response.json().get("response", "").strip()
