from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class AppConfig:
    model_name: str
    mcp_server_url: str
    mcp_server_auth_token: str | None
    synthetic_device_id: str
    default_search_limit: int
    default_explain_limit: int


def load_config() -> AppConfig:
    """Load the ADK runtime settings from environment variables."""

    model_name = os.getenv("ADK_MODEL", "gemini-2.5-flash").strip()
    mcp_server_url = os.getenv(
        "MCP_SERVER_URL",
        "https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp",
    ).strip()
    if not mcp_server_url:
        raise ValueError("MCP_SERVER_URL must be set before running the ADK app.")

    return AppConfig(
        model_name=model_name,
        mcp_server_url=mcp_server_url,
        mcp_server_auth_token=(os.getenv("MCP_SERVER_AUTH_TOKEN", "").strip() or None),
        synthetic_device_id=os.getenv("SYNTHETIC_DEVICE_ID", "adk-buyer-device").strip(),
        default_search_limit=int(os.getenv("DEFAULT_SEARCH_LIMIT", "5")),
        default_explain_limit=int(os.getenv("DEFAULT_EXPLAIN_LIMIT", "10")),
    )
