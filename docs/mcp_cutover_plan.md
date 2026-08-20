# MCP Cutover Plan

This is the safest rollout path for replacing the current buyer-only MCP service with the new seller-tools-capable MCP service.

## Current State

- Existing service: `ad-engine-mcp`
- Region: `us-west1`
- Behavior: buyer-video-focused only
- Current known tools:
  - `get_video_ads`
  - `search_video_ads`

## Target State

Deploy a new MCP service, for example:

- `ad-engine-mcp-v2`

and point LangGraph to it only after tool verification succeeds.

## Rollout Steps

1. Deploy the new Python FastMCP service from `/Users/tzechungkao/llm-ad-engine/mcp_server`.
2. Configure backend env vars on the new Cloud Run service.
3. Verify the new service exposes the expected buyer and seller tools.
4. Update `langgraph_app/.env` to the new `MCP_SERVER_URL`.
5. Run buyer and seller smoke tests through LangGraph.
6. Keep the old MCP service running until the new path is stable.
7. Retire the old MCP service only after successful cutover.

## Deploy

```bash
gcloud run deploy ad-engine-mcp-v2 \
  --source /Users/tzechungkao/llm-ad-engine/mcp_server \
  --region us-west1 \
  --allow-unauthenticated
```

## Configure

```bash
gcloud run services update ad-engine-mcp-v2 \
  --region us-west1 \
  --update-env-vars AD_ENGINE_API_BASE_URL=https://ad-engine-api-610270819686.us-west1.run.app
```

If required:

```bash
gcloud run services update ad-engine-mcp-v2 \
  --region us-west1 \
  --update-env-vars AD_ENGINE_API_TOKEN=YOUR_BACKEND_TOKEN
```

## Verify

```bash
cd /Users/tzechungkao/llm-ad-engine/mcp_server
python verify_remote_mcp.py https://YOUR-CLOUD-RUN-URL/mcp
```

Expected tools:

- `search_video_ads_for_buyer`
- `get_ad_by_id`
- `rank_ads_for_buyer`
- `explain_ad_match`
- `get_seller_billing_status`
- `create_billing_support_ticket`

## Switch LangGraph

Update:

```env
MCP_SERVER_URL=https://YOUR-CLOUD-RUN-URL/mcp
```

in `/Users/tzechungkao/llm-ad-engine/langgraph_app/.env`.

## Rollback

If the new MCP service fails verification:

- keep LangGraph pointed at the old MCP endpoint
- fix the new MCP service
- redeploy and re-run verification

Because the old buyer-only MCP service stays up during rollout, rollback is just a config change.
