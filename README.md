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

## Deployment (Gemini + Render + Vercel)

There is a chicken-and-egg between the two services: the backend needs the frontend's
origin for CORS, and the frontend needs the backend's URL. Deploy the backend first with
a placeholder, then come back and fix it in step 5.

### 1. Get a Gemini API key

Create one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Check it
works before deploying — see the model-availability note under [Notes](#notes) if you get
a 404:

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Say READY"}]}]}'
```

### 2. Deploy the backend to Render

`render.yaml` defines the service (Docker runtime, `rootDir: backend`, health check on
`/health`). Either use Render's **Blueprint** flow (New → Blueprint → pick this repo,
which reads `render.yaml`), or create a web service manually with runtime **Docker**,
root directory **`backend`**, and the env vars below.

Two values are `sync: false` in `render.yaml` and must be set in the dashboard:

| Var | Value |
| --- | --- |
| `GEMINI_API_KEY` | your key from step 1 |
| `CORS_ORIGINS` | `https://placeholder.vercel.app` for now — corrected in step 5 |

Everything else (`LLM_PROVIDER=gemini`, `GEMINI_MODEL`, `EMBEDDING_MODEL`, `TOP_K`, and
`CHROMA_DIR`/`CLONE_DIR` pointed at `/tmp`) comes from `render.yaml`.

The first build takes roughly 5–10 minutes — it installs CPU-only torch and bakes the
embedding model into the image so cold starts don't re-download it.

### 3. Verify the backend

```bash
curl https://<your-service>.onrender.com/health
# {"status":"ok","llm_provider":"gemini"}
```

If this 404s, the service is still building. If it hangs ~50s then responds, that's a
cold start, not a fault.

### 4. Deploy the frontend to Vercel

Import the repo, set **Root Directory** to `frontend` (Vercel auto-detects Vite; no
`vercel.json` needed), and set one env var:

| Var | Value |
| --- | --- |
| `VITE_API_URL` | `https://<your-service>.onrender.com` — no trailing slash |

### 5. Close the CORS loop

Go back to Render, set `CORS_ORIGINS` to your real Vercel origin
(`https://<your-app>.vercel.app`, no trailing slash, no path), and let it redeploy.

**This is the step people miss.** Skip it and the app loads fine but every request fails
with a CORS error in the browser console while `curl` still works — because `curl` doesn't
send an `Origin` header. Verify the preflight from the terminal:

```bash
curl -s -o /dev/null -D - -X OPTIONS \
  https://<your-service>.onrender.com/query \
  -H "Origin: https://<your-app>.vercel.app" \
  -H "Access-Control-Request-Method: POST" | grep -i access-control-allow-origin
# access-control-allow-origin: https://<your-app>.vercel.app
```

No header in the output means `CORS_ORIGINS` doesn't match your origin exactly.

### 6. Smoke-test end to end

Open the Vercel URL, ingest a small repo, and ask a question. Start small —
`psf/requests` indexes 36 files / 281 chunks in about 20s locally and takes longer on
0.1 CPU.

### Free-tier caveats

**Memory is the real constraint.** Measured peak is ~418MB against the 512MB cap, with
~94MB of headroom. That overhead is nearly all fixed — torch plus the model weights —
not proportional to index size (100 vs 400 chunks differed by ~9MB in testing), so large
repos cost ingest *time*, not much extra memory. If you hit OOM restarts, the culprit is
usually a raised `TOP_K` or a second worker process; keep uvicorn at one worker.

**Cold starts.** The service sleeps after 15 minutes idle and takes ~50s to wake. The
first request after a deploy also pays a one-time embedding-model load of a few seconds.

**Data is ephemeral.** Chroma writes to the container's disk, so the index is lost on
redeploy and on sleep — **re-ingest the repo when that happens.** Intentional for v1; no
hosted vector DB or volume mounting.

**Ingest is synchronous.** A very large repo can exceed Render's request timeout. Stick
to small and mid-sized repos on the free tier.

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
