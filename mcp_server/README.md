# LLM Ad Engine FastMCP Server

This folder contains a standalone Python FastMCP server for your deployed LLM Ad Engine backend:

- Backend base URL: `https://ad-engine-api-610270819686.us-west1.run.app`
- MCP framework: `FastMCP`

## Files

- `server.py`: FastMCP server and tool definitions
- `api_client.py`: shared `httpx` client with error handling
- `requirements.txt`: Python dependencies
- `.env.example`: environment variables and route overrides
- `Dockerfile`: Cloud Run/container deployment image
- `verify_remote_mcp.py`: verify a deployed MCP endpoint and its tool list

## Exposed MCP Tools

1. `search_video_ads_for_buyer`
2. `get_ad_by_id`
3. `rank_ads_for_buyer`
4. `explain_ad_match`
5. `get_seller_billing_status`
6. `create_billing_support_ticket`

## Setup

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

If your backend protects admin routes such as `/api/ads/:id` or billing endpoints, set `AD_ENGINE_API_TOKEN` in `.env`.

## Run Locally

### STDIO transport

This is the most common option for MCP clients that launch the server as a subprocess.

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
source .venv/bin/activate
python server.py --transport stdio
```

### Streamable HTTP transport

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
source .venv/bin/activate
python server.py --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

## Deploy To Cloud Run

This is the recommended path if you want a seller-tools-capable MCP service to replace or supplement the current buyer-only deployed MCP server.

### 1. Build and deploy from source

From the repo root:

```bash
gcloud run deploy ad-engine-mcp-v2 \
  --source /Users/tzechungkao/llm-ad-engine/mcp_server \
  --region us-west1 \
  --allow-unauthenticated
```

### 2. Set runtime environment variables

At minimum, configure the backend base URL:

```bash
gcloud run services update ad-engine-mcp-v2 \
  --region us-west1 \
  --update-env-vars AD_ENGINE_API_BASE_URL=https://ad-engine-api-610270819686.us-west1.run.app
```

If your backend requires auth for seller/admin routes, also set:

```bash
gcloud run services update ad-engine-mcp-v2 \
  --region us-west1 \
  --update-env-vars AD_ENGINE_API_TOKEN=YOUR_BACKEND_TOKEN
```

If your backend seller endpoints use different paths, set the route overrides too:

```bash
gcloud run services update ad-engine-mcp-v2 \
  --region us-west1 \
  --update-env-vars GET_AD_BY_ID_PATH_TEMPLATE=/api/ads/{ad_id},SELLER_BILLING_STATUS_PATH_TEMPLATE=/api/sellers/{seller_id}/billing-status,CREATE_BILLING_SUPPORT_TICKET_PATH=/api/billing/support-tickets
```

### 3. Verify the MCP endpoint

Once deployed, the MCP endpoint should be:

```text
https://YOUR-CLOUD-RUN-URL/mcp
```

Use the included verification helper:

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
python verify_remote_mcp.py https://YOUR-CLOUD-RUN-URL/mcp
```

You should see:

- `search_video_ads_for_buyer`
- `get_ad_by_id`
- `rank_ads_for_buyer`
- `explain_ad_match`
- `get_seller_billing_status`
- `create_billing_support_ticket`

### 4. Switch LangGraph to the new server

Update:

```env
MCP_SERVER_URL=https://YOUR-CLOUD-RUN-URL/mcp
```

in [langgraph_app/.env](/Users/tzechungkao/llm-ad-engine/langgraph_app/.env).

### SSE transport

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
source .venv/bin/activate
python server.py --transport sse --host 127.0.0.1 --port 8000 --path /mcp
```

## Notes About Backend Routes

The deployed frontend bundle publicly references:

- `POST /api/buyer/semantic-match`
- `POST /api/buyer/click`
- `GET /api/ads` and related ad routes behind authentication

This server uses `POST /api/buyer/semantic-match` by default for:

- `rank_ads_for_buyer`
- `search_video_ads_for_buyer`

`search_video_ads_for_buyer` filters the ranked matches down to ads whose `format` is `video`.

`explain_ad_match` works in two modes:

- If `EXPLAIN_AD_MATCH_PATH` is set, it calls that backend endpoint directly.
- If `EXPLAIN_AD_MATCH_PATH` is blank or returns `404`, it falls back to deriving an explanation from the backend semantic-match results.

Because the local backend source was not present in this workspace, the billing route defaults are configurable in `.env`. If your actual backend uses different paths, update:

- `ADS_LIST_PATH`
- `GET_AD_BY_ID_PATH_TEMPLATE`
- `EXPLAIN_AD_MATCH_PATH`
- `SELLERS_LIST_PATH`
- `SELLER_BILLING_STATUS_PATH_TEMPLATE`
- `CREATE_BILLING_SUPPORT_TICKET_PATH`

The server also includes two built-in fallbacks when dedicated per-record endpoints are missing:

- `get_ad_by_id` falls back to fetching `ADS_LIST_PATH` and filtering by `id`
- `get_seller_billing_status` falls back to fetching `SELLERS_LIST_PATH` and returning a billing-oriented seller snapshot

This is useful when the backend exposes list endpoints like `/api/ads` and `/api/sellers` but does not expose dedicated routes like `/api/ads/{id}` or `/api/sellers/{seller_id}/billing-status`.

## Important Constraint

The currently deployed MCP service at `ad-engine-mcp` is a separate TypeScript deployment whose source is not present in this workspace. That means this repo cannot directly patch that running service in place.

From this workspace, the practical way to "expand the deployed MCP server with seller tools" is:

1. deploy this Python FastMCP server as a new Cloud Run service
2. verify the seller tools against your backend
3. switch LangGraph to the new MCP endpoint
4. optionally retire or rename the older buyer-only MCP service later

See also [docs/mcp_cutover_plan.md](/Users/tzechungkao/llm-ad-engine/docs/mcp_cutover_plan.md) for the staged rollout and rollback plan.

## Example MCP Client Command

Example subprocess command for an MCP client configuration:

```json
{
  "command": "python",
  "args": ["/Users/tzechungkao/llm-ad-engine/mcp_server/server.py", "--transport", "stdio"],
  "cwd": "/Users/tzechungkao/llm-ad-engine/mcp_server"
}
```
