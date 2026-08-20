from __future__ import annotations

from typing import Any, Literal, TypedDict


DomainName = Literal["buyer", "seller", "qa"]
SpecialistName = Literal[
    "buyer_search_agent",
    "buyer_match_explainer_agent",
    "seller_ad_ops_agent",
    "seller_billing_agent",
    "seller_support_agent",
    "qa_agent",
]


class GraphState(TypedDict, total=False):
    user_input: str
    forced_domain: DomainName
    forced_specialist: SpecialistName
    buyer_video_only: bool
    domain: DomainName
    specialist: SpecialistName
    route_reason: str
    extraction: dict[str, Any]
    tool_results: list[dict[str, Any]]
    raw_result: dict[str, Any]
    response: str
    error: str
