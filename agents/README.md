# Agent Scaffolding

This folder contains the LangGraph-oriented agent architecture for the LLM Ad Engine using:

- **Nemotron Ultra** as the primary LLM
- **NIM** as the model serving layer
- your existing **deployed TypeScript MCP server** as the tool layer

## Graph Shape

- `top_router_agent`
- `buyer_graph`
- `seller_graph`
- optional `qa_agent`

## Buyer Specialists

- `buyer_search_agent`
- `buyer_match_explainer_agent`

## Seller Specialists

- `seller_ad_ops_agent`
- `seller_billing_agent`
- `seller_support_agent`

## Design Goals

- keep agents small and specialized
- keep buyer and seller flows separate
- make routing explicit
- keep the LLM provider swappable between hosted NVIDIA and self-hosted NIM

## Suggested Runtime Topology

- Nemotron Ultra via NIM for reasoning
- MCP server for tool access
- lightweight orchestrator that selects the right agent and passes context

## Expected Flow

1. User request arrives.
2. `top_router_agent` classifies the domain.
3. The request enters either the buyer or seller subgraph.
4. One specialist agent is selected.
5. That agent calls MCP tools if needed.
6. A final response is returned.

## Files

- `registry.yaml`: agent registry, model config, routing overview
- `prompts/*.md`: system prompts for each agent

## Suggested First Implementation Order

1. `top_router_agent`
2. `buyer_graph`
3. `seller_graph`
4. `qa_agent`

## Environment Shape

Suggested shared environment variables:

```env
LLM_PROVIDER=nvidia_nim
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
LLM_API_KEY=...

MCP_SERVER_URL=https://ad-engine-mcp-610270819686.us-west1.run.app/mcp
MCP_SERVER_TRANSPORT=streamable-http
MCP_SERVER_AUTH_TOKEN=
```
