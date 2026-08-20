from __future__ import annotations

from .graph import build_graph
from .state import DomainName, GraphState, SpecialistName


async def run_graph_state(
    user_input: str,
    *,
    forced_domain: DomainName | None = None,
    forced_specialist: SpecialistName | None = None,
    buyer_video_only: bool = False,
) -> GraphState:
    graph = build_graph()
    initial_state: GraphState = {"user_input": user_input}
    if forced_domain:
        initial_state["forced_domain"] = forced_domain
    if forced_specialist:
        initial_state["forced_specialist"] = forced_specialist
    if buyer_video_only:
        initial_state["buyer_video_only"] = True
    result = await graph.ainvoke(initial_state)
    return result


async def run_graph_response(
    user_input: str,
    *,
    forced_domain: DomainName | None = None,
    forced_specialist: SpecialistName | None = None,
    buyer_video_only: bool = False,
) -> str:
    result = await run_graph_state(
        user_input,
        forced_domain=forced_domain,
        forced_specialist=forced_specialist,
        buyer_video_only=buyer_video_only,
    )
    return str(result.get("response", ""))
