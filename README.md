# Codebase Assist — Workspace Overview

A RAG (retrieval-augmented generation) chat app for exploring a GitHub Python
repository. Point it at a repo URL; it clones the repo, chunks the code at
function/class granularity with tree-sitter, embeds the chunks locally, and
answers natural-language questions with `file:line` citations back to the
source.

**Scope (v1):** Python repositories only. One repo indexed at a time (a new
ingest replaces the old index). Embeddings always run locally via
sentence-transformers; answer synthesis switches between local Ollama and
Gemini depending on `LLM_PROVIDER`.

## Architecture at a glance

```
GitHub repo URL
      │  POST /ingest
      ▼
 ingest.py     shallow git clone, walk *.py files (skips venvs/build dirs, >512KB files)
      │
      ▼
 chunker.py    tree-sitter parse → one Chunk per top-level function/class;
               leftover top-level code grouped into "<module>" runs;
               unparseable files fall back to one whole-file chunk
      │
      ▼
 store.py      embed each chunk (sentence-transformers, all-MiniLM-L6-v2)
               and upsert into a local persistent Chroma collection

 --- separately, per question ---

GET question
      │  POST /query
      ▼
 store.search()   embed the question, cosine-similarity top_k against Chroma
      ▼
 query.py         build a bounded-size prompt from the retrieved chunks
      ▼
 llm/*            get_llm_client() picks Ollama or Gemini via LLM_PROVIDER
      ▼
 answer + citations (file_path, name, kind, start_line, end_line) returned to the frontend
```

## Repository layout

```
backend/
  app/
    main.py         FastAPI app — POST /ingest, POST /query, GET /health
    config.py       env-driven configuration (no hardcoded secrets)
    models.py       Pydantic request/response schemas
    ingest.py       GitHub URL parsing, shallow clone, .py file walk
    chunker.py      tree-sitter structural chunking (functions/classes/module)
    store.py        sentence-transformers embeddings + Chroma persistence
    query.py        prompt assembly + answer/citation synthesis
    llm/
      __init__.py       get_llm_client() — the single LLM_PROVIDER branch point
      base.py           LLMClient interface
      ollama_client.py  local Ollama chat completion
      gemini_client.py  Gemini API chat completion
  requirements.txt
  Dockerfile
  .env.example
frontend/
  src/
    App.jsx             top-level layout: RepoInput + Chat
    api.js               fetch wrappers for /ingest and /query
    components/
      RepoInput.jsx       repo URL form, triggers ingest
      Chat.jsx            question input + message list
      Citations.jsx       renders file:line citation chips
    styles.css
  package.json
  vite.config.js
  .env.example
render.yaml           Render Blueprint: Docker backend, health check on /health
README.md             full setup/deploy instructions (this file summarizes it)
```

## Backend design notes

- **Chunking** (`chunker.py`): each top-level `function_definition` /
  `class_definition` becomes its own chunk, decorators included in the line
  span; methods stay nested inside their class chunk rather than being
  indexed separately. Non-def top-level code (imports, constants, `__main__`
  guards) is grouped into contiguous `<module>` chunks so every chunk's
  `start_line`–`end_line` is honest. Files that fail to parse fall back to a
  single whole-file chunk.
- **Embedding text** (`store.py`): each chunk is embedded as
  `path :: kind name\n\n<code>` so symbol-name questions match as well as
  behavioral questions.
- **Retrieval** (`store.py`/`query.py`): cosine distance over Chroma;
  `TOP_K` chunks go to the LLM and *all* of them come back as citations.
  Prompt size is capped (`MAX_CONTEXT_CHARS`) so a large `top_k` can't blow
  past model context limits.
- **LLM provider switch** (`llm/__init__.py`): the only place in the codebase
  that branches on `LLM_PROVIDER`; each concrete client implements a common
  `LLMClient.complete()` interface.
- **Safety/limits**: `ingest.py` skips `.git`, virtualenvs, `node_modules`,
  caches, and build dirs, and skips any file over 512KB; GitHub URLs are
  validated against a strict `owner/repo` pattern before shelling out to
  `git clone --depth 1`.

## Configuration (env vars)

| Var | Default | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | |
| `OLLAMA_MODEL` | `llama3.1` | any model from `ollama list` |
| `GEMINI_API_KEY` | — | required when `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-3.5-flash` | `gemini-2.5-flash*` 404s for newer API keys |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | always local, both modes |
| `CHROMA_DIR` | `./chroma_data` | on-disk vector store path |
| `CHROMA_COLLECTION` | `code_chunks` | |
| `TOP_K` | `8` | chunks retrieved per query |
| `CLONE_DIR` | `./repo_cache` | |
| `CORS_ORIGINS` | `http://localhost:5173` | comma-separated |

## API surface

- `POST /ingest` — `{ "repo_url": "https://github.com/owner/repo" }` →
  `{ "repo", "files_indexed", "chunks_indexed" }`
- `POST /query` — `{ "question": "...", "top_k": 8 }` →
  `{ "answer", "citations": [{ file_path, name, kind, start_line, end_line }] }`
- `GET /health` — `{ "status": "ok", "llm_provider": "ollama" | "gemini" }`

## Running locally

```bash
# backend
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
ollama pull llama3.1   # or set OLLAMA_MODEL to something already pulled

# frontend
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev             # http://localhost:5173
```

## Verified behavior

Both LLM providers were exercised end-to-end:

| | Ollama (`gemma3:12b`) | Gemini (`gemini-3.5-flash`) |
| --- | --- | --- |
| Repo | `benoitc/http-parser` | `psf/requests` |
| Ingest | 16 files → 75 chunks, 26s | 36 files → 281 chunks, 21s |
| Query latency | 15–19s | 4–9s |
| Citations resolving to real definitions | 8/8 | 16/16 |

Retrieval correctly ranked `class Response` first for *"what class
represents an HTTP response"* and `class SessionRedirectMixin` first for
*"how does this library handle redirects."* Where retrieved context
genuinely lacked the answer, the model said so instead of guessing.
