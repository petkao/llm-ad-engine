from __future__ import annotations

import argparse
import atexit
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from api_client import (
    AdEngineApiClient,
    ApiClientError,
    ApiConfigurationError,
    build_api_client_from_env,
)


load_dotenv()
load_dotenv(Path(__file__).with_name(".env"))

mcp = FastMCP(
    name="LLM Ad Engine MCP Server",
    instructions=(
        "Tools for searching and managing ads in the deployed LLM Ad Engine backend."
    ),
)


@lru_cache(maxsize=1)
def get_api_client() -> AdEngineApiClient:
    """Return a shared API client configured from environment variables."""
    client = build_api_client_from_env()
    atexit.register(client.close)
    return client


def _validate_limit(limit: int) -> None:
    if limit < 1 or limit > 100:
        raise ToolError("`limit` must be between 1 and 100.")


def _require_query_or_category(query: str, category: str | None) -> None:
    if not query.strip() and not (category or "").strip():
        raise ToolError("Provide at least one of `query` or `category`.")


def _normalize_text_terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_fallback_explanation(
    *,
    client: AdEngineApiClient,
    ad_id: str,
    query: str,
    category: str | None,
    device_id: str,
    limit: int,
) -> dict[str, Any]:
    ranking = client.rank_ads_for_buyer(
        query=query,
        category=category,
        device_id=device_id,
        limit=limit,
    )
    matches = ranking.get("matches", []) or []

    for match in matches:
        if match.get("id") != ad_id:
            continue

        query_terms = _normalize_text_terms(query)
        intent_tags = [str(tag) for tag in (match.get("intent_tags") or [])]
        tag_hits = [
            tag
            for tag in intent_tags
            if any(term in tag.lower() or tag.lower() in term for term in query_terms)
        ]

        reasons: list[str] = []
        relevance_score = match.get("relevance_score")
        if relevance_score is not None:
            reasons.append(f"Backend relevance score: {float(relevance_score):.3f}.")
        if tag_hits:
            reasons.append(
                "Intent tags overlapping the buyer query: " + ", ".join(tag_hits[:5]) + "."
            )
        if category and (match.get("category") or "").strip().lower() == category.strip().lower():
            reasons.append(f"Category matched `{category}`.")
        if match.get("product_title"):
            reasons.append(f"Matched product: {match['product_title']}.")
        if not reasons:
            reasons.append(
                "The ad appeared in the backend's ranked semantic-match results for this buyer query."
            )

        return {
            "mode": "fallback_semantic_match",
            "ad_id": ad_id,
            "query": query,
            "category": category or "",
            "found_in_top_results": True,
            "rank_position": match.get("rank_position"),
            "relevance_score": relevance_score,
            "explanation": " ".join(reasons),
            "match": match,
        }

    return {
        "mode": "fallback_semantic_match",
        "ad_id": ad_id,
        "query": query,
        "category": category or "",
        "found_in_top_results": False,
        "explanation": (
            f"Ad `{ad_id}` was not present in the top {limit} ranked results "
            "returned by the backend for this buyer query."
        ),
        "matches_considered": len(matches),
    }


def _translate_error(exc: Exception) -> ToolError:
    return ToolError(str(exc))


@mcp.tool()
def search_video_ads_for_buyer(
    query: str,
    category: str | None = None,
    device_id: str = "mcp-fastmcp-client",
    limit: int = 10,
) -> dict[str, Any]:
    """Search for buyer-relevant ads and return only video results.

    Args:
        query: Buyer search text or intent summary.
        category: Optional category filter forwarded to the backend.
        device_id: Anonymous device identifier sent to the backend matcher.
        limit: Maximum number of video ads to return.

    Returns:
        A structured payload containing only video ad matches from the backend.
    """

    _validate_limit(limit)
    _require_query_or_category(query, category)

    try:
        response = get_api_client().search_video_ads_for_buyer(
            query=query,
            category=category,
            device_id=device_id,
            limit=min(limit * 3, 100),
        )
    except ApiClientError as exc:
        raise _translate_error(exc) from exc

    matches = response.get("matches", []) or []
    video_matches = [
        match for match in matches if str(match.get("format", "")).lower() == "video"
    ][:limit]

    return {
        "query": response.get("query", query),
        "category": response.get("category", category or ""),
        "engine": response.get("engine"),
        "total_matches_from_backend": response.get("total", len(matches)),
        "video_matches_returned": len(video_matches),
        "matches": video_matches,
    }


@mcp.tool()
def get_ad_by_id(ad_id: str) -> dict[str, Any]:
    """Fetch a single ad by ID from the backend API.

    Args:
        ad_id: Backend ad identifier.

    Returns:
        The backend response for the requested ad.
    """

    try:
        return get_api_client().get_ad_by_id(ad_id=ad_id)
    except ApiClientError as exc:
        raise _translate_error(exc) from exc


@mcp.tool()
def rank_ads_for_buyer(
    query: str,
    category: str | None = None,
    device_id: str = "mcp-fastmcp-client",
    limit: int = 10,
) -> dict[str, Any]:
    """Return ranked ads for a buyer query using the backend matcher.

    Args:
        query: Buyer search text or intent summary.
        category: Optional category filter forwarded to the backend.
        device_id: Anonymous device identifier sent to the backend matcher.
        limit: Maximum number of ranked ads to request.

    Returns:
        The ranked ad-match response from the backend API.
    """

    _validate_limit(limit)
    _require_query_or_category(query, category)

    try:
        return get_api_client().rank_ads_for_buyer(
            query=query,
            category=category,
            device_id=device_id,
            limit=limit,
        )
    except ApiClientError as exc:
        raise _translate_error(exc) from exc


@mcp.tool()
def explain_ad_match(
    ad_id: str,
    query: str,
    category: str | None = None,
    device_id: str = "mcp-fastmcp-client",
    limit: int = 25,
) -> dict[str, Any]:
    """Explain why a specific ad matches a buyer query.

    Args:
        ad_id: Backend ad identifier to explain.
        query: Buyer search text or intent summary.
        category: Optional category filter forwarded to the backend.
        device_id: Anonymous device identifier sent to the backend matcher.
        limit: Number of ranked results to inspect when using fallback mode.

    Returns:
        Either the backend explanation payload or a fallback explanation derived
        from the backend semantic-match response.
    """

    _validate_limit(limit)
    _require_query_or_category(query, category)

    client = get_api_client()
    try:
        return client.explain_ad_match(
            ad_id=ad_id,
            query=query,
            category=category,
            device_id=device_id,
        )
    except ApiConfigurationError:
        return _build_fallback_explanation(
            client=client,
            ad_id=ad_id,
            query=query,
            category=category,
            device_id=device_id,
            limit=limit,
        )
    except ApiClientError as exc:
        if exc.status_code == 404:
            return _build_fallback_explanation(
                client=client,
                ad_id=ad_id,
                query=query,
                category=category,
                device_id=device_id,
                limit=limit,
            )
        raise _translate_error(exc) from exc


@mcp.tool()
def get_seller_billing_status(seller_id: str) -> dict[str, Any]:
    """Fetch the current billing status for a seller.

    Args:
        seller_id: Backend seller identifier.

    Returns:
        The backend billing-status payload for the seller.
    """

    try:
        return get_api_client().get_seller_billing_status(seller_id=seller_id)
    except ApiClientError as exc:
        raise _translate_error(exc) from exc


@mcp.tool()
def create_billing_support_ticket(
    seller_id: str,
    subject: str,
    description: str,
    email: str | None = None,
    priority: Literal["low", "medium", "high"] = "medium",
) -> dict[str, Any]:
    """Create a billing support ticket for a seller.

    Args:
        seller_id: Backend seller identifier.
        subject: Short summary of the billing issue.
        description: Detailed ticket description.
        email: Optional contact email for follow-up.
        priority: Billing ticket urgency level.

    Returns:
        The backend response for the newly created support ticket.
    """

    if not subject.strip():
        raise ToolError("`subject` must not be empty.")
    if not description.strip():
        raise ToolError("`description` must not be empty.")

    try:
        return get_api_client().create_billing_support_ticket(
            seller_id=seller_id,
            subject=subject,
            description=description,
            email=email,
            priority=priority,
        )
    except ApiClientError as exc:
        raise _translate_error(exc) from exc


def main() -> None:
    """Run the FastMCP server with either stdio or HTTP transport."""

    parser = argparse.ArgumentParser(description="Run the LLM Ad Engine FastMCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http", "sse"],
        default="stdio",
        help="FastMCP transport to use.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for HTTP-based transports.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for HTTP-based transports.",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="HTTP path for streamable HTTP or SSE transports.",
    )
    args = parser.parse_args()

    run_kwargs: dict[str, Any] = {}
    if args.transport != "stdio":
        run_kwargs["host"] = args.host
        run_kwargs["port"] = args.port
        run_kwargs["path"] = args.path

    mcp.run(transport=args.transport, **run_kwargs)


if __name__ == "__main__":
    main()
