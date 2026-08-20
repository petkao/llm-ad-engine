from __future__ import annotations

import json
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent

from .config import load_config


class RemoteMCPClient:
    """Minimal async client for calling a remote MCP server over streamable HTTP."""

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        config = load_config()
        headers: dict[str, str] = {}
        if config.mcp_server_auth_token:
            headers["Authorization"] = f"Bearer {config.mcp_server_auth_token}"

        async with streamablehttp_client(config.mcp_server_url, headers=headers or None) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result: CallToolResult = await session.call_tool(name, arguments or {})
                return normalize_tool_result(name, result)


def normalize_tool_result(tool_name: str, result: CallToolResult) -> dict[str, Any]:
    """Convert an MCP CallToolResult into a regular Python dictionary."""

    text_content: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            text_content.append(block.text)

    parsed_json: Any | None = None
    if text_content:
        joined = "\n".join(text_content).strip()
        if joined.startswith("[") or joined.startswith("{"):
            try:
                parsed_json = json.loads(joined)
            except json.JSONDecodeError:
                parsed_json = None

    return {
        "tool_name": tool_name,
        "is_error": result.isError,
        "structured_content": result.structuredContent,
        "text_content": text_content,
        "parsed_json": parsed_json,
    }
