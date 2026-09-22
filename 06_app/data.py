"""SQL warehouse data access for PolicyLens Command Center.

All data is SYNTHETIC. The health plan is referred to only as "EBCBS".
Reads governed gold/silver/ML tables and calls Unity Catalog function tools
via the Databricks SQL warehouse using the app service principal (OAuth).
"""
import os
import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

CATALOG = "arjoon_ws_catalog"
GOLD = f"{CATALOG}.policylens_gold"
SILVER = f"{CATALOG}.policylens_silver"
ML = f"{CATALOG}.policylens_ml"

WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "8085db376d889a9a")

_cfg = Config()  # auto-configures from the app service principal env


def _connect():
    return sql.connect(
        server_hostname=_cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: _cfg.authenticate,
    )


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    """Run a read query and return a DataFrame (cached 5 min)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            cols = [c[0] for c in cur.description]
            rows = cur.fetchall()
    return pd.DataFrame([list(r) for r in rows], columns=cols)


def execute(statement: str):
    """Run a write/DDL statement (not cached)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(statement)


# ---------- Domain queries ----------

def get_policies() -> pd.DataFrame:
    return run_query(f"""
        SELECT policy_id, policy_name, policy_category, topic, prior_auth_required,
               n_ebcbs_cpts, n_exclusive_cpts, n_competitors, pa_requests,
               denial_rate, appeal_rate, avg_competitor_restrictiveness,
               total_procedures, total_allowed, criteria_text
        FROM {GOLD}.policy_comparison_features
        ORDER BY policy_id
    """)


def get_gap_alerts() -> pd.DataFrame:
    return run_query(f"""
        SELECT policy_id, policy_name, gap_type, severity, description, detail_metric
        FROM {GOLD}.policy_gap_alerts
        ORDER BY CASE severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, policy_id
    """)


def get_policy_by_name(policy_name: str) -> pd.DataFrame:
    """All payers (EBCBS + Competitor_A..D) that publish a policy with this name."""
    safe = policy_name.replace("'", "''")
    return run_query(f"""
        SELECT payer, policy_id, policy_name, prior_auth_required,
               size(cpt_codes_covered) AS n_cpts,
               array_join(cpt_codes_covered, ', ') AS cpt_codes,
               criteria_text
        FROM {SILVER}.silver_medical_policy
        WHERE policy_name = '{safe}'
        ORDER BY CASE WHEN payer = 'EBCBS' THEN 0 ELSE 1 END, payer
    """)


def get_cpts_for_policy(policy_id: str) -> pd.DataFrame:
    safe = policy_id.replace("'", "''")
    return run_query(f"""
        SELECT DISTINCT cpt_code, description, category,
               annual_allowed, avg_cost_per_procedure, avg_denial_rate
        FROM {GOLD}.financial_impact_scenarios
        WHERE policy_id = '{safe}'
        ORDER BY annual_allowed DESC
    """)


def simulate_financial_impact(policy_id: str, change_type: str, cpt: str) -> pd.DataFrame:
    p = policy_id.replace("'", "''")
    c = cpt.replace("'", "''")
    ct = change_type.replace("'", "''")
    return run_query(
        f"SELECT * FROM {GOLD}.simulate_financial_impact('{p}', '{ct}', '{c}')"
    )


def get_pa_analysis(policy_id: str) -> pd.DataFrame:
    p = policy_id.replace("'", "''")
    return run_query(
        f"SELECT * FROM {GOLD}.get_prior_auth_analysis('{p}')"
    )
