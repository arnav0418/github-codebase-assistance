"""Retrieval + prompt construction + answer synthesis."""

from app.models import Citation


def build_prompt(question: str, hits: list[dict]) -> str:
    """Assemble the RAG prompt from retrieved chunks.

    TODO: implement — system framing, then each chunk labelled with its
    file:start-end so the model can cite, then the question.
    """
    raise NotImplementedError


def answer_question(question: str, top_k: int) -> tuple[str, list[Citation]]:
    """Retrieve, prompt, call the LLM, and return (answer, citations).

    TODO: implement — store.search -> build_prompt -> get_llm_client().complete,
    and map the hits' metadata into Citation objects.
    """
    raise NotImplementedError
