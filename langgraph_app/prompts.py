from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts"


@lru_cache(maxsize=32)
def load_prompt(filename: str) -> str:
    """Load a prompt markdown file from the shared prompts directory."""

    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8").strip()
