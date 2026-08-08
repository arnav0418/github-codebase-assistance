"""Retrieval + prompt construction + answer synthesis."""

from app import store
from app.llm import get_llm_client
from app.models import Citation

SYSTEM_PROMPT = """You are a code assistant answering questions about a specific \
Python codebase. Use only the code excerpts below — they are the retrieved context \
for this question. If they do not contain the answer, say so plainly instead of \
guessing.

Cite the code you rely on inline as `path/to/file.py:START-END`, matching the \
headers on the excerpts. Be concise and concrete."""

# Keep the assembled prompt bounded so a big top_k can't blow past context limits.
MAX_CONTEXT_CHARS = 24000


def build_prompt(question: str, hits: list[dict]) -> str:
    """Assemble the RAG prompt from retrieved chunks."""
    blocks: list[str] = []
    budget = MAX_CONTEXT_CHARS

    for hit in hits:
        header = (
            f"--- {hit['file_path']}:{hit['start_line']}-{hit['end_line']} "
            f"({hit['kind']} {hit['name']}) ---"
        )
        block = f"{header}\n```python\n{hit['code']}\n```"
        if len(block) > budget:
            break
        blocks.append(block)
        budget -= len(block)

    context = "\n\n".join(blocks) if blocks else "(no code retrieved)"
    return f"{SYSTEM_PROMPT}\n\n# Code excerpts\n\n{context}\n\n# Question\n\n{question}"


def answer_question(question: str, top_k: int) -> tuple[str, list[Citation]]:
    """Retrieve, prompt, call the LLM, and return (answer, citations)."""
    hits = store.search(question, top_k)
    if not hits:
        return (
            "No code has been indexed yet. Ingest a repository first, then ask again.",
            [],
        )

    answer = get_llm_client().complete(build_prompt(question, hits))

    citations = [
        Citation(
            file_path=hit["file_path"],
            name=hit["name"],
            kind=hit["kind"],
            start_line=hit["start_line"],
            end_line=hit["end_line"],
        )
        for hit in hits
    ]
    return answer, citations
