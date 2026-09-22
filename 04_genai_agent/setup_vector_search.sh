#!/usr/bin/env bash
# PolicyLens — Step 6 Vector Search setup (run once). All data synthetic; EBCBS is a code name.
# The policy_documents source table is created by 02_unity_catalog (see gold_features) / below.
set -euo pipefail
P="${DBNB_PROFILE:-fe-vm-fevm-arjoon-ws}"

# 1) Source table for RAG (built from silver_medical_policy; CDF enabled) — see also resources/dbsql.sh
#    CREATE OR REPLACE TABLE arjoon_ws_catalog.policylens_gold.policy_documents
#      TBLPROPERTIES (delta.enableChangeDataFeed = true) AS SELECT ... document_text ...

# 2) Vector Search endpoint
databricks vector-search-endpoints create-endpoint policylens-vs STANDARD --no-wait --profile "$P"

# 3) Delta-sync index over policy_documents, embeddings via databricks-gte-large-en
databricks vector-search-indexes create-index --profile "$P" --json '{
  "name": "arjoon_ws_catalog.policylens_gold.policy_documents_index",
  "endpoint_name": "policylens-vs",
  "primary_key": "policy_id",
  "index_type": "DELTA_SYNC",
  "delta_sync_index_spec": {
    "source_table": "arjoon_ws_catalog.policylens_gold.policy_documents",
    "pipeline_type": "TRIGGERED",
    "embedding_source_columns": [
      {"name": "document_text", "embedding_model_endpoint_name": "databricks-gte-large-en"}
    ]
  }
}'

# 4) UC function tools: resources/dbsql.sh over 04_genai_agent/uc_tools.sql
# 5) Agent: resources/run_notebook.sh 04_genai_agent/agent.py
