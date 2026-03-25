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

from database import Base, engine

# Import new models so Alembic / create_all sees them
import models  # noqa: F401
try:
    import models_v2  # noqa: F401
except Exception:
    pass

from routers import programs, wizard, modules, scenarios, standards, sufficiency, files, documents

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(programs.router)
app.include_router(wizard.router)
app.include_router(modules.router)
app.include_router(scenarios.router)
app.include_router(standards.router)
app.include_router(sufficiency.router)
app.include_router(files.router)
app.include_router(documents.router)


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
