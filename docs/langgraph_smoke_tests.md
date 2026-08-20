# LangGraph Smoke Tests

Use this after any of these changes:

- rotating the NVIDIA `LLM_API_KEY`
- rotating the MCP/backend service token
- redeploying `ad-engine-api`
- redeploying `ad-engine-mcp-v2`
- changing LangGraph prompts or routing

## Prerequisites

- `/Users/tzechungkao/llm-ad-engine/langgraph_app/.env` contains a valid `LLM_API_KEY`
- `MCP_SERVER_URL` points to `https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp`
- `langgraph_app/.venv` exists and has `langgraph_app/requirements.txt` installed

## One-command smoke test

```bash
cd /Users/tzechungkao/llm-ad-engine
bash langgraph_app/smoke_test.sh
```

## What the script checks

1. Buyer search
   Expected result: returns cat-furniture video ad results.

2. Seller billing
   Expected result: returns billing status for seller `0d162d0e-83ca-474d-a17c-8616475d4e99`.

3. Seller ad lookup
   Expected result: returns ad details for ad `aa622160-c5a9-4241-b8ca-77b30dc79a3a`.

4. Billing ticket creation
   Expected result: returns a submitted ticket response.
   After backend persistence was added, the response should include:
   - `persistence: "database"`

## Override IDs

You can point the script at different records:

```bash
cd /Users/tzechungkao/llm-ad-engine
AD_ID=YOUR_AD_UUID SELLER_ID=YOUR_SELLER_UUID bash langgraph_app/smoke_test.sh
```

## How To Find Real UUIDs

The easiest way is to query the live backend API with your current service token.

```bash
TOKEN="YOUR_CURRENT_SERVICE_TOKEN"
```

Ads:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://ad-engine-api-610270819686.us-west1.run.app/api/ads | python3 -m json.tool
```

Sellers:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://ad-engine-api-610270819686.us-west1.run.app/api/sellers | python3 -m json.tool
```

Best practice:

- copy one real `ad_id` from `/api/ads`
- copy one real `seller_id` from `/api/sellers`
- if the ad payload already contains `seller_id`, you can reuse it for seller-side tests

Current known-good values:

- `AD_ID=aa622160-c5a9-4241-b8ca-77b30dc79a3a`
- `SELLER_ID=0d162d0e-83ca-474d-a17c-8616475d4e99`

## Manual spot checks

Buyer:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/python -m langgraph_app.main "Find video ads for cat furniture"
```

Seller billing:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/python -m langgraph_app.main "Check billing status for seller 0d162d0e-83ca-474d-a17c-8616475d4e99"
```

Seller ad lookup:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/python -m langgraph_app.main "Get ad details for ad aa622160-c5a9-4241-b8ca-77b30dc79a3a"
```

Seller ticket creation:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/python -m langgraph_app.main "Create a billing support ticket for seller 0d162d0e-83ca-474d-a17c-8616475d4e99 with subject Billing smoke test and description LangGraph smoke test ticket creation."
```

## Failure hints

- If buyer and seller flows both fail before any answer appears, check `LLM_API_KEY`.
- If the LLM answers but tool-backed data is missing, verify the MCP server URL and service token configuration.
- If billing ticket creation works but does not show `persistence: "database"`, redeploy `ad-engine-api` again.
