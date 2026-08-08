"""Environment-driven configuration. No secrets hardcoded."""

import os

# --- LLM provider ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Embeddings (always local, same in dev and prod) ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Vector store ---
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_data")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "code_chunks")

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "8"))

# --- Ingest ---
CLONE_DIR = os.getenv("CLONE_DIR", "./repo_cache")

# --- CORS: comma-separated list of allowed origins ---
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
