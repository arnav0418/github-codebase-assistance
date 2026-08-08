"""The one interface both LLM clients implement."""

from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Send `prompt` to the model and return the raw text answer."""
        ...
