# Step 8 — PolicyLens Command Center (Databricks App)

_Synthetic data; EBCBS is a code name._

## Deployment

- **URL**: https://policylens-command-center-7474656670319354.aws.databricksapps.com
- **Status** (verified via `databricks apps get`): app **RUNNING**, compute **ACTIVE**, active deployment **SUCCEEDED**
- **Stack**: Streamlit Databricks App; service principal `ea440edc-9f62-4670-8d34-d234330093da`
- **Declared resources**: `sql-warehouse` (CAN_USE, `8085db376d889a9a`) + `database` (CAN_CONNECT_AND_CREATE, `policylens-oltp`)
- **Files**: `06_app/{app.py, data.py, lakebase.py, genie.py, app.yaml, requirements.txt, README.md}`

## Tabs (all six)

1. **Executive KPI tiles** — before/after (12 weeks → <1 week; 8h → 30min; 2 weeks → real-time; 15 → 50 gaps; 2,400 → ~400 analyst hours).
2. **Policy dashboard** — 18 EBCBS policies + gap alerts; scatter + table.
3. **Comparison view** — EBCBS vs Competitor_A–D coverage/criteria + comparison features.
4. **Financial simulator** — add/remove a CPT → `simulate_financial_impact` (ML-grounded annualized $).
5. **Copilot** — embedded Genie NL Q&A (Conversation API) → answer + data + generated SQL.
6. **Review cases** — lists Lakebase `policy_review_cases`; creates new cases (write path).

## Data paths (all working — no fallback used)

- **SQL Warehouse** — KPIs, dashboard, comparison, simulator (UC function `simulate_financial_impact`).
- **Lakebase** — review-cases read/write; app SP authenticates via the Database Credentials API; new case
  creation verified (e.g. `CASE-P-2024-KNEE-01-5FE931`).
- **Genie** — space `01f1b60efe501b9f9c318dfa6d59059b`; returns NL answer + table + SQL.

## Grants applied (by owner)

- App SP: `USE CATALOG` on `arjoon_ws_catalog`; `USE SCHEMA`+`SELECT` on `policylens_gold/silver/ml`;
  `EXECUTE` on `policylens_gold` functions; Genie space `CAN_RUN`.
- Lakebase: SP's Postgres role granted `USAGE` on schema `policylens` + `SELECT/INSERT/UPDATE/DELETE`
  on its tables (+ default privileges) — the fix that enabled the SP read/write path.

## ROI framing

Value is presented as workflow automation / faster time-to-decision / analyst capacity redirected.
Dollar figures are labeled "budget exposure / financial-impact context," explicitly **not** cost savings.

## Demo note

First Copilot question after the serverless warehouse idles can take ~2–3 min (cold start); warm it with
one throwaway query before presenting. Stop the app between demos to save spend:
`databricks apps stop policylens-command-center -p fe-vm-fevm-arjoon-ws`.
