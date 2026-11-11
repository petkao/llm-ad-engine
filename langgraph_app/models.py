from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from .config import AppConfig, load_config


def _timeout_seconds() -> float:
    try:
        return max(1.0, float(os.getenv("LLM_TIMEOUT_SECONDS", "20")))
    except ValueError:
        return 20.0


def get_llm() -> ChatOpenAI:
    """Create the Nemotron Ultra chat model via NIM's OpenAI-compatible API.

    Each call times out after LLM_TIMEOUT_SECONDS. The client's own retries are
    off because llm_json retries every failure (timeouts, errors, empty replies)
    in one place, which keeps the worst-case request time predictable.
    """

    config: AppConfig = load_config()
    return ChatOpenAI(
        model=config.llm_model,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        temperature=config.llm_temperature,
        timeout=_timeout_seconds(),
        max_retries=0,
    )
