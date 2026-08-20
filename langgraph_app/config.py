from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
load_dotenv(Path(__file__).with_name(".env"))


@dataclass(frozen=True)
class AppConfig:
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_temperature: float
    mcp_server_url: str
    mcp_server_auth_token: str | None
    synthetic_device_id: str
    default_search_limit: int
    default_explain_limit: int


def load_config() -> AppConfig:
    """Load runtime configuration from environment variables."""

    llm_base_url = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()
    llm_model = os.getenv("LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    mcp_server_url = os.getenv(
        "MCP_SERVER_URL",
        "https://ad-engine-mcp-610270819686.us-west1.run.app/mcp",
    ).strip()

    if not llm_api_key:
        raise ValueError("LLM_API_KEY must be set before running the LangGraph app.")
    if not mcp_server_url:
        raise ValueError("MCP_SERVER_URL must be set before running the LangGraph app.")

    return AppConfig(
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        mcp_server_url=mcp_server_url,
        mcp_server_auth_token=(os.getenv("MCP_SERVER_AUTH_TOKEN", "").strip() or None),
        synthetic_device_id=os.getenv("SYNTHETIC_DEVICE_ID", "langgraph-buyer-device").strip(),
        default_search_limit=int(os.getenv("DEFAULT_SEARCH_LIMIT", "5")),
        default_explain_limit=int(os.getenv("DEFAULT_EXPLAIN_LIMIT", "10")),
    )
