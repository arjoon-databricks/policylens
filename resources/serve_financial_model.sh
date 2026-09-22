#!/usr/bin/env bash
# PolicyLens — Level-up A: serve the financial-impact model (READY-TO-RUN once the
# UC registered-model quota is freed). This makes the "one-config change" concrete.
#
# Prereq: 03_ml/register_model.py has registered arjoon_ws_catalog.policylens_ml.financial_impact_model
#         (currently blocked by QUOTA_EXCEEDED on metastore c0da88f1... — 5000 model limit).
#
# Steps:
#   1) create a Model Serving endpoint for the registered model (scale-to-zero, Small)
#   2) enable AI/Unity Gateway INFERENCE TABLE on it (request/response audit logging to UC)
#      NOTE: custom-model endpoints support gateway inference tables (not LLM guardrails).
#   3) then repoint the app simulator / agent simulate_financial_impact tool to call the endpoint.
set -euo pipefail
P="${DBNB_PROFILE:-fe-vm-fevm-arjoon-ws}"
ENDPOINT="policylens-financial-impact"
MODEL="arjoon_ws_catalog.policylens_ml.financial_impact_model"
VERSION="${1:?usage: serve_financial_model.sh <registered_model_version>}"

echo ">> creating serving endpoint $ENDPOINT for $MODEL v$VERSION"
databricks serving-endpoints create --profile "$P" --json "{
  \"name\": \"$ENDPOINT\",
  \"config\": {
    \"served_entities\": [{
      \"entity_name\": \"$MODEL\",
      \"entity_version\": \"$VERSION\",
      \"workload_size\": \"Small\",
      \"scale_to_zero_enabled\": true
    }]
  }
}"

echo ">> enabling AI/Unity Gateway inference table (audit logging) on $ENDPOINT"
databricks serving-endpoints put-ai-gateway "$ENDPOINT" --profile "$P" --json '{
  "inference_table_config": {
    "enabled": true,
    "catalog_name": "arjoon_ws_catalog",
    "schema_name": "policylens_ml",
    "table_name_prefix": "financial_impact_serving"
  },
  "usage_tracking_config": {"enabled": true}
}'

echo ">> done. Then set an env/flag so 06_app/data.py + 04_genai_agent/agent.py call the endpoint"
echo "   (scoring URL: <workspace>/serving-endpoints/$ENDPOINT/invocations)"
