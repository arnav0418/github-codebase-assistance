# Codebase RAG Assistant

Chat with a GitHub repo. Point it at a Python repository; it clones the repo, chunks
the code structurally with tree-sitter (function/class granularity, not fixed-size text
splitting), embeds the chunks locally, and answers questions with `file:line` citations.

**Scope (v1):** Python repos only. Chroma on local disk. Embeddings always run in-process
via sentence-transformers. Answer synthesis switches between local Ollama and Gemini.

## Structure

```
backend/
  app/
    main.py         FastAPI app — /ingest, /query, /health
    config.py       env-driven config
    models.py       request/response schemas
    ingest.py       shallow clone + .py file walk
    chunker.py      tree-sitter function/class chunking
    store.py        sentence-transformers embeddings + Chroma
    query.py        retrieval, prompt building, answer + citations
    llm/
      __init__.py   get_llm_client() — the only LLM_PROVIDER branch
      base.py       LLMClient interface
      ollama_client.py
      gemini_client.py
  requirements.txt
  Dockerfile
  .env.example
frontend/
  src/
    App.jsx
    api.js          calls /ingest and /query
    components/     RepoInput, Chat, Citations
  package.json
  .env.example
render.yaml
```

## Local setup (Ollama)

Backend:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # defaults are already set for Ollama
uvicorn app.main:app --reload --port 8000
```

You also need Ollama running with a model pulled:

```bash
ollama pull llama3.1        # or any chat model you already have
```

To use a model other than the default, set `OLLAMA_MODEL` in `backend/.env` —
e.g. `OLLAMA_MODEL=gemma3:12b`. `ollama list` shows what's installed locally.

Frontend:

```bash
cd frontend
npm install
cp .env.example .env       # VITE_API_URL=http://localhost:8000
npm run dev                # http://localhost:5173
```

### Local env vars

| Var | Default | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | |
| `OLLAMA_MODEL` | `llama3.1` | any model from `ollama list` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | always local, both modes |
| `CHROMA_DIR` | `./chroma_data` | |
| `CHROMA_COLLECTION` | `code_chunks` | |
| `TOP_K` | `8` | chunks retrieved per query |
| `CLONE_DIR` | `./repo_cache` | |
| `CORS_ORIGINS` | `http://localhost:5173` | comma-separated |

## Deployed setup (Gemini + Render + Vercel)

### Backend → Render (free web service)

`render.yaml` at the repo root defines the service (Docker runtime, `rootDir: backend`,
health check on `/health`). Either commit it and use Render's Blueprint flow, or create a
web service manually with: runtime Docker, root directory `backend`, and the env vars below.

Set in the Render dashboard (both are `sync: false` in `render.yaml`):

- `GEMINI_API_KEY` — your Google AI Studio key
- `CORS_ORIGINS` — your Vercel origin, e.g. `https://your-app.vercel.app`

Already set by `render.yaml`: `LLM_PROVIDER=gemini`, `GEMINI_MODEL=gemini-2.5-flash`,
`EMBEDDING_MODEL`, `TOP_K`, and `CHROMA_DIR`/`CLONE_DIR` pointed at `/tmp`.

### Frontend → Vercel

Import the repo, set the root directory to `frontend` (Vercel detects Vite), and set:

- `VITE_API_URL` — your Render URL, e.g. `https://codebase-assist-api.onrender.com`

### Free-tier caveats

The Render free tier gives 512MB RAM / 0.1 CPU and sleeps after 15 minutes idle, so the
first request after a sleep is slow. Chroma writes to the container's ephemeral disk —
**index data is lost on redeploy or sleep, so re-ingest the repo when that happens.**
This is intentional for v1; no hosted vector DB or volume mounting.

## API

`POST /ingest` — `{ "repo_url": "https://github.com/owner/repo" }` →
`{ "repo": "owner/repo", "files_indexed": 42, "chunks_indexed": 310 }`

`POST /query` — `{ "question": "How does auth work?", "top_k": 8 }` →
`{ "answer": "...", "citations": [{ "file_path": "...", "name": "...", "kind": "function", "start_line": 10, "end_line": 42 }] }`

`GET /health` — `{ "status": "ok", "llm_provider": "ollama" }`

## How chunking works

`chunker.py` parses each file with tree-sitter and emits one chunk per top-level
function and class, with decorators included in the line span. Methods stay inside
their class rather than being indexed twice. Leftover top-level code (imports,
constants, `if __name__ == "__main__"` blocks) is grouped into `<module>` chunks,
split into contiguous runs so every chunk's `start_line`–`end_line` honestly covers
its own content. Files that fail to parse fall back to a single whole-file chunk.

Each chunk is embedded as `path :: kind name` plus the code body, so questions
phrased in terms of symbol names match as well as questions about behavior.

## Notes

- `/ingest` indexes one repo at a time — ingesting a new repo resets the collection.
- Retrieval uses cosine distance; `TOP_K` chunks are passed to the LLM, and every
  retrieved chunk is returned as a citation.
- Files over 512KB are skipped as likely generated or vendored.
- **Gemini model availability:** `gemini-2.5-flash` (and `-flash-lite`) return 404
  for API keys created after their cutoff — "no longer available to new users".
  The default is `gemini-3.5-flash`. If you hit a 404 naming the model, list what
  your key can actually call:
  ```bash
  curl -s -H "x-goog-api-key: $GEMINI_API_KEY" \
    https://generativelanguage.googleapis.com/v1beta/models
  ```
  Note the listing includes models your key may still be refused for — test before
  relying on one.

## Verified

Both providers were exercised end to end against real repositories:

| | Ollama (`gemma3:12b`) | Gemini (`gemini-3.5-flash`) |
| --- | --- | --- |
| Repo | `benoitc/http-parser` | `psf/requests` |
| Ingest | 16 files → 75 chunks, 26s | 36 files → 281 chunks, 21s |
| Query latency | 15–19s | 4–9s |
| Citations resolving to real definitions | 8/8 | 16/16 |

Retrieval ranked `class Response` first for *"what class represents an HTTP
response"* and `class SessionRedirectMixin` first for *"how does this library
handle redirects"*. Where the retrieved context genuinely lacked the answer, the
model said so rather than inventing one.
