"""
services/exemplar_service.py — Extract per-section style excerpts from exemplar files.

Called after an exemplar file is uploaded. Writes ExemplarStyle rows that are
later retrieved by generation/orchestrator.py _get_exemplar_style().
"""
import logging
import os
import re

logger = logging.getLogger(__name__)

# Section name patterns to search for in exemplar text.
# Matches the exemplar_pattern values defined in orchestrator.py SectionDefs.
_SECTION_PATTERNS = [
    "executive summary",
    "program overview",
    "acquisition approach",
    "mosa",
    "milestone",
    "schedule",
    "cost",
    "data rights",
    "test",
    "verification",
    "risk",
    "contract",
    "overview",
    "module",
    "architecture",
    "technical review",
]


def extract_exemplar_styles(db, file_row, file_path: str) -> int:
    """
    Extract section-matched style excerpts from an exemplar file and persist
    ExemplarStyle rows. Idempotent — deletes existing rows for this file first.

    Args:
        db: SQLAlchemy session
        file_row: ProgramFile ORM instance (must be committed, needs .id)
        file_path: absolute path to the file on disk

    Returns:
        Number of ExemplarStyle rows written.
    """
    text = _extract_text(file_path)
    if not text or len(text) < 200:
        logger.info("Exemplar file %s: too short to extract styles", file_row.filename)
        return 0

    try:
        from models_v2 import ExemplarStyle
        from generation.orchestrator import SECTION_MAP
    except ImportError as exc:
        logger.warning("Cannot import ExemplarStyle or SECTION_MAP: %s", exc)
        return 0

    # Delete stale rows for this file
    db.query(ExemplarStyle).filter_by(file_id=file_row.id).delete()

    written = 0
    seen: set[tuple] = set()

    for doc_type, section_defs in SECTION_MAP.items():
        for sec in section_defs:
            key = (doc_type, sec.name)
            if key in seen:
                continue
            seen.add(key)

            excerpt = _find_section_excerpt(text, sec.exemplar_pattern)
            if not excerpt:
                continue

            try:
                db.add(ExemplarStyle(
                    file_id=file_row.id,
                    doc_type=doc_type,
                    section_name=sec.name,
                    style_excerpt=excerpt[:600],
                ))
                written += 1
            except Exception as exc:
                logger.warning("Failed to write ExemplarStyle for %s/%s: %s",
                               doc_type, sec.name, exc)

    if written:
        try:
            db.commit()
        except Exception as exc:
            logger.error("Failed to commit ExemplarStyle rows: %s", exc)
            db.rollback()
            return 0

    logger.info("Extracted %d exemplar style rows from %s", written, file_row.filename)
    return written


def _extract_text(file_path: str) -> str:
    """Extract plain text from a file. Handles .docx, .pdf, .txt, .md."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as exc:
            logger.warning("DOCX extraction failed for %s: %s", file_path, exc)
            return ""

    elif ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages)
        except Exception:
            pass
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            logger.warning("PDF extraction failed for %s: %s", file_path, exc)
            return ""

    elif ext in (".txt", ".md"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as exc:
            logger.warning("Text extraction failed for %s: %s", file_path, exc)
            return ""

    return ""


def _find_section_excerpt(text: str, pattern: str, max_chars: int = 600) -> str:
    """
    Find text near a section heading matching pattern.
    Returns up to max_chars of content following the match.
    """
    idx = text.lower().find(pattern.lower())
    if idx == -1:
        return ""
    # Skip past the heading line to get the content beneath it
    newline_pos = text.find("\n", idx)
    start = (newline_pos + 1) if newline_pos != -1 else idx
    excerpt = text[start: start + max_chars].strip()
    return excerpt if len(excerpt) > 30 else ""
