"""FastAPI app: /ingest and /query."""

import gc
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import config, ingest as ingest_mod, query as query_mod, store
from app.chunker import chunk_python_file
from app.models import IngestRequest, IngestResponse, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Codebase RAG Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": config.LLM_PROVIDER}


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    """Clone -> walk .py files -> chunk -> embed -> store (streaming to cap memory)."""
    try:
        slug, checkout = ingest_mod.clone_repo(req.repo_url, config.CLONE_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # v1 indexes one repo at a time, so a new ingest replaces the old index.
    store.reset_collection()
    # Force garbage collection to free old HNSW index before building new one.
    gc.collect()

    files_indexed = 0
    chunks_indexed = 0

    for file_index, (relative_path, absolute_path) in enumerate(
        ingest_mod.iter_python_files(checkout)
    ):
        try:
            with open(absolute_path, encoding="utf-8", errors="replace") as handle:
                source = handle.read()
        except OSError:
            continue

        chunks = chunk_python_file(relative_path, source)
        if not chunks:
            del source, chunks
            continue

        files_indexed += 1
        # Stream chunks one at a time to avoid holding all chunks in memory.
        # This keeps peak memory per file constant rather than linear in file count.
        for chunk in chunks:
            chunks_indexed += store.index_chunks(slug, [chunk])
            del chunk

        # Free source and chunk list before next file.
        del source, chunks

        # Garbage collect after each file to keep memory usage flat.
        gc.collect()

    if chunks_indexed == 0:
        raise HTTPException(
            status_code=422, detail=f"No Python files found in {slug}"
        )

    # Final garbage collection to restore clean state.
    gc.collect()

    logger.info("indexed %s: %d files, %d chunks", slug, files_indexed, chunks_indexed)
    return IngestResponse(
        repo=slug, files_indexed=files_indexed, chunks_indexed=chunks_indexed
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """Embed question -> retrieve top-k -> prompt LLM -> answer + citations."""
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    top_k = req.top_k or config.TOP_K
    try:
        answer, citations = query_mod.answer_question(question, top_k)
    except RuntimeError as exc:
        # LLM provider unreachable / misconfigured.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(answer=answer, citations=citations)
