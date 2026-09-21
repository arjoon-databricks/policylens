# PolicyLens — Medical Policy Intelligence Platform

> An end-to-end AI prototype that helps medical-policy analysts at a Blue Cross Blue Shield
> health plan (**EBCBS** — a code name) review medical policies: compare EBCBS policies against
> competitors, surface coverage/criteria gaps, simulate the financial impact of policy changes,
> and draft data-grounded recommendations.

**All data in this repo is synthetic. "EBCBS" is a code name — no real customer data or names appear anywhere.**

> **ROI framing:** value is framed as **admin workflow automation, faster time-to-decision, and
> better-informed policy decisions** — never cost savings. A payer must not appear to make medical
> decisions based on cost.

---

## What it does

Two personas:
- **Executive sponsor** (VP Medical Policy / CMO) — policy competitiveness, appeals, admin efficiency.
- **Domain owner** (Medical Policy Analyst lead) — accurate comparisons and defensible recommendations.

Four capabilities: **compare** EBCBS vs 4 competitors, **identify gaps**, **simulate** financial impact
of CPT/criteria changes, and **generate** grounded recommendations.

## Six Databricks-native layers (one connected journey)

| # | Layer | Implementation |
|---|---|---|
| 1 | **Lakeflow** | Spark Declarative Pipeline `policylens-medallion` — Auto Loader ingests the raw Volume → 6 bronze + 6 silver tables with DQ expectations (`01_lakeflow_pipeline/`) |
| 2 | **Unity Catalog** | Automatic lineage; column mask on member PII; region row filter (RLS); governance tags (`02_unity_catalog/governance.sql`) |
| 3 | **Lakebase** | Postgres instance `policylens-oltp` — gold loaded to read tables (3 ms reads) + transactional review-case tables (`05_lakebase/`) |
| 4 | **ML / Gen AI** | LightGBM financial-impact regressor (R²≈0.998, SHAP) + policy-gap classifier, MLflow-tracked, batch-scored to UC (`03_ml/`) |
| 5 | **Gen AI Agent** | PolicyLens Copilot: Claude (Foundation Model API) + Vector Search RAG over policy docs + 6 UC/Lakebase tools + policy-admin guardrails (`04_genai_agent/`) |
| 6 | **Genie** | Metric View semantic layer + Genie space with 8 curated questions over 7 governed tables (`05_genie/`) |
| — | **Databricks App** | PolicyLens Command Center: KPI tiles, policy dashboard, comparison, financial simulator, embedded Genie copilot, review cases (`06_app/`) |

Data journey: `raw Volume → bronze_* → silver_* (governed) → gold features → { ML batch scores, Vector Search index, Metric View } → Agent + Genie + App`, with the operational read/write path served by Lakebase.

## Unity Catalog layout

- Catalog **`arjoon_ws_catalog`** (this workspace user lacks `CREATE CATALOG`, so PolicyLens lives here
  rather than a dedicated `policylens_demo` catalog — see [BUILD.md](BUILD.md)).
- Schemas: `policylens_bronze` (+ `raw` Volume), `policylens_silver`, `policylens_gold`, `policylens_ml`.

## The 3 seeded gaps (present and verified across every layer)

| Policy | Gap | Signal |
|---|---|---|
| `P-2024-KNEE-01` | Overly **permissive** | Covers 4 CPTs 3/4 competitors exclude; no prior auth; competitors 0.80 restrictive |
| `P-2024-SPINE-01` | Overly **restrictive** | 32% PA denial (vs 11% baseline), 19% appeals; competitors looser (0.39) |
| `P-2024-CARD-01` | **Ambiguous** language | PA denial varies 9.8% (Rochester) → 38.4% (Utica-Mohawk) by region |

## Target business KPIs

| KPI | Manual baseline | With PolicyLens |
|---|---|---|
| Annual policy review cycle | ~12 weeks | < 1 week |
| Time per policy comparison | ~8 hours | ~30 minutes |
| Financial simulation turnaround | ~2 weeks | real-time |
| Policy gaps identified per cycle | ~15 | ~50 |
| Analyst hours per cycle | ~2,400 | ~400 (~2,000 saved) |

## Repo structure

```
00_data_generation/   synthetic data generator (2M claims, policies, PA, utilization)
01_lakeflow_pipeline/  Spark Declarative Pipeline (bronze -> silver + DQ)
02_unity_catalog/      governance (masks/RLS/tags) + gold feature tables
03_ml/                 LightGBM financial-impact model + gap classifier (MLflow)
04_genai_agent/        UC function tools + Vector Search + Claude agent
05_genie/              Metric View + Genie space config
06_app/                PolicyLens Command Center (Databricks App)
evidence/              text evidence reports + executed-notebook HTML for every step
resources/             run harness (SQL + serverless-notebook runners), shared config
```

## How it was built / reproduced

Everything runs **on the workspace** (local PyPI is firewalled), which also satisfies the evidence gate
("notebook cells with outputs"). The harness in `resources/`:
- `dbsql.sh` — run SQL via the Statement Execution API
- `run_notebook.sh` — import + run a notebook on serverless, capture outputs
- `policylens_common.py` — shared UC/Lakebase config + an `EvidenceReport` that writes each step's
  results as markdown to the Volume; pulled into `evidence/` via `pull_evidence.sh`

Build order matches the step folders (`00_…` → `06_…`). See [BUILD.md](BUILD.md) for the full log,
AI tools used, decisions/trade-offs, and the environment constraints handled; [PLAN.md](PLAN.md) for
the plan, personas, and KPIs.

## Evidence

Each step has a readable text report in `evidence/NN_*.md` plus an executed-notebook HTML render.
These are the primary execution evidence (the evaluator reads text, not screenshots).
