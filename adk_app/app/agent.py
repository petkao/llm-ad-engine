from __future__ import annotations

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .config import load_config
from .mcp_bridge import (
    create_billing_support_ticket,
    explain_ad_match,
    get_ad_by_id,
    get_seller_billing_status,
    rank_ads_for_buyer,
    search_video_ads_for_buyer,
)
from .prompts import load_prompt
from .schemas import (
    BuyerExplainRequest,
    BuyerSearchRequest,
    QaRequest,
    SellerAdLookupRequest,
    SellerBillingRequest,
    SellerSupportRequest,
)


def _build_model() -> Gemini:
    config = load_config()
    return Gemini(
        model=config.model_name,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


buyer_search_agent = Agent(
    name="buyer_search_agent",
    model=_build_model(),
    description="Use for buyer ad discovery and video ad search requests.",
    instruction=load_prompt("buyer_search_agent.md"),
    tools=[search_video_ads_for_buyer, rank_ads_for_buyer],
    input_schema=BuyerSearchRequest,
    mode="single_turn",
)

buyer_match_explainer_agent = Agent(
    name="buyer_match_explainer_agent",
    model=_build_model(),
    description="Use for why-did-this-ad-match questions.",
    instruction=load_prompt("buyer_match_explainer_agent.md"),
    tools=[explain_ad_match],
    input_schema=BuyerExplainRequest,
    mode="single_turn",
)

seller_billing_agent = Agent(
    name="seller_billing_agent",
    model=_build_model(),
    description="Use for seller billing questions and ticket escalation.",
    instruction=load_prompt("seller_billing_agent.md"),
    tools=[get_seller_billing_status, create_billing_support_ticket],
    input_schema=SellerBillingRequest,
    mode="single_turn",
)

seller_ad_ops_agent = Agent(
    name="seller_ad_ops_agent",
    model=_build_model(),
    description="Use for looking up a seller ad by UUID and reviewing its state.",
    instruction=load_prompt("seller_ad_ops_agent.md"),
    tools=[get_ad_by_id],
    input_schema=SellerAdLookupRequest,
    mode="single_turn",
)

seller_support_agent = Agent(
    name="seller_support_agent",
    model=_build_model(),
    description="Use for mixed seller issues spanning ads, billing, and match quality.",
    instruction=load_prompt("seller_support_agent.md"),
    tools=[get_ad_by_id, get_seller_billing_status, explain_ad_match],
    input_schema=SellerSupportRequest,
    mode="single_turn",
)

qa_agent = Agent(
    name="qa_agent",
    model=_build_model(),
    description="Use for smoke tests, regression checks, and tool validation.",
    instruction=load_prompt("qa_agent.md"),
    tools=[
        search_video_ads_for_buyer,
        rank_ads_for_buyer,
        explain_ad_match,
        get_ad_by_id,
        get_seller_billing_status,
    ],
    input_schema=QaRequest,
    mode="single_turn",
)

root_agent = Agent(
    name="root_agent",
    model=_build_model(),
    description="Top-level coordinator for buyer, seller, and QA requests in the LLM Ad Engine.",
    instruction=(
        "You are the top-level coordinator for the LLM Ad Engine.\n\n"
        "Your job is to delegate each request to exactly one specialist sub-agent.\n\n"
        "Use `buyer_search_agent` for ad discovery and video ad search.\n"
        "Use `buyer_match_explainer_agent` for why-did-this-ad-match questions.\n"
        "Use `seller_billing_agent` for billing and support-ticket creation.\n"
        "Use `seller_ad_ops_agent` for ad record lookup by UUID.\n"
        "Use `seller_support_agent` for mixed seller problems that span ads and billing.\n"
        "Use `qa_agent` only for explicit testing, validation, or regression-check requests.\n\n"
        "Prefer the smallest useful handoff and let the specialist answer the user."
    ),
    sub_agents=[
        buyer_search_agent,
        buyer_match_explainer_agent,
        seller_billing_agent,
        seller_ad_ops_agent,
        seller_support_agent,
        qa_agent,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
