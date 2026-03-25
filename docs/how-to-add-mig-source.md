# How to Add a New MIG Reference Source

MIG (Modular Implementation Guide) documents are global reference PDFs that
ground MOSA requirements in service-specific policy. They are indexed once
at startup and retrieved during document generation for all programs.

---

## Step 1 — Add the file

Drop the PDF (or `.docx`) into:
```
backend/reference_docs/
```

Name it clearly so the source is traceable in citations:
```
MIG-USAF-2021.pdf
MIG-USN-2022.pdf
MIG-USSF-2023.pdf
MIG-ARMY-2022.pdf
```

---

## Step 2 — Register the MIG ID (if adding a new branch/variant)

**File:** `backend/rules/engine.py`

Update the lookup tables:

```python
_SERVICE_TO_MIG: dict[str, str] = {
    "USN":  "MIG-USN-2022",
    "USAF": "MIG-USAF-2021",
    "USSF": "MIG-USSF-2023",
    "ARMY": "MIG-ARMY-2022",
    "USMC": "MIG-USMC-2024",    # ← new branch
}
```

For an Army PAE sub-variant:
```python
_ARMY_PAE_TO_MIG: dict[str, str] = {
    "PM_PEO_C3T":   "MIG-ARMY-C3T-2022",
    "PM_PEO_IEW_S": "MIG-ARMY-IEWS-2022",
    "PM_YOUR_PAE":  "MIG-ARMY-YOURPAE-2024",   # ← new PAE
}
```

---

## Step 3 — Restart the backend

On startup, `index_reference_docs()` in `backend/llm/retrieval.py` checks
whether global `RagChunk` rows already exist. If they do, it skips indexing.

To force re-indexing after adding a new file:

```bash
# Option A: clear existing global chunks and restart
psql $DATABASE_URL -c "DELETE FROM rag_chunks WHERE program_id IS NULL;"
uvicorn main:app --reload

# Option B: (safer) check what's already indexed first
psql $DATABASE_URL -c "SELECT source_filename, COUNT(*) FROM rag_chunks WHERE program_id IS NULL GROUP BY source_filename;"
```

---

## Step 4 — Add the branch to the frontend (if new service branch)

**File:** `frontend/src/components/brief/ServiceBranchField.tsx`

```tsx
const BRANCHES = [
  { value: 'USN',  label: 'Navy (USN)',          mig: 'MIG-USN-2022'  },
  { value: 'USAF', label: 'Air Force (USAF)',     mig: 'MIG-USAF-2021' },
  { value: 'USSF', label: 'Space Force (USSF)',   mig: 'MIG-USSF-2023' },
  { value: 'ARMY', label: 'Army',                 mig: 'MIG-ARMY-2022' },
  { value: 'USMC', label: 'Marine Corps (USMC)',  mig: 'MIG-USMC-2024' }, // ← add
]
```

**File:** `frontend/src/types/index.ts`

```typescript
export type ServiceBranch = 'USN' | 'USAF' | 'USSF' | 'ARMY' | 'USMC'
```

---

## How MIG content is used in generation

During document generation, the orchestrator:
1. Sets `mig_id` from the rules engine (e.g., `"MIG-USAF-2021"`)
2. Passes it in the fact pack to relevant sections (MOSA sections especially)
3. Retrieval pulls chunks from the matching MIG file via `source_filename` metadata

The LLM sees both the `mig_id` value in the fact pack and the actual MIG
text in the retrieved chunks — this grounds MOSA requirements in the
specific service's policy.

---

## Verifying retrieval

To check that a new MIG is being retrieved for a specific program:
```bash
curl "http://localhost:8000/programs/{id}/knowledge/search?q=modular+open+systems"
```

Or check the Knowledge tab in the UI after generation.
