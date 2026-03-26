"""
main_v2.py — New slim FastAPI app that mounts routers.

Migration path:
  1. This file runs alongside the existing main.py during transition.
  2. Move endpoints from main.py into routers/ one domain at a time.
  3. Once all endpoints are migrated, rename main_v2.py → main.py.

To test locally:
  uvicorn main_v2:app --reload --port 8001
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import Base, engine

# Import new models so Alembic / create_all sees them
import models  # noqa: F401
try:
    import models_v2  # noqa: F401
except Exception:
    pass

# Enable pgvector, create tables, run column migrations — all wrapped so a
# failure never prevents the app from starting.
try:
    with engine.connect() as _conn:
        try:
            _conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            _conn.commit()
        except Exception:
            _conn.rollback()
except Exception:
    pass

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

try:
    with engine.connect() as _conn:
        for _stmt in [
            "ALTER TABLE programs ADD COLUMN service_branch TEXT",
            "ALTER TABLE programs ADD COLUMN army_pae TEXT",
            "ALTER TABLE programs ADD COLUMN army_branch TEXT",
            "ALTER TABLE programs ADD COLUMN mig_id TEXT",
            "ALTER TABLE program_standards ADD COLUMN applies_to_modules BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE program_standards ADD COLUMN applies_to_interfaces BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE modules ADD COLUMN future_recompete BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE program_files ADD COLUMN extracted_text TEXT",
            "ALTER TABLE program_files ADD COLUMN source_type TEXT NOT NULL DEFAULT 'program_input'",
            "ALTER TABLE file_chunks ADD COLUMN source_type TEXT NOT NULL DEFAULT 'program_input'",
            "ALTER TABLE modules ADD COLUMN description TEXT",
        ]:
            try:
                _conn.execute(text(_stmt))
                _conn.commit()
            except Exception:
                _conn.rollback()
except Exception:
    pass

from routers import programs, brief, wizard, modules, scenarios, standards, sufficiency, files, documents, prefill, evidence

app = FastAPI(
    title="Acquisition Program Workbench API v2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(programs.router)
app.include_router(brief.router)
app.include_router(wizard.router)
app.include_router(modules.router)
app.include_router(scenarios.router)
app.include_router(standards.router)
app.include_router(sufficiency.router)
app.include_router(files.router)
app.include_router(documents.router)
app.include_router(prefill.router)
app.include_router(evidence.router)


# ---------------------------------------------------------------------------
# Mount legacy app for endpoints not yet migrated
# ---------------------------------------------------------------------------

try:
    from main import app as legacy_app  # type: ignore
    app.mount("/v1", legacy_app)
except Exception:
    pass  # main.py may not import cleanly in all environments


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
