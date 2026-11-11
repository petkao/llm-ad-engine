# LangGraph Chat On Cloud Run

This deploy keeps NVIDIA hosted inference in place.

The LangGraph service runs on Cloud Run, but the LLM still uses:

- `LLM_BASE_URL=https://integrate.api.nvidia.com/v1`
- `LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b`

## What Moves To Cloud Run

- browser chat UI at `/portal`, `/buyer`, `/seller` and `/chat`
- LangGraph runtime
- buyer and seller agent HTTP endpoints

## What Stays External

- NVIDIA hosted API for inference
- deployed MCP server at `https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp`
- deployed backend API at `https://ad-engine-api-610270819686.us-west1.run.app`

## Which Command To Use

The service already exists in project `ad-engine-4da45`, region `us-west1`, with all of its env vars set.

- **Redeploying new code:** use the redeploy command below. It keeps every existing setting.
- **Creating the service from scratch** (new project, or after deleting it): use the first-time setup.

Always pass `--project`: the gcloud default project on this machine is a different one.

## Redeploy

From the repo root:

```bash
cd /Users/tzechungkao/llm-ad-engine
```

```bash
gcloud run deploy ad-engine-langgraph-chat \
  --source . \
  --project ad-engine-4da45 \
  --region us-west1
```

To change one setting, use `--update-env-vars`, which leaves the others alone:

```bash
gcloud run services update ad-engine-langgraph-chat \
  --project ad-engine-4da45 \
  --region us-west1 \
  --update-env-vars DEFAULT_SEARCH_LIMIT=5
```

Don't run the first-time command against the existing service. `--set-env-vars` replaces the whole list of variables. If the placeholder key is left in, it overwrites the real key and the app stops answering.

## First-Time Setup

Replace `YOUR_NVIDIA_API_KEY` with a real key from `https://build.nvidia.com` before running this:

```bash
gcloud run deploy ad-engine-langgraph-chat \
  --source . \
  --project ad-engine-4da45 \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars "LLM_BASE_URL=https://integrate.api.nvidia.com/v1,LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b,MCP_SERVER_URL=https://ad-engine-mcp-v2-610270819686.us-west1.run.app/mcp,LLM_TEMPERATURE=0.1,SYNTHETIC_DEVICE_ID=langgraph-buyer-device,DEFAULT_SEARCH_LIMIT=5,DEFAULT_EXPLAIN_LIMIT=10,LLM_API_KEY=YOUR_NVIDIA_API_KEY"
```

If you later protect the MCP service, add its token without touching the other variables:

```bash
gcloud run services update ad-engine-langgraph-chat \
  --project ad-engine-4da45 \
  --region us-west1 \
  --update-env-vars MCP_SERVER_AUTH_TOKEN=YOUR_MCP_BEARER_TOKEN
```

## Better Secret Handling

The live service currently stores `LLM_API_KEY` as a plain env var. For production, Secret Manager is better: the key stays out of the service config, and rotating it means adding a secret version instead of editing the service.

The project has no NVIDIA secret yet. To move the key into Secret Manager:

1. Create the secret (the command reads the key from your terminal, so it doesn't land in shell history):

   ```bash
   read -rs NVIDIA_KEY && printf %s "$NVIDIA_KEY" | gcloud secrets create nvidia-api-key \
     --project ad-engine-4da45 \
     --data-file=-
   ```

2. Let the service's runtime account read it:

   ```bash
   gcloud secrets add-iam-policy-binding nvidia-api-key \
     --project ad-engine-4da45 \
     --member "serviceAccount:610270819686-compute@developer.gserviceaccount.com" \
     --role roles/secretmanager.secretAccessor
   ```

3. Swap the plain variable for the secret in one update:

   ```bash
   gcloud run services update ad-engine-langgraph-chat \
     --project ad-engine-4da45 \
     --region us-west1 \
     --remove-env-vars LLM_API_KEY \
     --update-secrets LLM_API_KEY=nvidia-api-key:latest
   ```

Cloud Run reads secrets only when a revision starts, so after adding a new secret version, roll a new revision (any `services update` or redeploy).

## Verify

Health:

```bash
curl -s https://ad-engine-langgraph-chat-610270819686.us-west1.run.app/health
```

Chat page:

```text
https://ad-engine-langgraph-chat-610270819686.us-west1.run.app/portal
```

Sample API call:

```bash
curl -s -X POST https://ad-engine-langgraph-chat-610270819686.us-west1.run.app/agent/buyer/search \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Find video ads for cat furniture"}'
```

## User-Facing Entry Points

For non-technical buyers and sellers, use:

- `https://ad-engine-langgraph-chat-610270819686.us-west1.run.app/portal`, which links to the two sites below
- `/buyer` for buyers and `/seller` for sellers

`/chat` is the shared internal hub for mixed routing and QA.

They do not need direct access to the MCP server or backend API.
