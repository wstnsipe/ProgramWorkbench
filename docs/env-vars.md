# Environment Variables

## Backend — `backend/.env`

Create this file (not committed to git):

```bash
# ── Required ──────────────────────────────────────────────────────────────────

# PostgreSQL connection string
# Local dev: uses docker-compose.yml defaults
DATABASE_URL=postgresql://acq:acqpass@127.0.0.1:5433/acq_workbench

# OpenAI API key — required for document generation and embeddings
OPENAI_API_KEY=sk-...

# ── Optional ──────────────────────────────────────────────────────────────────

# OpenAI model for document generation
# Default: gpt-4o-mini  (change to gpt-4o for higher quality)
OPENAI_MODEL=gpt-4o-mini

# OpenAI model for embeddings
# Default: text-embedding-3-small
OPENAI_EMBED_MODEL=text-embedding-3-small

# Comma-separated list of allowed CORS origins
# In production, set to your Vercel frontend URL
FRONTEND_URL=https://your-app.vercel.app

# Max characters of context sent to the LLM per generation call
# Default: 12000  (increase with caution — affects cost and latency)
MAX_CONTEXT_CHARS=12000

# File upload directory (absolute or relative to backend/)
# Default: data/uploads
UPLOAD_DIR=data/uploads

# Generated document output directory
# Default: data/documents
OUTPUT_DIR=data/documents
```

### Railway deployment

In Railway, set these as environment variables in the service settings (not a file).
Railway automatically injects `DATABASE_URL` when you provision a Postgres plugin.
`PORT` is also injected by Railway — do not set it manually.

---

## Frontend — `frontend/.env`

Create this file (not committed to git):

```bash
# ── Required ──────────────────────────────────────────────────────────────────

# Backend API base URL — no trailing slash
# Local dev:
VITE_API_BASE_URL=http://localhost:8000

# Production (Railway backend URL):
# VITE_API_BASE_URL=https://your-backend.up.railway.app
```

### Vercel deployment

In Vercel → Project Settings → Environment Variables, set:

```
VITE_API_BASE_URL = https://your-backend.up.railway.app
```

This must be set **before** the build runs (Vite bakes it in at build time).

---

## Example files

Create these in the repo root (already in `.gitignore`):

**`backend/.env.example`** — commit this as a template:
```bash
DATABASE_URL=postgresql://acq:acqpass@127.0.0.1:5433/acq_workbench
OPENAI_API_KEY=sk-replace-me
OPENAI_MODEL=gpt-4o-mini
FRONTEND_URL=http://localhost:5173
MAX_CONTEXT_CHARS=12000
```

**`frontend/.env.example`**:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## Where each variable is read

| Variable | File | Default |
|----------|------|---------|
| `DATABASE_URL` | `backend/database.py:5` | `postgresql://acq:acqpass@127.0.0.1:5433/acq_workbench` |
| `OPENAI_API_KEY` | `backend/llm/client.py:8` | *(none — fails at runtime)* |
| `OPENAI_MODEL` | `backend/llm/client.py:17` | `gpt-4o-mini` |
| `OPENAI_EMBED_MODEL` | `backend/rag.py:20` | `text-embedding-3-small` |
| `FRONTEND_URL` | `backend/main.py:49` | *(empty — localhost origins added by default)* |
| `MAX_CONTEXT_CHARS` | `backend/main.py:1220` | `12000` |
| `UPLOAD_DIR` | `backend/routers/files.py:18` | `data/uploads` |
| `OUTPUT_DIR` | `backend/routers/documents.py:19` | `data/documents` |
| `VITE_API_BASE_URL` | `frontend/src/api/client.ts:6` | *(none — build fails)* |
