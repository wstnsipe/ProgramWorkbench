# Local Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (for Postgres)
- An OpenAI API key

---

## 1. Clone and configure environment

```bash
git clone <repo-url>
cd acq-program-workbench
cp backend/.env.example backend/.env      # edit with your values
cp frontend/.env.example frontend/.env    # edit with your values
```

See [env-vars.md](env-vars.md) for what to put in each file.

---

## 2. Start Postgres

The app requires PostgreSQL 16 with the `pgvector` extension.

```bash
docker compose up -d
```

This starts `acq_workbench_db` on port **5433** (not 5432, to avoid conflicts).

Verify:
```bash
docker compose ps
# should show: acq_workbench_db   running
```

---

## 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create tables (runs SQLAlchemy `create_all` on startup automatically, but you can also run):
```bash
python -c "from database import engine; from models import Base; Base.metadata.create_all(engine)"
```

If you've added models from `models_v2.py`, run the migration SQL:
```bash
psql postgresql://acq:acqpass@127.0.0.1:5433/acq_workbench < docs/migration_v2.sql
```

Start the dev server:
```bash
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:5173

---

## 5. Verify end-to-end

1. Open http://localhost:5173
2. Create a program
3. Open the Brief tab, fill in description and service branch
4. Upload a file in the Upload tab
5. Go to Documents tab → generate an RFI
6. Download the `.docx`

If generation fails with a 503, check that `OPENAI_API_KEY` is set in `backend/.env`.

---

## Common issues

| Problem | Fix |
|---------|-----|
| `pgvector` not found | Make sure you used the `pgvector/pgvector:pg16` Docker image, not plain `postgres` |
| `DATABASE_URL` connection refused | Check Docker is running and port 5433 is mapped correctly |
| `OPENAI_API_KEY not set` | Add it to `backend/.env` |
| Frontend shows blank page | Check `VITE_API_BASE_URL` in `frontend/.env` points to `http://localhost:8000` |
| `create_all` drops no tables | Expected — SQLAlchemy `create_all` is additive only. Use Alembic or raw SQL for schema changes. |

---

## Resetting the database

```bash
docker compose down -v    # removes the volume — all data deleted
docker compose up -d
# tables recreated on next backend startup
```
