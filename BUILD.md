# BUILD.md — PolicyLens build log, tooling, and decisions

All data synthetic; "EBCBS" is a code name. Built on Databricks workspace `fevm-arjoon-ws` (AWS us-east-1).

## Build methodology

Everything executes **on the workspace**, for two reasons: (1) the build machine's local PyPI is
firewalled (public PyPI unreachable, internal mirror SSO-gated), and (2) the FE Bar evidence gate wants
"notebook cells committed WITH outputs." So each step is a **serverless notebook** or **SQL run**, driven
by a small harness in `resources/`:

- `dbsql.sh` + `_dbsql.py` — run a SQL statement via the SQL Statement Execution API (no local deps).
- `run_notebook.sh` + `_runhelp.py` — import a local `.py` notebook, run it on serverless as a one-time
  job, capture the `dbutils.notebook.exit()` summary and an HTML render of the executed cells.
- `policylens_common.py` — shared UC/Lakebase config + `EvidenceReport`, which prints results and writes
  a markdown report to the raw Volume; `pull_evidence.sh` copies it into `evidence/` as readable text.

This harness was validated on a trivial notebook before scaling to the 2M-row generator.

## AI tools used

- **Claude Code** (Claude) — authored all code, notebooks, SQL, the agent, and this documentation, and
  drove the workspace via the Databricks CLI / REST APIs.
- **Claude Sonnet 5** via the Databricks **Foundation Model API** — the PolicyLens Copilot agent's LLM
  (tool-calling loop).
- **databricks-gte-large-en** — embeddings for the Vector Search policy-document index.
- **LightGBM + MLflow + SHAP** — financial-impact regressor and policy-gap classifier.
- **Databricks Genie** — natural-language semantic self-serve over the governed Metric View + tables.
- FE plugin skills — `databricks-data-generation` (Step 1) and the `databricks-apps-developer` agent (Step 8).

## Step-by-step log (all run on serverless; evidence in `evidence/`)

1. **Synthetic data** (`00_data_generation/generate_synthetic_data.py`) — ~1.99M claims (monthly-partitioned
   parquet), 90 policies across EBCBS + 4 competitors, 72 competitor-policy rows, 40K prior-auth, 2,088
   utilization rows, 58 CPTs. 3 gaps seeded + verified. → `evidence/01_data_generation.md`
2. **Lakeflow SDP + UC governance** — pipeline `policylens-medallion` ran to COMPLETED (1.99M → silver);
   column mask on member PII, region row filter, classification tags. → `evidence/02_lakeflow_pipeline.md`
3. **Gold features** (`02_unity_catalog/gold_features.sql`) — 4 tables; gap detector surfaced all 3 gaps.
   → `evidence/03_gold_features.md`
4. **ML** (`03_ml/train_models.py`) — financial-impact regressor R²≈0.998, MAE ~$151K/mo, SHAP; gap
   classifier; batch scored to UC. → `evidence/04_ml.md`
5. **Lakebase** (`05_lakebase/setup_lakebase.py`) — instance `policylens-oltp`; gold → 3 read tables
   (3 ms reads) + 2 OLTP write tables, seeded review cases. → `evidence/05_lakebase.md`
6. **Gen AI agent** (`04_genai_agent/`) — Vector Search index over 90 policy docs; 6 tools; guardrailed
   Claude agent produced grounded recommendations for all 3 gaps and declined a clinical question.
   → `evidence/06_genai_agent.md`
7. **Genie + Metric View** (`05_genie/`) — Metric View semantic layer; Genie space over 7 tables with the
   8 curated questions; NL query returned correct SQL + answer. → `evidence/07_genie.md`
8. **Databricks App** (`06_app/`) — PolicyLens Command Center. → `evidence/08_app.md`
9. **Evidence pass** — README/BUILD/PLAN, evidence reports, presentation deck.

## Key decisions & trade-offs

- **Bespoke Polars/NumPy generation** over `dbldatagen` so the 3 gaps are correlated *consistently* across
  claims, prior-auth, and utilization (cross-table patterns the ML model and agent then surface).
- **Claims land as monthly parquet files** in the Volume — realistic Auto Loader incremental ingestion and
  a better Lakeflow story.
- **Financial model excludes procedure_count** as a feature so it predicts spend from CPT cost/category/UM
  signals (a real prediction task) rather than trivially reconstructing `procedures × cost`. R² is high
  because monthly spend is strongly cost/volume-driven; SHAP confirms `cat_surgical` + `avg_national_cost` dominate.
- **Rule-based gold `policy_gap_alerts` is the authoritative gap detector**; the ML gap classifier is a
  compact demonstrator of the MLflow multiclass workflow (small rule-labeled set).
- **Agent uses precomputed ML predictions + ad-hoc model load** rather than a Model Serving endpoint (see
  quota constraint below) — same functionality, no endpoint dependency.

## Environment constraints hit — and how each was handled

| Constraint | Handling |
|---|---|
| No `CREATE CATALOG` on the metastore | Used existing `arjoon_ws_catalog` with `policylens_*` schemas instead of a `policylens_demo` catalog |
| UC **registered-model quota** exhausted (5000/5000) | Models **logged** to MLflow (loadable via `runs:/<id>/model`) instead of registered |
| Legacy **workspace model registry disabled** | No fallback registry; app/agent consume ML via UC batch-prediction tables + ad-hoc model load |
| → therefore **no Model Serving endpoint** | Precomputed predictions in `policylens_ml.*` + `mlflow.pyfunc.load_model`; documented — registering later needs no code change |
| Lakebase **managed synced tables** need `CREATE CATALOG` | Loaded Postgres directly from gold via the app's connection path |
| Local **PyPI firewalled** | All compute runs as serverless notebooks / SQL on the workspace |
| Serverless base image lacked `mlflow`/`scikit-learn` after `%pip` env switch | Added them to the `%pip install` line |
| MLflow default **skops** serializer rejects LightGBM types | Used the native `mlflow.lightgbm` flavor |
| Generated datetimes landed as `TIMESTAMP_NTZ` | Enabled the `delta.feature.timestampNtz` table property on bronze |
| Metastore **tag-governance policy** restricts tag values | Tagged member PII `classification = confidential` (allowed value) |
| Claude Sonnet 5 rejects the `temperature` param | Removed it; raised `max_tokens` so extended-thinking leaves room for the answer |
| Genie `serialized_space` API is a string-typed object, `tables` must be sorted | Discovered the schema from a populated space; created the space via the REST API with sorted `data_sources.tables` |
| GitHub repo is **public** and push identity lacked access | Kept EBCBS/synthetic discipline; authenticated the owning GitHub account for push |

## Code review pass (Isaac Review)

A deeper review of the full branch surfaced 7 findings; all were addressed:

| # | Finding | Resolution |
|---|---|---|
| 1 | Lakebase load feeds numpy scalars to psycopg2 | Hardened `load_df` to convert via `.item()` (did not reproduce — original load succeeded — but robust across psycopg2 versions) |
| 2 | App delta-fallback `list_cases` cached 5 min after write | `D.run_query.clear()` after the fallback insert; app redeployed (Lakebase primary path was unaffected) |
| 3 | claims `prior_auth_id` format ≠ `fact_prior_auth.pa_id` | Generator now mints `PA-<8d>` in the PA id space. **No functional impact** (nothing joins on it); deployed data predates the fix (not regenerated) |
| 4 | Simulator `float(None)` on a no-prediction CPT | Guarded with `pd.notna(...)`; app redeployed |
| 5 | Agent reasoning-only turn dropped the assistant message | Append the assistant turn before the follow-up nudge; agent re-run verified (3 grounded recs + guardrail hold) |
| 6 | `more_permissive` severity CASE was dead code | Tier `high` at ≥4 exclusive CPTs (WHERE keeps ≥3); gold re-run |
| 7 | `29882` listed as knee-exclusive but covered by 2 competitors | Corrected to the 4 truly-exclusive codes + comment; matches the computed `n_exclusive_cpts` (no regen) |

Notes: findings #3 and #7 are code/accuracy fixes with no functional impact and were not worth regenerating
2M rows; the deployed silver data reflects the pre-fix values (documented here). The app was redeployed
(deployment `01f1b61f6c1e1d8bbe0f7ae283124b6b`, RUNNING) and the agent re-verified after the fixes.
