# Agent Entrypoints

This project now supports two ways to invoke agents:

- LangGraph CLI
- LangGraph API wrapper

## CLI

Generic routing:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/python -m langgraph_app.main "Find video ads for cat furniture"
```

## API Wrapper

Start the API locally:

```bash
cd /Users/tzechungkao/llm-ad-engine
langgraph_app/.venv/bin/uvicorn langgraph_app.api:app --host 0.0.0.0 --port 8010
```

Health check:

```bash
curl -s http://127.0.0.1:8010/health
```

## Minimum Useful Entrypoints

### Generic router

```text
POST /agent/run
```

Use when you want the top-level graph to decide buyer vs seller vs QA.

### Buyer search

```text
POST /agent/buyer/search
```

Use for:

- find matching ads
- find video ads
- rank ads for a buyer query

### Buyer explanation

```text
POST /agent/buyer/explain
```

Use for:

- explain why a specific ad matched
- inspect one ad against one buyer query

### Seller billing

```text
POST /agent/seller/billing
```

Use for:

- billing status
- balance questions
- billing support ticket creation

### Seller ad ops

```text
POST /agent/seller/ad-ops
```

Use for:

- look up an ad by UUID
- inspect ad status and metadata

### Seller support

```text
POST /agent/seller/support
```

Use for:

- mixed seller support issues
- ad + billing combinations
- ambiguous seller requests

### QA / validation

```text
POST /agent/qa
```

Use for:

- smoke tests
- tool validation
- regression checks

## Example Requests

Buyer search:

```bash
curl -s -X POST http://127.0.0.1:8010/agent/buyer/search \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Find video ads for cat furniture"}'
```

Seller billing:

```bash
curl -s -X POST http://127.0.0.1:8010/agent/seller/billing \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Check billing status for seller 0d162d0e-83ca-474d-a17c-8616475d4e99"}'
```

Seller ticket creation:

```bash
curl -s -X POST http://127.0.0.1:8010/agent/seller/billing \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Create a billing support ticket for seller 0d162d0e-83ca-474d-a17c-8616475d4e99 with subject Billing smoke test and description LangGraph smoke test ticket creation."}'
```
