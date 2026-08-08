"""Pydantic request/response schemas for the API."""

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL to ingest")


class IngestResponse(BaseModel):
    repo: str
    files_indexed: int
    chunks_indexed: int


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


class Citation(BaseModel):
    file_path: str
    name: str
    kind: str  # "function" | "class" | "module"
    start_line: int
    end_line: int


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
