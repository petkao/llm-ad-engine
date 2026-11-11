from __future__ import annotations

from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent

from .config import load_config


def _normalize_tool_result(tool_name: str, result: CallToolResult) -> dict[str, Any]:
    text_content: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            text_content.append(block.text)

    return {
        "tool_name": tool_name,
        "is_error": result.isError,
        "structured_content": result.structuredContent,
        "text_content": text_content,
    }


async def call_remote_mcp_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the deployed MCP server over streamable HTTP."""

    config = load_config()
    headers: dict[str, str] = {}
    if config.mcp_server_auth_token:
        headers["Authorization"] = f"Bearer {config.mcp_server_auth_token}"

    async with streamablehttp_client(config.mcp_server_url, headers=headers or None) as streams:
        read_stream, write_stream, _ = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments or {})
            return _normalize_tool_result(name, result)


async def search_video_ads_for_buyer(
    query: str,
    category: str | None = None,
    device_id: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Search the deployed MCP server for buyer-relevant video ads."""

    config = load_config()
    return await call_remote_mcp_tool(
        "search_video_ads_for_buyer",
        {
            "query": query,
            "category": category,
            "device_id": device_id or config.synthetic_device_id,
            "limit": limit or config.default_search_limit,
        },
    )


async def rank_ads_for_buyer(
    query: str,
    category: str | None = None,
    device_id: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Search the deployed MCP server for ranked ads."""

    config = load_config()
    return await call_remote_mcp_tool(
        "rank_ads_for_buyer",
        {
            "query": query,
            "category": category,
            "device_id": device_id or config.synthetic_device_id,
            "limit": limit or config.default_search_limit,
        },
    )


async def explain_ad_match(
    ad_id: str,
    query: str,
    category: str | None = None,
    device_id: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Explain a match by calling the deployed MCP server."""

    config = load_config()
    return await call_remote_mcp_tool(
        "explain_ad_match",
        {
            "ad_id": ad_id,
            "query": query,
            "category": category,
            "device_id": device_id or config.synthetic_device_id,
            "limit": limit or config.default_explain_limit,
        },
    )


async def get_ad_by_id(ad_id: str) -> dict[str, Any]:
    """Fetch a single ad via the deployed MCP server."""

    return await call_remote_mcp_tool("get_ad_by_id", {"ad_id": ad_id})


async def get_seller_billing_status(seller_id: str) -> dict[str, Any]:
    """Fetch seller billing information via the deployed MCP server."""

    return await call_remote_mcp_tool("get_seller_billing_status", {"seller_id": seller_id})


async def create_billing_support_ticket(
    seller_id: str,
    subject: str,
    description: str,
    email: str | None = None,
    priority: str = "medium",
) -> dict[str, Any]:
    """Create a seller billing support ticket via the deployed MCP server."""

    return await call_remote_mcp_tool(
        "create_billing_support_ticket",
        {
            "seller_id": seller_id,
            "subject": subject,
            "description": description,
            "email": email,
            "priority": priority,
        },
    )
