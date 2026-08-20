from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Iterable

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


DEFAULT_REQUIRED_TOOLS = [
    "search_video_ads_for_buyer",
    "get_ad_by_id",
    "rank_ads_for_buyer",
    "explain_ad_match",
    "get_seller_billing_status",
    "create_billing_support_ticket",
]


async def verify_remote_mcp(
    url: str,
    *,
    required_tools: Iterable[str],
    auth_token: str | None,
) -> int:
    headers: dict[str, str] | None = None
    if auth_token:
        headers = {"Authorization": f"Bearer {auth_token}"}

    async with streamablehttp_client(url, headers=headers) as streams:
        read_stream, write_stream, _ = streams
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            tools = await session.list_tools()

    tool_names = [tool.name for tool in tools.tools]
    missing = [tool for tool in required_tools if tool not in tool_names]

    print(json.dumps(
        {
            "url": url,
            "server_name": init.serverInfo.name,
            "server_version": init.serverInfo.version,
            "tool_names": tool_names,
            "missing_required_tools": missing,
        },
        indent=2,
    ))

    return 1 if missing else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a remote MCP endpoint and its tool list.")
    parser.add_argument("url", help="Remote MCP endpoint URL, such as https://service-url/mcp")
    parser.add_argument(
        "--auth-token",
        default=None,
        help="Optional bearer token for protected MCP services.",
    )
    parser.add_argument(
        "--required-tool",
        action="append",
        default=[],
        help="Required tool name. Can be passed multiple times. Defaults to the full seller+buyer tool set.",
    )
    args = parser.parse_args()

    required_tools = args.required_tool or DEFAULT_REQUIRED_TOOLS
    exit_code = asyncio.run(
        verify_remote_mcp(
            args.url,
            required_tools=required_tools,
            auth_token=args.auth_token,
        )
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
