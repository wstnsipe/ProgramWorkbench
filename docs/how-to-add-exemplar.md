# How to Add a New Exemplar / Template Document

Exemplars are real or sanitized acquisition documents uploaded to teach the
system what good documents look like. They are stored as `source_type = "exemplar"`
files and used to inject per-section style excerpts into LLM prompts.

---

## What exemplars do

At upload time, the backend:
1. Extracts full text from the file
2. Chunks it and stores in `file_chunks` / `rag_chunks` with `source_type = "exemplar"`
3. *(Future)* Runs a one-time LLM call to extract per-section style excerpts
   into the `exemplar_styles` table (`models_v2.py`)

At generation time, the orchestrator retrieves a matching style excerpt
(≤600 chars) for each section and injects it into the system prompt:
```
EXEMPLAR STYLE REFERENCE (match this tone and structure):
---
[excerpt here]
---
```

---

## Option A — Upload via the UI

1. Go to the **Exemplars** tab for any program
2. Upload a `.docx`, `.pdf`, or `.txt` file
3. The file is stored with `source_type = "exemplar"` and indexed

This is the normal path for per-program exemplars.

---

## Option B — Global reference exemplar (all programs)

Put the file in `backend/reference_docs/`. It will be indexed at startup
as a global `RagChunk` (no `program_id`) and retrieved alongside
program-specific chunks for all programs.

```bash
cp "My Exemplar Acq Strategy.docx" backend/reference_docs/
# Restart backend — indexed on startup automatically
```

To force re-indexing without restart:
```bash
# Hit the re-index endpoint (if exposed):
curl -X POST http://localhost:8000/admin/index-reference-docs
```

---

## Option C — Pre-seed exemplar styles (advanced)

For production quality, pre-extract per-section styles at file upload time.
This uses the `exemplar_styles` table (requires `models_v2.py` migration).

After uploading an exemplar, call the extraction endpoint:
```bash
curl -X POST http://localhost:8000/programs/{id}/files/{file_id}/extract-exemplar-styles \
  -H "Content-Type: application/json" \
  -d '{"doc_type": "acq_strategy"}'
```

*(This endpoint is not yet implemented — see `backend/generation/orchestrator.py`
`_get_exemplar_style()` for the retrieval side. Implement the extraction
endpoint when exemplar quality becomes a priority.)*

---

## File format tips

| Format | Notes |
|--------|-------|
| `.docx` | Best — heading structure preserved |
| `.pdf`  | Works — text extracted, no heading detection |
| `.txt`  | Fine for plain prose |
| `.doc`  | Not supported — convert to `.docx` first |

### Sanitizing exemplars

Before uploading real program documents:
- Replace all program names with `[PROGRAM NAME]`
- Replace all dollar amounts with `[$XXM]`
- Replace organization names with `[ORG]`
- Keep structural language intact — that's what the LLM learns from

---

## Checking what's indexed

```bash
# Via the Knowledge tab in the UI, or:
curl http://localhost:8000/programs/{id}/knowledge/status
```

For global reference docs:
```sql
SELECT source_filename, COUNT(*) as chunks
FROM rag_chunks
WHERE program_id IS NULL
GROUP BY source_filename;
```
