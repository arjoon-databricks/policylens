# Level-up: Unity Gateway Model Service for the Copilot (Claude Sonnet 5)

_Synthetic data; EBCBS is a code name._

## What was built
A first-class **Unity Gateway Model Service** (UC securable) governs the PolicyLens Copilot's LLM access:
- **Name**: `model-services/arjoon_ws_catalog.policylens_ml.policylens_copilot`
- **Routes to**: pay-per-token `models/system.ai.databricks-claude-sonnet-5` (Claude Sonnet 5)
- **Governance**: rate limit 100 req/min (service key); **request/response audit logging** to the inference
  table `arjoon_ws_catalog.policylens_ml.policylens_copilot_payload`
- **Capabilities**: `function_calling: true` (tool-calling passes through), OpenAI-compatible
  (`mlflow/v1/chat/completions`) + `anthropic/v1/messages`
- Quota-independent: model services are UC securables, not registered models — so this works even with the
  registered-model quota full (which still blocks the separate financial-impact Model Serving endpoint).

## How it's queried (agent wired to this)
- base_url: `https://<host>/ai-gateway/mlflow/v1`
- model: `arjoon_ws_catalog.policylens_ml.policylens_copilot`
- Verified: direct chat call returned HTTP 200 with a Claude Sonnet 5 completion.

## Verification
- `04_genai_agent/agent.py` now points at the model service (base_url + full name). Re-run: **SUCCESS** —
  grounded recommendations for all 3 gap policies, tool-calling intact, guardrail still declines clinical questions.
- **Audit trail**: after the run, `policylens_ml.policylens_copilot_payload` held **14 logged requests** —
  the gateway captured every Copilot request/response for auditability.

## Note
An earlier attempt used a classic external-model serving endpoint (`policylens-copilot-llm`) + a PAT secret;
that was replaced by this proper Model Service and cleaned up (endpoint deleted, PAT revoked, secret scope removed).
