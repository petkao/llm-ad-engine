from __future__ import annotations

from langchain_openai import ChatOpenAI

from .config import AppConfig, load_config


def get_llm() -> ChatOpenAI:
    """Create the Nemotron Ultra chat model via NIM's OpenAI-compatible API."""

    config: AppConfig = load_config()
    return ChatOpenAI(
        model=config.llm_model,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        temperature=config.llm_temperature,
    )
