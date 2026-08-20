#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/langgraph_app/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing virtualenv Python at ${PYTHON_BIN}"
  echo "Create it first with:"
  echo "  python3 -m venv langgraph_app/.venv"
  echo "  langgraph_app/.venv/bin/pip install -r langgraph_app/requirements.txt"
  exit 1
fi

AD_ID="${AD_ID:-aa622160-c5a9-4241-b8ca-77b30dc79a3a}"
SELLER_ID="${SELLER_ID:-0d162d0e-83ca-474d-a17c-8616475d4e99}"

run_case() {
  local label="$1"
  local prompt="$2"

  echo
  echo "============================================================"
  echo "${label}"
  echo "Prompt: ${prompt}"
  echo "============================================================"
  "${PYTHON_BIN}" -m langgraph_app.main "${prompt}"
}

run_case \
  "1. Buyer Search" \
  "Find video ads for cat furniture"

run_case \
  "2. Seller Billing" \
  "Check billing status for seller ${SELLER_ID}"

run_case \
  "3. Seller Ad Lookup" \
  "Get ad details for ad ${AD_ID}"

run_case \
  "4. Billing Ticket Creation" \
  "Create a billing support ticket for seller ${SELLER_ID} with subject Billing smoke test and description LangGraph smoke test ticket creation."

