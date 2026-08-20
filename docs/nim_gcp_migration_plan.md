# GCP Migration Plan: Hosted NVIDIA API to True NIM

This project currently uses:

- model: `nvidia/nemotron-3-ultra-550b-a55b`
- hosted API base URL: `https://integrate.api.nvidia.com/v1`

That means the stack is already using NVIDIA-hosted inference, but not yet a self-hosted NIM deployment.

## Current Architecture

```text
LangGraph runtime
  -> NVIDIA hosted API
  -> MCP server
  -> ad-engine-api
```

## Target Architecture

```text
LangGraph runtime
  -> self-hosted NIM endpoint on GCP
  -> MCP server
  -> ad-engine-api
```

## Recommended Migration Sequence

### Phase 1. Freeze the current contract

Do not change the LangGraph app contract beyond environment configuration.

Keep:

- `LLM_MODEL`
- the OpenAI-compatible client shape in `langgraph_app/models.py`

Only plan to swap:

- `LLM_BASE_URL`
- possibly `LLM_API_KEY` / auth token

### Phase 2. Deploy a single NIM endpoint first

Start with one controlled environment before Kubernetes.

Recommended first shape:

- one GPU-backed VM or managed GPU environment on GCP
- one NIM service
- one internal or restricted HTTPS endpoint

Why:

- easier debugging
- lower blast radius
- preserves rollback to the hosted NVIDIA endpoint

### Phase 3. Validate compatibility

Confirm the self-hosted NIM service supports the same request/response pattern expected by:

- `langgraph_app/models.py`
- `langgraph_app/llm_json.py`

Run:

```bash
cd /Users/tzechungkao/llm-ad-engine
bash langgraph_app/smoke_test.sh
```

### Phase 4. Cut over by config only

Update:

- `/Users/tzechungkao/llm-ad-engine/langgraph_app/.env`

Change:

- `LLM_BASE_URL` from hosted NVIDIA to your NIM endpoint
- `LLM_API_KEY` if the NIM endpoint uses a different auth secret

### Phase 5. Harden production

Before full traffic:

- add endpoint health checks
- set request timeouts
- measure latency on buyer and seller flows
- keep rollback instructions to the hosted endpoint
- run `langgraph_app/smoke_test.sh` after every deploy

### Phase 6. Scale only after stability

Only move to a larger GCP architecture if traffic requires it:

- load balancer
- private service networking
- autoscaling GPU pools
- Kubernetes / Helm

## Repo Changes Needed Later

When moving to true NIM, this repo should change only in a few places:

- `langgraph_app/.env`
- maybe `langgraph_app/README.md`
- maybe deployment docs

Core graph logic, MCP integration, and backend API calls should stay unchanged.

## Rollback Plan

If the NIM deployment underperforms:

1. point `LLM_BASE_URL` back to `https://integrate.api.nvidia.com/v1`
2. restore the hosted NVIDIA API key if needed
3. rerun `bash langgraph_app/smoke_test.sh`

## Recommendation

Best order for this project:

1. continue validating workflows with the hosted NVIDIA endpoint
2. deploy one single-node NIM endpoint on GCP
3. cut over by environment variable only
4. scale later if the workload justifies it
