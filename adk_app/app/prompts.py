from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "agents" / "prompts"


@lru_cache(maxsize=32)
def load_prompt(filename: str) -> str:
    """Load a shared prompt file from the existing prompt directory."""

    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()
