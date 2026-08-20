from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .config import load_config
from .llm_json import invoke_json
from .mcp_client import RemoteMCPClient
from .models import get_llm
from .prompts import load_prompt
from .state import GraphState


def _append_tool_result(state: GraphState, result: dict[str, Any]) -> list[dict[str, Any]]:
    return [*(state.get("tool_results") or []), result]


def _clamp_limit(value: Any, default: int) -> int:
    if isinstance(value, int):
        return max(1, min(value, 20))
    return default


def _tool_payload(tool_result: dict[str, Any]) -> Any:
    return (
        tool_result.get("parsed_json")
        or tool_result.get("structured_content")
        or tool_result.get("text_content")
        or {}
    )


def _stringify_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()
    return str(content)


def _fallback_response(state: GraphState, error: Exception | None = None) -> str:
    tool_results = state.get("tool_results") or []
    if not tool_results:
        base = "The agent could not complete the request and no tool output was returned."
        if error:
            return f"{base}\n\nFallback reason: {error}"
        return base

    latest = tool_results[-1]
    tool_name = str(latest.get("tool_name", "tool"))
    payload = _tool_payload(latest)

    if tool_name == "get_seller_billing_status" and isinstance(payload, dict):
        seller_name = payload.get("seller_name", "Unknown seller")
        seller_id = payload.get("seller_id", "unknown")
        lines = [
            f"Billing status for {seller_name} (seller ID: {seller_id})",
            f"Plan: {payload.get('plan', 'unknown')}",
            f"Status: {payload.get('status', 'unknown')}",
            f"Verified: {'Yes' if payload.get('is_verified') else 'No'}",
            f"Current balance: ${payload.get('balance', '0')}",
            f"Product count: {payload.get('product_count', 0)}",
            f"Ad count: {payload.get('ad_count', 0)}",
            f"Total ad spend: ${payload.get('ad_spend_total', 0)}",
        ]
        summary = payload.get("transaction_summary")
        if isinstance(summary, dict):
            lines.extend(
                [
                    "",
                    "Transaction summary:",
                    f"- Transactions: {summary.get('transaction_count', 0)}",
                    f"- Total charges: ${summary.get('total_charges', 0)}",
                    f"- Total credits: ${summary.get('total_credits', 0)}",
                    f"- Last transaction at: {summary.get('last_transaction_at') or 'None'}",
                ]
            )
        if error:
            lines.extend(["", f"Fallback reason: {error}"])
        return "\n".join(lines)

    if tool_name == "create_billing_support_ticket" and isinstance(payload, dict):
        lines = [
            f"Billing support ticket submitted: {payload.get('ticket_id', 'unknown')}",
            f"Status: {payload.get('status', 'submitted')}",
            f"Seller: {payload.get('seller_name', 'Unknown seller')}",
            f"Priority: {payload.get('priority', 'medium')}",
            f"Subject: {payload.get('subject', '')}",
            f"Created at: {payload.get('created_at', 'unknown')}",
        ]
        if error:
            lines.extend(["", f"Fallback reason: {error}"])
        return "\n".join(lines)

    if tool_name == "get_ad_by_id" and isinstance(payload, dict):
        lines = [
            f"Ad lookup result for {payload.get('id', 'unknown ad')}",
            f"Headline: {payload.get('headline', '')}",
            f"Product: {payload.get('product_title', '')}",
            f"Seller: {payload.get('seller_name', '')}",
            f"Status: {payload.get('status', 'unknown')}",
            f"Category: {payload.get('category', '')}",
            f"Format: {payload.get('format', '')}",
        ]
        if error:
            lines.extend(["", f"Fallback reason: {error}"])
        return "\n".join(lines)

    if tool_name in {"search_video_ads_for_buyer", "rank_ads_for_buyer"} and isinstance(payload, dict):
        matches = payload.get("matches")
        if isinstance(matches, list) and matches:
            lines = [
                f"Found {len(matches)} matching ads for query: {payload.get('query', 'unknown')}",
            ]
            for match in matches[:3]:
                if not isinstance(match, dict):
                    continue
                lines.append(
                    f"- {match.get('product_title') or match.get('headline') or 'Ad'} by {match.get('seller_name', 'unknown seller')} "
                    f"(score: {match.get('relevance_score', match.get('similarity_score', 'n/a'))})"
                )
            if error:
                lines.extend(["", f"Fallback reason: {error}"])
            return "\n".join(lines)

    if isinstance(payload, dict):
        summary = json.dumps(payload, indent=2, default=str)
        if error:
            return f"Tool output summary:\n{summary}\n\nFallback reason: {error}"
        return f"Tool output summary:\n{summary}"

    text_chunks = latest.get("text_content") or []
    if text_chunks:
        text = "\n".join(str(chunk) for chunk in text_chunks)
        if error:
            return f"{text}\n\nFallback reason: {error}"
        return text

    base = "The request completed with tool output, but the final response formatter was unavailable."
    if error:
        return f"{base}\n\nFallback reason: {error}"
    return base


async def top_router_node(state: GraphState) -> GraphState:
    forced_domain = str(state.get("forced_domain", "")).strip().lower()
    if forced_domain in {"buyer", "seller", "qa"}:
        return {"domain": forced_domain, "route_reason": "forced_domain"}

    payload = await invoke_json(
        load_prompt("top_router_agent.md"),
        state["user_input"],
        {"domain": "buyer", "reason": "short reason"},
    )
    domain = str(payload.get("domain", "seller")).strip().lower()
    if domain not in {"buyer", "seller", "qa"}:
        domain = "seller"
    return {"domain": domain, "route_reason": str(payload.get("reason", ""))}


async def buyer_router_node(state: GraphState) -> GraphState:
    forced_specialist = str(state.get("forced_specialist", "")).strip()
    if forced_specialist in {"buyer_search_agent", "buyer_match_explainer_agent"}:
        return {"specialist": forced_specialist, "route_reason": "forced_specialist"}

    payload = await invoke_json(
        load_prompt("buyer_router_agent.md"),
        state["user_input"],
        {"specialist": "buyer_search_agent", "reason": "short reason"},
    )
    specialist = str(payload.get("specialist", "buyer_search_agent")).strip()
    if specialist not in {"buyer_search_agent", "buyer_match_explainer_agent"}:
        specialist = "buyer_search_agent"
    return {"specialist": specialist, "route_reason": str(payload.get("reason", ""))}


async def seller_router_node(state: GraphState) -> GraphState:
    forced_specialist = str(state.get("forced_specialist", "")).strip()
    if forced_specialist in {
        "seller_ad_ops_agent",
        "seller_billing_agent",
        "seller_support_agent",
    }:
        return {"specialist": forced_specialist, "route_reason": "forced_specialist"}

    payload = await invoke_json(
        load_prompt("seller_router_agent.md"),
        state["user_input"],
        {"specialist": "seller_support_agent", "reason": "short reason"},
    )
    specialist = str(payload.get("specialist", "seller_support_agent")).strip()
    if specialist not in {
        "seller_ad_ops_agent",
        "seller_billing_agent",
        "seller_support_agent",
    }:
        specialist = "seller_support_agent"
    return {"specialist": specialist, "route_reason": str(payload.get("reason", ""))}


async def buyer_search_node(state: GraphState) -> GraphState:
    config = load_config()
    force_video_only = bool(state.get("buyer_video_only"))
    payload = await invoke_json(
        load_prompt("buyer_search_agent.md"),
        state["user_input"],
        {
            "query": "trail running shoes",
            "category": "",
            "device_id": config.synthetic_device_id,
            "limit": config.default_search_limit,
            "video_only": False,
        },
    )

    arguments = {
        "query": str(payload.get("query") or state["user_input"]).strip(),
        "category": str(payload.get("category", "")).strip() or None,
        "device_id": str(payload.get("device_id") or config.synthetic_device_id).strip(),
        "limit": _clamp_limit(payload.get("limit"), config.default_search_limit),
    }
    tool_name = (
        "search_video_ads_for_buyer"
        if force_video_only or bool(payload.get("video_only"))
        else "rank_ads_for_buyer"
    )
    result = await RemoteMCPClient().call_tool(tool_name, arguments)
    return {
        "extraction": payload,
        "raw_result": result,
        "tool_results": _append_tool_result(state, result),
    }


async def buyer_match_explainer_node(state: GraphState) -> GraphState:
    config = load_config()
    payload = await invoke_json(
        load_prompt("buyer_match_explainer_agent.md"),
        state["user_input"],
        {
            "ad_id": "",
            "query": "trail running shoes",
            "category": "",
            "device_id": config.synthetic_device_id,
            "limit": config.default_explain_limit,
        },
    )

    ad_id = str(payload.get("ad_id", "")).strip()
    if not ad_id:
        return {"error": "An ad_id is required to explain why a specific ad matched."}

    arguments = {
        "ad_id": ad_id,
        "query": str(payload.get("query") or state["user_input"]).strip(),
        "category": str(payload.get("category", "")).strip() or None,
        "device_id": str(payload.get("device_id") or config.synthetic_device_id).strip(),
        "limit": _clamp_limit(payload.get("limit"), config.default_explain_limit),
    }
    result = await RemoteMCPClient().call_tool("explain_ad_match", arguments)
    return {
        "extraction": payload,
        "raw_result": result,
        "tool_results": _append_tool_result(state, result),
    }


async def seller_ad_ops_node(state: GraphState) -> GraphState:
    payload = await invoke_json(
        load_prompt("seller_ad_ops_agent.md"),
        state["user_input"],
        {"ad_id": ""},
    )
    ad_id = str(payload.get("ad_id", "")).strip()
    if not ad_id:
        return {"error": "An ad_id is required to inspect an ad record."}

    result = await RemoteMCPClient().call_tool("get_ad_by_id", {"ad_id": ad_id})
    return {
        "extraction": payload,
        "raw_result": result,
        "tool_results": _append_tool_result(state, result),
    }


async def seller_billing_node(state: GraphState) -> GraphState:
    payload = await invoke_json(
        load_prompt("seller_billing_agent.md"),
        state["user_input"],
        {
            "seller_id": "",
            "create_ticket": False,
            "subject": "",
            "description": "",
            "email": "",
            "priority": "medium",
        },
    )
    seller_id = str(payload.get("seller_id", "")).strip()
    if not seller_id:
        return {"error": "A seller_id is required for seller billing actions."}

    client = RemoteMCPClient()
    tool_results = state.get("tool_results") or []
    status_result = await client.call_tool("get_seller_billing_status", {"seller_id": seller_id})
    tool_results.append(status_result)

    raw_result = status_result
    if bool(payload.get("create_ticket")):
        description = str(payload.get("description", "")).strip()
        subject = str(payload.get("subject", "")).strip() or "Billing support request"
        if not description:
            return {
                "error": "A ticket description is required before creating a billing support ticket.",
                "tool_results": tool_results,
                "raw_result": status_result,
            }
        ticket_result = await client.call_tool(
            "create_billing_support_ticket",
            {
                "seller_id": seller_id,
                "subject": subject,
                "description": description,
                "email": str(payload.get("email", "")).strip() or None,
                "priority": str(payload.get("priority", "medium")).strip() or "medium",
            },
        )
        tool_results.append(ticket_result)
        raw_result = ticket_result

    return {
        "extraction": payload,
        "raw_result": raw_result,
        "tool_results": tool_results,
    }


async def seller_support_node(state: GraphState) -> GraphState:
    config = load_config()
    payload = await invoke_json(
        load_prompt("seller_support_agent.md"),
        state["user_input"],
        {
            "seller_id": "",
            "ad_id": "",
            "billing_related": False,
            "needs_match_explanation": False,
            "query": "",
            "category": "",
        },
    )

    client = RemoteMCPClient()
    tool_results = state.get("tool_results") or []
    raw_result: dict[str, Any] = {}

    ad_id = str(payload.get("ad_id", "")).strip()
    seller_id = str(payload.get("seller_id", "")).strip()
    if ad_id:
        ad_result = await client.call_tool("get_ad_by_id", {"ad_id": ad_id})
        tool_results.append(ad_result)
        raw_result = ad_result

    if bool(payload.get("needs_match_explanation")) and ad_id:
        explain_result = await client.call_tool(
            "explain_ad_match",
            {
                "ad_id": ad_id,
                "query": str(payload.get("query") or state["user_input"]).strip(),
                "category": str(payload.get("category", "")).strip() or None,
                "device_id": config.synthetic_device_id,
                "limit": config.default_explain_limit,
            },
        )
        tool_results.append(explain_result)
        raw_result = explain_result

    if bool(payload.get("billing_related")) and seller_id:
        billing_result = await client.call_tool(
            "get_seller_billing_status",
            {"seller_id": seller_id},
        )
        tool_results.append(billing_result)
        raw_result = billing_result

    if not tool_results:
        return {
            "error": "The seller support request needs at least an ad_id, seller_id, or a clearer issue description.",
            "extraction": payload,
        }

    return {
        "extraction": payload,
        "raw_result": raw_result,
        "tool_results": tool_results,
    }


async def qa_node(state: GraphState) -> GraphState:
    config = load_config()
    result = await RemoteMCPClient().call_tool(
        "rank_ads_for_buyer",
        {
            "query": "running shoes",
            "category": None,
            "device_id": config.synthetic_device_id,
            "limit": 3,
        },
    )
    return {
        "raw_result": result,
        "tool_results": _append_tool_result(state, result),
    }


async def final_response_node(state: GraphState) -> GraphState:
    if state.get("error"):
        return {"response": state["error"]}

    llm = get_llm()
    raw_json = json.dumps(
        {
            "domain": state.get("domain"),
            "specialist": state.get("specialist"),
            "route_reason": state.get("route_reason"),
            "tool_results": state.get("tool_results", []),
        },
        indent=2,
        default=str,
    )
    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=load_prompt("final_response_agent.md")),
                HumanMessage(
                    content=(
                        f"Original request:\n{state['user_input']}\n\n"
                        f"Execution data:\n{raw_json}"
                    )
                ),
            ]
        )
        return {"response": _stringify_message_content(response.content)}
    except Exception as exc:
        return {"response": _fallback_response(state, exc)}
