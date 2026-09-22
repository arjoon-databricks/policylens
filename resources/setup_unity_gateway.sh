#!/usr/bin/env bash
# PolicyLens — Unity Gateway Model Service for the Copilot's Claude Sonnet 5.
# Creates a governed UC model service (rate limits + request/response audit inference table)
# routing to the pay-per-token claude-sonnet-5 foundation model. Quota-independent
# (model services are UC securables, not registered models). All data synthetic; EBCBS is a code name.
set -euo pipefail
P="${DBNB_PROFILE:-fe-vm-fevm-arjoon-ws}"

# Create the model service in our own schema (parent + model_service_id are QUERY params).
databricks api post "/api/2.1/unity-catalog/model-services?parent=schemas/arjoon_ws_catalog.policylens_ml&model_service_id=policylens_copilot" \
  --profile "$P" --json '{
  "comment": "PolicyLens Copilot — governed Claude Sonnet 5 (synthetic demo; EBCBS code name)",
  "config": {
    "routing": {"destinations": [{
      "name": "claude-sonnet-5",
      "destination_type": "DESTINATION_TYPE_PAY_PER_TOKEN_FOUNDATION_MODEL",
      "traffic_percentage": 100,
      "pay_per_token_config": {"model": "models/system.ai.databricks-claude-sonnet-5"}
    }]},
    "rate_limits": [{"key": "RATE_LIMIT_KEY_SERVICE", "renewal_period": "RATE_LIMIT_RENEWAL_PERIOD_MINUTE", "requests": 100}],
    "inference_table": {"parent": "schemas/arjoon_ws_catalog.policylens_ml", "table_name_prefix": "policylens_copilot"}
  }
}'

# Query it (OpenAI-compatible) — the agent uses this base_url + the fully-qualified name as `model`:
#   base_url = https://<host>/ai-gateway/mlflow/v1
#   model    = arjoon_ws_catalog.policylens_ml.policylens_copilot
# Audit log: arjoon_ws_catalog.policylens_ml.policylens_copilot_payload
