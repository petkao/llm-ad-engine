from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import (
    buyer_match_explainer_node,
    buyer_router_node,
    buyer_search_node,
    final_response_node,
    qa_node,
    seller_ad_ops_node,
    seller_billing_node,
    seller_router_node,
    seller_support_node,
    top_router_node,
)
from .state import GraphState


def route_domain(state: GraphState) -> str:
    domain = state.get("domain", "seller")
    if domain == "buyer":
        return "buyer_router"
    if domain == "qa":
        return "qa_agent"
    return "seller_router"


def route_buyer_specialist(state: GraphState) -> str:
    specialist = state.get("specialist", "buyer_search_agent")
    if specialist == "buyer_match_explainer_agent":
        return "buyer_match_explainer_agent"
    return "buyer_search_agent"


def route_seller_specialist(state: GraphState) -> str:
    specialist = state.get("specialist", "seller_support_agent")
    if specialist == "seller_ad_ops_agent":
        return "seller_ad_ops_agent"
    if specialist == "seller_billing_agent":
        return "seller_billing_agent"
    return "seller_support_agent"


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("top_router", top_router_node)
    graph.add_node("buyer_router", buyer_router_node)
    graph.add_node("seller_router", seller_router_node)
    graph.add_node("buyer_search_agent", buyer_search_node)
    graph.add_node("buyer_match_explainer_agent", buyer_match_explainer_node)
    graph.add_node("seller_ad_ops_agent", seller_ad_ops_node)
    graph.add_node("seller_billing_agent", seller_billing_node)
    graph.add_node("seller_support_agent", seller_support_node)
    graph.add_node("qa_agent", qa_node)
    graph.add_node("final_response", final_response_node)

    graph.add_edge(START, "top_router")
    graph.add_conditional_edges(
        "top_router",
        route_domain,
        {
            "buyer_router": "buyer_router",
            "seller_router": "seller_router",
            "qa_agent": "qa_agent",
        },
    )
    graph.add_conditional_edges(
        "buyer_router",
        route_buyer_specialist,
        {
            "buyer_search_agent": "buyer_search_agent",
            "buyer_match_explainer_agent": "buyer_match_explainer_agent",
        },
    )
    graph.add_conditional_edges(
        "seller_router",
        route_seller_specialist,
        {
            "seller_ad_ops_agent": "seller_ad_ops_agent",
            "seller_billing_agent": "seller_billing_agent",
            "seller_support_agent": "seller_support_agent",
        },
    )

    for node_name in (
        "buyer_search_agent",
        "buyer_match_explainer_agent",
        "seller_ad_ops_agent",
        "seller_billing_agent",
        "seller_support_agent",
        "qa_agent",
    ):
        graph.add_edge(node_name, "final_response")

    graph.add_edge("final_response", END)
    return graph.compile(name="llm_ad_engine_graph")
