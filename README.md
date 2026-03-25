# ACQ Program Workbench

AI-powered document generation for DoD acquisition program offices. Given a program brief, candidate modules, MOSA scenarios, and supporting files, the app generates grounded acquisition documents (RFI, Acquisition Strategy, SEP, MOSA Conformance Plan).

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19 + Vite + TypeScript |
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL 16 + pgvector |
| AI | OpenAI (GPT-4o, text-embedding-3-small) |
| Frontend hosting | Vercel |
| Backend hosting | Railway |

## Repo layout

```
acq-program-workbench/
├── backend/                   FastAPI app
│   ├── main.py                All routes (monolith; see routers/ for v2)
│   ├── models.py              SQLAlchemy ORM models
│   ├── schemas.py             Pydantic request/response schemas
│   ├── document_templates.py  TEMPLATE_REGISTRY — section order, formats, required fields
│   ├── docx_builder.py        DOCX rendering (python-docx)
│   ├── config/
│   │   └── questions.yaml     Wizard question definitions
│   ├── reference_docs/        MIG and policy PDFs — indexed at startup
│   ├── rules/                 Deterministic rules engine (no LLM)
│   ├── generation/            Section-by-section LLM generation pipeline
│   ├── routers/               Modular FastAPI routers (v2 path)
│   ├── services/              Business logic layer
│   └── llm/                   OpenAI client, RAG retrieval, context builder
├── frontend/                  React + Vite app
│   └── src/
│       ├── api/               Typed API client
│       ├── hooks/             Custom React hooks per domain
│       ├── components/        Shared UI components
│       ├── types/index.ts     All TypeScript interfaces
│       └── pages/             Tab-based workspace pages
├── docs/                      Developer guides (you are here)
├── docker-compose.yml         Local Postgres + pgvector
└── Procfile                   Railway startup command
```

## Quick start

See [docs/local-setup.md](docs/local-setup.md).

## Developer guides

- [docs/local-setup.md](docs/local-setup.md) — environment setup
- [docs/env-vars.md](docs/env-vars.md) — all environment variables
- [docs/how-to-add-wizard-question.md](docs/how-to-add-wizard-question.md)
- [docs/how-to-add-rule.md](docs/how-to-add-rule.md)
- [docs/how-to-add-document-type.md](docs/how-to-add-document-type.md)
- [docs/how-to-add-exemplar.md](docs/how-to-add-exemplar.md)
- [docs/how-to-add-mig-source.md](docs/how-to-add-mig-source.md)
- [docs/deployment.md](docs/deployment.md) — Vercel + Railway
- [docs/prompt-design.md](docs/prompt-design.md) — LLM prompt principles

## Architecture in one paragraph

The backend holds four data layers per program: (1) user-entered facts in `program_briefs` and `program_answers`, (2) extracted text from uploaded files in `file_chunks` with pgvector embeddings, (3) deterministic rules-engine outputs (MIG selection, DocModifiers) computed from the facts, and (4) LLM-generated document sections grounded in all three. Document generation is section-by-section — each section gets a focused system prompt, a fact pack, retrieved chunks, and an exemplar style excerpt.
