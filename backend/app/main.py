"""FastAPI app: /ingest and /query."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.models import IngestRequest, IngestResponse, QueryRequest, QueryResponse

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
    """Clone -> walk .py files -> chunk -> embed -> store.

    TODO: implement — wire ingest.clone_repo, ingest.iter_python_files,
    chunker.chunk_python_file, store.index_chunks.
    """
    raise NotImplementedError


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """Embed question -> retrieve top-k -> prompt LLM -> answer + citations.

    TODO: implement — wire query.answer_question.
    """
    raise NotImplementedError
