"""Embeddings (sentence-transformers) + vector store (Chroma, on-disk)."""

from app.chunker import Chunk


def get_embedder():
    """Return a lazily-loaded, process-wide SentenceTransformer instance.

    TODO: implement — load config.EMBEDDING_MODEL once and cache it. Loading is
    slow and memory-hungry; must not happen per-request on a 512MB Render dyno.
    """
    raise NotImplementedError


def get_collection():
    """Return the persistent Chroma collection, creating it if needed.

    TODO: implement — chromadb.PersistentClient(path=config.CHROMA_DIR).
    """
    raise NotImplementedError


def index_chunks(repo: str, chunks: list[Chunk]) -> int:
    """Embed `chunks` and upsert them into Chroma. Return the count stored.

    TODO: implement — batch the encode call, store file_path/name/kind/start_line/
    end_line/repo as metadata, use a stable id like f"{repo}:{path}:{start}-{end}".
    """
    raise NotImplementedError


def search(question: str, top_k: int) -> list[dict]:
    """Embed `question` and return the top_k matching chunks with metadata.

    TODO: implement.
    """
    raise NotImplementedError


def reset_collection() -> None:
    """Drop and recreate the collection (used before re-ingesting a repo).

    TODO: implement.
    """
    raise NotImplementedError
