# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Step 5: Lakebase (operational serving)
# MAGIC
# MAGIC Lakebase Postgres instance `policylens-oltp` (PG 16). Two paths:
# MAGIC - **Read path** — gold tables loaded into Postgres for low-latency app reads:
# MAGIC   `policy_comparison_current`, `cpt_utilization_current`, `policy_gap_alerts`
# MAGIC - **Write path** — transactional OLTP tables for analyst review cases:
# MAGIC   `policy_review_cases`, `recommendation_actions`
# MAGIC
# MAGIC NOTE: managed UC *synced tables* need a Database Catalog (CREATE CATALOG on the metastore),
# MAGIC which this user lacks — so we load Postgres directly from gold (the same connection the app uses).
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------

# MAGIC %pip install psycopg2-binary databricks-sdk --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import uuid, json
import requests
import psycopg2
from psycopg2.extras import execute_values
from databricks.sdk import WorkspaceClient

INSTANCE = "policylens-oltp"
PG_DB = "databricks_postgres"
PG_SCHEMA = "policylens"

# The serverless SDK lacks w.database, so call the Database REST API directly.
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
DBX_HOST = ctx.apiUrl().get()
DBX_TOKEN = ctx.apiToken().get()
H = {"Authorization": f"Bearer {DBX_TOKEN}"}

inst = requests.get(f"{DBX_HOST}/api/2.0/database/instances/{INSTANCE}", headers=H).json()
host = inst["read_write_dns"]
inst = type("I", (), {"pg_version": inst.get("pg_version"), "read_write_dns": host})
cred = requests.post(f"{DBX_HOST}/api/2.0/database/credentials", headers=H,
                     json={"instance_names": [INSTANCE], "request_id": str(uuid.uuid4())}).json()
token = cred["token"]
user = WorkspaceClient().current_user.me().user_name

conn = psycopg2.connect(host=host, port=5432, dbname=PG_DB, user=user, password=token, sslmode="require")
conn.autocommit = True
cur = conn.cursor()
cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA}")

rep = EvidenceReport("05_lakebase", "Step 5 — Lakebase operational serving")
rep.kv("instance", INSTANCE).kv("pg_version", inst.pg_version).kv("read_write_dns", host)
rep.kv("database.schema", f"{PG_DB}.{PG_SCHEMA}")

# COMMAND ----------

# MAGIC %md ## Read path — load gold tables into Postgres

# COMMAND ----------

def _py(v):
    """Convert numpy scalars (int64/bool_/float64) to Python natives for psycopg2."""
    if pd_isna(v):
        return None
    return v.item() if hasattr(v, "item") else v

def load_df(pdf, table, ddl, cols):
    cur.execute(f"DROP TABLE IF EXISTS {PG_SCHEMA}.{table} CASCADE")
    cur.execute(ddl)
    rows = [tuple(_py(r[c]) for c in cols) for _, r in pdf.iterrows()]
    execute_values(cur, f"INSERT INTO {PG_SCHEMA}.{table} ({', '.join(cols)}) VALUES %s", rows)
    return len(rows)

def pd_isna(v):
    try:
        import pandas as pd
        return pd.isna(v)
    except Exception:
        return v is None

pcf = spark.table(f"{CATALOG}.{GOLD}.policy_comparison_features").toPandas()
n1 = load_df(pcf, "policy_comparison_current",
    f"""CREATE TABLE {PG_SCHEMA}.policy_comparison_current(
        policy_id text PRIMARY KEY, policy_name text, policy_category text, topic text,
        prior_auth_required boolean, n_ebcbs_cpts int, n_exclusive_cpts int, n_competitors int,
        pa_requests int, denial_rate double precision, appeal_rate double precision,
        avg_competitor_restrictiveness double precision, total_procedures bigint,
        total_allowed double precision, criteria_text text)""",
    ["policy_id","policy_name","policy_category","topic","prior_auth_required","n_ebcbs_cpts",
     "n_exclusive_cpts","n_competitors","pa_requests","denial_rate","appeal_rate",
     "avg_competitor_restrictiveness","total_procedures","total_allowed","criteria_text"])

cus = spark.table(f"{CATALOG}.{GOLD}.cpt_utilization_summary").toPandas()
n2 = load_df(cus, "cpt_utilization_current",
    f"""CREATE TABLE {PG_SCHEMA}.cpt_utilization_current(
        cpt_code text PRIMARY KEY, description text, category text, avg_national_cost double precision,
        total_procedures bigint, total_allowed double precision, total_paid double precision,
        avg_cost_per_procedure double precision, avg_prior_auth_rate double precision,
        avg_denial_rate double precision, months_active int)""",
    ["cpt_code","description","category","avg_national_cost","total_procedures","total_allowed",
     "total_paid","avg_cost_per_procedure","avg_prior_auth_rate","avg_denial_rate","months_active"])

pga = spark.table(f"{CATALOG}.{GOLD}.policy_gap_alerts").toPandas()
pga = pga.reset_index(drop=True); pga["alert_id"] = pga.index + 1
n3 = load_df(pga, "policy_gap_alerts",
    f"""CREATE TABLE {PG_SCHEMA}.policy_gap_alerts(
        alert_id int PRIMARY KEY, policy_id text, policy_name text, gap_type text,
        severity text, description text, detail_metric double precision)""",
    ["alert_id","policy_id","policy_name","gap_type","severity","description","detail_metric"])

rep.h("Read path (gold -> Postgres)")
rep.kv("policy_comparison_current", n1).kv("cpt_utilization_current", n2).kv("policy_gap_alerts", n3)

# COMMAND ----------

# MAGIC %md ## Write path — transactional OLTP tables + seed review cases

# COMMAND ----------

cur.execute(f"""CREATE TABLE IF NOT EXISTS {PG_SCHEMA}.policy_review_cases(
    case_id text PRIMARY KEY, policy_id text, gap_type text, status text,
    assigned_analyst text, recommendation_json jsonb, financial_impact_json jsonb,
    created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now())""")
cur.execute(f"""CREATE TABLE IF NOT EXISTS {PG_SCHEMA}.recommendation_actions(
    action_id text PRIMARY KEY, case_id text REFERENCES {PG_SCHEMA}.policy_review_cases(case_id),
    action_type text, cpt_code text, status text, created_at timestamptz DEFAULT now())""")

# seed one open review case per detected gap alert (transactional write demo)
cur.execute(f"TRUNCATE {PG_SCHEMA}.recommendation_actions, {PG_SCHEMA}.policy_review_cases CASCADE")
seed = 0
for _, a in pga.iterrows():
    cid = f"CASE-{a['policy_id']}-{a['gap_type'][:4].upper()}"
    rec = {"gap_type": a["gap_type"], "severity": a["severity"], "suggestion": "Review vs competitor benchmark"}
    fin = {"detail_metric": None if pd_isna(a["detail_metric"]) else float(a["detail_metric"])}
    cur.execute(
        f"""INSERT INTO {PG_SCHEMA}.policy_review_cases
            (case_id, policy_id, gap_type, status, assigned_analyst, recommendation_json, financial_impact_json)
            VALUES (%s,%s,%s,'open','unassigned',%s,%s) ON CONFLICT (case_id) DO NOTHING""",
        (cid, a["policy_id"], a["gap_type"], json.dumps(rec), json.dumps(fin)))
    seed += 1

rep.h("Write path (OLTP)")
cur.execute(f"SELECT count(*) FROM {PG_SCHEMA}.policy_review_cases")
rep.kv("policy_review_cases seeded", cur.fetchone()[0])
rep.kv("recommendation_actions table", "created (empty, written by app)")

# COMMAND ----------

# MAGIC %md ## Verify low-latency reads

# COMMAND ----------

import time
t0 = time.time()
cur.execute(f"SELECT policy_id, gap_type, severity FROM {PG_SCHEMA}.policy_gap_alerts ORDER BY policy_id")
alerts = cur.fetchall()
lat = (time.time() - t0) * 1000
rep.h("Sample serving read")
rep.kv("gap alerts read latency", f"{lat:.0f} ms").kv("rows", len(alerts))
for r in alerts:
    rep.line(f"  - {r[0]} | {r[1]} | {r[2]}")

cur.close(); conn.close()
path = rep.save()
dbutils.notebook.exit(f"STEP5_OK read_tables=3 oltp_tables=2 cases={seed} host={host} evidence={path}")
