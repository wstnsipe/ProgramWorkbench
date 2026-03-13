"""Shared OpenAI client factory used across all LLM-powered endpoints."""
from __future__ import annotations

import os


def get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please configure it and restart the server."
        )
    return key


def get_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-5-mini")


def get_client():
    try:
        import openai as _openai
    except ImportError:
        raise RuntimeError(
            "The 'openai' Python package is not installed. Run: pip install openai"
        )
    return _openai.OpenAI(api_key=get_api_key())
