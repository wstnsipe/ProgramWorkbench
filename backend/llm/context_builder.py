"""Program context builder – assembles and persists a program knowledge snapshot.

Output: backend/data/programs/{id}/context/context.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_program_context(
    program,
    brief,
    answers: dict,
    modules: list,
    files: list,
    data_dir: Path,
) -> dict:
    """Assemble a context dict from all program knowledge and save to context.json."""
    brief_data = None
    if brief:
        brief_data = {
            "program_description": brief.program_description,
            "dev_cost_estimate": brief.dev_cost_estimate,
            "production_unit_cost": brief.production_unit_cost,
            "attritable": brief.attritable,
            "sustainment_tail": brief.sustainment_tail,
            "software_large_part": brief.software_large_part,
            "mission_critical": brief.mission_critical,
            "safety_critical": brief.safety_critical,
        }

    modules_data = [
        {
            "id": m.id,
            "name": m.name,
            "rationale": m.rationale,
            "key_interfaces": m.key_interfaces,
            "standards": m.standards,
            "tech_risk": m.tech_risk,
            "obsolescence_risk": m.obsolescence_risk,
            "cots_candidate": m.cots_candidate,
        }
        for m in modules
    ]

    files_data = [
        {
            "id": f.id,
            "filename": f.filename,
            "extracted_text_chars": len(f.extracted_text or ""),
        }
        for f in files
    ]

    ctx = {
        "program_id": program.id,
        "program_name": program.name,
        "brief": brief_data,
        "wizard_answers": {k: v for k, v in answers.items() if v},
        "modules": modules_data,
        "files": files_data,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }

    ctx_dir = data_dir / "programs" / str(program.id) / "context"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "context.json").write_text(json.dumps(ctx, indent=2, default=str))
    return ctx


def load_context(program_id: int, data_dir: Path) -> dict | None:
    """Load an existing context.json, return None if not present."""
    path = data_dir / "programs" / str(program_id) / "context" / "context.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def context_summary_and_gaps(ctx: dict) -> tuple[str, list[str]]:
    """Return (one-line summary, list of missing-info questions)."""
    missing: list[str] = []
    brief = ctx.get("brief") or {}
    answers = ctx.get("wizard_answers") or {}

    if not brief.get("program_description") and not answers.get("a_program_description"):
        missing.append("What is the program description?")
    if not ctx.get("modules"):
        missing.append("What modules has the program been decomposed into? (add via Modules tab)")
    if not answers.get("g_mosa_scenarios"):
        missing.append("What are the program-specific MOSA scenarios? (wizard question g)")
    if not answers.get("i_known_standards_architectures_mapping"):
        missing.append(
            "What standards and architectures apply to each module? (wizard question i)"
        )
    if not answers.get("f_tech_challenges_and_risk_areas"):
        missing.append(
            "What are the technical challenges and risk areas? (wizard question f)"
        )
    if not ctx.get("files"):
        missing.append(
            "No reference documents uploaded. Consider uploading program docs for richer context."
        )

    n_modules = len(ctx.get("modules") or [])
    n_files = len(ctx.get("files") or [])
    n_answers = len(answers)
    summary = (
        f"Context built for program '{ctx['program_name']}': "
        f"{n_modules} module(s), {n_files} uploaded file(s), "
        f"{n_answers} wizard answer(s) available."
    )
    return summary, missing
