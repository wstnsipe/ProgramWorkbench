"""
renderer.py — DOCX rendering layer.

Wraps docx_builder.py with a clean interface.
Full implementation: replace the stubs below with calls into docx_builder
(or rewrite incrementally using the docx JS skill for new documents).

Receives the assembled section dict from orchestrator.py and writes a .docx file.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Map doc_type → docx_builder function name
_BUILDER_FN_MAP = {
    "rfi":          "build_rfi_docx",
    "acq_strategy": "build_acq_strategy_docx",
    "sep":          "build_sep_docx",
    "mcp":          "build_mcp_docx",
}


def render_document(*, assembled: dict[str, Any], doc_type: str, output_path: str) -> None:
    """
    Write assembled section data to a .docx file at output_path.

    Strategy:
      1. Try the new section-aware renderer (implement incrementally).
      2. Fall back to the existing docx_builder monolithic function.
    """
    # Stage 1: Attempt new renderer (not yet implemented — add sections here as they're built)
    try:
        _render_new(assembled, doc_type, output_path)
        return
    except NotImplementedError:
        pass

    # Stage 2: Fall back to existing builder
    try:
        import docx_builder
        fn_name = _BUILDER_FN_MAP.get(doc_type)
        if not fn_name:
            raise ValueError(f"No builder function for doc_type: {doc_type}")
        fn = getattr(docx_builder, fn_name, None)
        if not fn:
            raise AttributeError(f"docx_builder.{fn_name} not found")
        fn(assembled, output_path)
        logger.info("Rendered %s via legacy docx_builder.%s", doc_type, fn_name)
    except Exception as exc:
        logger.error("Rendering failed for %s: %s", doc_type, exc, exc_info=True)
        raise


def _render_new(assembled: dict[str, Any], doc_type: str, output_path: str) -> None:
    """
    New section-aware renderer.
    Implement one doc_type at a time here, then remove from legacy fallback.
    """
    raise NotImplementedError("New renderer not yet implemented — using legacy fallback")
