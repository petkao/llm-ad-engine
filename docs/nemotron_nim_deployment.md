# Nemotron Ultra + NIM Deployment Advice

## Short Answer

For **prototype / immediate agent work**, use the **hosted NVIDIA endpoint** first.

For **production**, use **self-hosted NIM on a GPU Kubernetes cluster**.

## Recommended Path

### Option 1: Fastest path right now

Use the NVIDIA-hosted endpoint for Nemotron Ultra behind the OpenAI-compatible API shape.

Why:

- fastest time to first working agent
- no GPU cluster to operate
- easiest way to validate prompts, routing, and MCP tool use

Suggested use:

- build and test the router agent
- build and test the specialist agents
- validate tool calling and response formats

### Option 2: Best production path

Use **self-hosted NIM** on **Kubernetes with dedicated GPUs**.

If you are staying on GCP, the cleanest fit is:

- **GKE Standard** with GPU node pools

Why this is the best long-term fit:

- your backend is already in GCP
- Kubernetes is a better operational fit than serverless for large, long-lived GPU inference
- easier to scale independently from the MCP/tooling layer
- easier to isolate model serving, agent runtime, and API services

## Practical Recommendation

Start in two stages:

1. Use the hosted NVIDIA endpoint for Nemotron Ultra now.
2. Move to self-hosted NIM on GKE after the agent behavior is stable.

This avoids paying the complexity cost of GPU infrastructure before the agent prompts, routing rules, and MCP workflows are working well.

## What I Would Not Do First

I would **not** start by self-hosting Nemotron Ultra on Cloud Run.

Reason:

- for a very large reasoning model, the operational shape is closer to a dedicated GPU serving system than a typical request-scaled serverless app
- separating model serving from your MCP/API layer will make scaling and debugging easier

## Deployment Split I Recommend

- **NIM model serving**: GKE GPU cluster
- **Agent runtime / orchestrator**: Cloud Run or your app backend
- **MCP server**: existing deployed TypeScript server for now

This gives you:

- one layer for LLM inference
- one layer for orchestration
- one layer for tools/data access

## Environment Model

Use a provider-agnostic config shape so you can switch from hosted NVIDIA to self-hosted NIM later without rewriting agent logic:

```env
LLM_PROVIDER=nvidia_nim
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
LLM_API_KEY=...
```

Later, swap only the base URL:

```env
LLM_PROVIDER=nvidia_nim
LLM_BASE_URL=https://YOUR-SELF-HOSTED-NIM-ENDPOINT/v1
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
LLM_API_KEY=...
```

## Decision Rule

Choose **hosted NVIDIA first** if:

- you want working agents this week
- prompt iteration matters more than infra control
- you have not finalized tool workflows yet

Choose **self-hosted NIM on GKE** if:

- you need production control
- you expect meaningful traffic
- you need predictable GPU allocation
- you want tighter control over latency, scaling, and networking
