from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.routing import Route

from .service import run_graph_state

STATIC_DIR = Path(__file__).with_name("static")


class AgentRequest(BaseModel):
    prompt: str = Field(..., description="User request to process through the LangGraph runtime.")


def _response_payload(result: dict) -> dict:
    return {
        "response": str(result.get("response", "")),
        "domain": result.get("domain"),
        "specialist": result.get("specialist"),
        "route_reason": result.get("route_reason"),
        "tool_results": result.get("tool_results") or [],
        "raw_result": result.get("raw_result"),
        "error": result.get("error"),
    }


async def _run(
    prompt: str,
    *,
    domain: str | None = None,
    specialist: str | None = None,
    buyer_video_only: bool = False,
) -> JSONResponse:
    result = await run_graph_state(
        prompt,
        forced_domain=domain,  # type: ignore[arg-type]
        forced_specialist=specialist,  # type: ignore[arg-type]
        buyer_video_only=buyer_video_only,
    )
    return JSONResponse(_response_payload(result))


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def index(_: Request) -> RedirectResponse:
    return RedirectResponse(url="/portal", status_code=307)


async def chat_ui(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "chat.html")


async def buyer_ui(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "buyer.html")


async def seller_ui(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "seller.html")


async def portal_ui(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


async def chat_js(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "chat.js", media_type="application/javascript")


async def chat_css(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "chat.css", media_type="text/css")


async def run_agent(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(payload.prompt)


async def buyer_search(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(payload.prompt, domain="buyer", specialist="buyer_search_agent")


async def buyer_video_search(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(
        payload.prompt,
        domain="buyer",
        specialist="buyer_search_agent",
        buyer_video_only=True,
    )


async def buyer_explain(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(
        payload.prompt,
        domain="buyer",
        specialist="buyer_match_explainer_agent",
    )


async def seller_billing(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(
        payload.prompt,
        domain="seller",
        specialist="seller_billing_agent",
    )


async def seller_ad_ops(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(
        payload.prompt,
        domain="seller",
        specialist="seller_ad_ops_agent",
    )


async def seller_support(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(
        payload.prompt,
        domain="seller",
        specialist="seller_support_agent",
    )


async def qa_agent(request: Request) -> JSONResponse:
    payload = AgentRequest.model_validate(json.loads((await request.body()).decode("utf-8")))
    return await _run(payload.prompt, domain="qa")


app = Starlette(
    debug=False,
    routes=[
        Route("/", index, methods=["GET"]),
        Route("/portal", portal_ui, methods=["GET"]),
        Route("/buyer", buyer_ui, methods=["GET"]),
        Route("/seller", seller_ui, methods=["GET"]),
        Route("/chat", chat_ui, methods=["GET"]),
        Route("/static/chat.js", chat_js, methods=["GET"]),
        Route("/static/chat.css", chat_css, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/agent/run", run_agent, methods=["POST"]),
        Route("/agent/buyer/search", buyer_search, methods=["POST"]),
        Route("/agent/buyer/video-search", buyer_video_search, methods=["POST"]),
        Route("/agent/buyer/explain", buyer_explain, methods=["POST"]),
        Route("/agent/seller/billing", seller_billing, methods=["POST"]),
        Route("/agent/seller/ad-ops", seller_ad_ops, methods=["POST"]),
        Route("/agent/seller/support", seller_support, methods=["POST"]),
        Route("/agent/qa", qa_agent, methods=["POST"]),
    ],
)
