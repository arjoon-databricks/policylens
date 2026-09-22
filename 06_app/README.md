# PolicyLens Command Center (Databricks App)

Streamlit app for the FE Bar demo. **All data is SYNTHETIC**; the health plan is
referred to only as **EBCBS** (a Blue Cross Blue Shield plan code name).

Value is framed as **admin workflow automation, faster time-to-decision, and
better-informed policy decisions** — never as cost savings. Dollar figures in
the simulator are **budget-exposure / financial-impact context** for policy
administration, not savings targets.

## Sections
1. **Executive KPIs** — target operating-model outcomes (cycle time, analyst hours redirected, gaps surfaced) + live counts.
2. **Policy Dashboard** — EBCBS policies from `policy_comparison_features` with gap alerts; the 3 seeded gaps (KNEE / SPINE / CARD) are starred.
3. **Comparison** — EBCBS vs Competitor_A–D coverage & criteria (join by policy_name in `silver_medical_policy`).
4. **Financial Simulator** — `simulate_financial_impact(policy, change, cpt)` UC function over ML predictions.
5. **Copilot** — embedded Genie Conversation API over the governed space.
6. **Review Cases** — Lakebase read/write (`policylens-oltp`), with Delta fallback (`policylens_ml.app_review_cases`).

## Data paths
- **SQL Warehouse** (`8085db376d889a9a`) via `databricks-sql-connector` + SP OAuth — reads gold/silver/ML, calls UC functions.
- **Lakebase** (`policylens-oltp`) via Database credentials REST + psycopg2 — review cases (falls back to Delta if SP auth fails).
- **Genie** space `01f1b60efe501b9f9c318dfa6d59059b` via Conversation API.

## Files
- `app.py` — main UI (6 tabs, styling).
- `data.py` — SQL warehouse access + domain queries.
- `lakebase.py` — review-cases store (Lakebase primary, Delta fallback).
- `genie.py` — Genie Conversation API client.
- `app.yaml` — Streamlit launch config + warehouse env mapping.
- `requirements.txt` — Python deps (installed on app compute).

## Deploy
```bash
P=fe-vm-fevm-arjoon-ws
databricks sync . /Workspace/Users/arjoon.jeyapaalan@databricks.com/policylens-command-center -p $P
databricks apps deploy policylens-command-center \
  --source-code-path /Workspace/Users/arjoon.jeyapaalan@databricks.com/policylens-command-center -p $P
```
App declares a `sql-warehouse` resource (grants the app SP use of the warehouse)
and a `database` resource for Lakebase.
