# LangGraph Chat On Cloud Run

This deploy keeps NVIDIA hosted inference in place.

The LangGraph service runs on Cloud Run, but the LLM still uses:

- `LLM_BASE_URL=https://integrate.api.nvidia.com/v1`
- `LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b`

## What Moves To Cloud Run

- browser chat UI at `/chat`
- LangGraph runtime
- buyer and seller agent HTTP endpoints

## What Stays External

- NVIDIA hosted API for inference
- deployed MCP server at `https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp`
- deployed backend API at `https://ad-engine-api-610270819686.us-west1.run.app`

## Deploy Command

From the repo root:

```bash
cd /Users/tzechungkao/llm-ad-engine
```

Deploy with plain environment variables:

```bash
gcloud run deploy ad-engine-langgraph-chat \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars LLM_BASE_URL=https://integrate.api.nvidia.com/v1 \
  --set-env-vars LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b \
  --set-env-vars MCP_SERVER_URL=https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp \
  --set-env-vars LLM_TEMPERATURE=0.1 \
  --set-env-vars SYNTHETIC_DEVICE_ID=langgraph-buyer-device \
  --set-env-vars DEFAULT_SEARCH_LIMIT=5 \
  --set-env-vars DEFAULT_EXPLAIN_LIMIT=10 \
  --set-env-vars LLM_API_KEY=YOUR_NVIDIA_API_KEY
```

If you later protect the MCP service, add:

```bash
--set-env-vars MCP_SERVER_AUTH_TOKEN=YOUR_MCP_BEARER_TOKEN
```

## Better Secret Handling

For production, prefer Secret Manager over plain env vars.

Example pattern:

```bash
gcloud run deploy ad-engine-langgraph-chat \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars LLM_BASE_URL=https://integrate.api.nvidia.com/v1 \
  --set-env-vars LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b \
  --set-env-vars MCP_SERVER_URL=https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp \
  --set-env-vars LLM_TEMPERATURE=0.1 \
  --set-env-vars SYNTHETIC_DEVICE_ID=langgraph-buyer-device \
  --set-env-vars DEFAULT_SEARCH_LIMIT=5 \
  --set-env-vars DEFAULT_EXPLAIN_LIMIT=10 \
  --set-secrets LLM_API_KEY=nvidia-api-key:latest
```

## Verify

Health:

```bash
curl -s https://YOUR-CLOUD-RUN-URL/health
```

Chat page:

```text
https://YOUR-CLOUD-RUN-URL/chat
```

Sample API call:

```bash
curl -s -X POST https://YOUR-CLOUD-RUN-URL/agent/buyer/search \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Find video ads for cat furniture"}'
```

## User-Facing Entry Point

For non-technical buyers and sellers, use:

- `https://YOUR-CLOUD-RUN-URL/chat`

They do not need direct access to the MCP server or backend API.
