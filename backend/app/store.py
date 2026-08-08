"""Embeddings (sentence-transformers) + vector store (Chroma, on-disk)."""

import os
from functools import lru_cache

# Must be set before chromadb is imported — it reads this at import time.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402
from chromadb.config import Settings  # noqa: E402

from app import config  # noqa: E402
from app.chunker import Chunk  # noqa: E402

# Cap what we hand the embedder per chunk. MiniLM truncates at 256 word pieces
# anyway; this just keeps a pathological chunk from blowing up memory.
MAX_CHARS = 8000

# Small batches keep peak RSS down on a 512MB dyno.
BATCH_SIZE = 32


@lru_cache(maxsize=1)
def get_embedder():
    """Return a lazily-loaded, process-wide SentenceTransformer instance."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.EMBEDDING_MODEL, device="cpu")


@lru_cache(maxsize=1)
def _client():
    return chromadb.PersistentClient(
        path=config.CHROMA_DIR,
        # Chroma's telemetry is noisy and errors against some posthog versions.
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection():
    """Return the persistent Chroma collection, creating it if needed."""
    return _client().get_or_create_collection(
        name=config.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    vectors = embedder.encode(
        [t[:MAX_CHARS] for t in texts],
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return [v.tolist() for v in vectors]


def _embed_text(chunk: Chunk) -> str:
    """What actually gets embedded — the path and symbol name matter as much as
    the body for questions phrased in terms of names."""
    return f"{chunk.file_path} :: {chunk.kind} {chunk.name}\n\n{chunk.code}"


def index_chunks(repo: str, chunks: list[Chunk]) -> int:
    """Embed `chunks` and upsert them into Chroma. Return the count stored."""
    if not chunks:
        return 0

    collection = get_collection()
    stored = 0

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        collection.upsert(
            ids=[
                f"{repo}:{c.file_path}:{c.start_line}-{c.end_line}:{c.name}"
                for c in batch
            ],
            embeddings=_embed([_embed_text(c) for c in batch]),
            documents=[c.code[:MAX_CHARS] for c in batch],
            metadatas=[
                {
                    "repo": repo,
                    "file_path": c.file_path,
                    "name": c.name,
                    "kind": c.kind,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                }
                for c in batch
            ],
        )
        stored += len(batch)

    return stored


def search(question: str, top_k: int) -> list[dict]:
    """Embed `question` and return the top_k matching chunks with metadata."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=_embed([question]),
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Chroma nests results one level per query; we only ever send one.
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    return [
        {"code": doc, "distance": dist, **meta}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]


def reset_collection() -> None:
    """Drop and recreate the collection (used before re-ingesting a repo)."""
    try:
        _client().delete_collection(config.CHROMA_COLLECTION)
    except Exception:
        # Nothing to delete on a cold start.
        pass
    get_collection()
