"""Operational review-cases store for PolicyLens Command Center.

Primary path: Lakebase (managed Postgres, instance `policylens-oltp`) for the
read/write "review cases" workflow. If the app service principal cannot
authenticate to Lakebase Postgres, we transparently fall back to a Delta table
(arjoon_ws_catalog.policylens_ml.app_review_cases) served via the SQL warehouse.

All data is SYNTHETIC; health plan referred to only as "EBCBS".
"""
import json
import uuid
import datetime as dt

import pandas as pd
import requests
from databricks.sdk.core import Config

import data as D

INSTANCE = "policylens-oltp"
PG_DB = "databricks_postgres"
PG_SCHEMA = "policylens"
FALLBACK_TABLE = f"{D.ML}.app_review_cases"

_cfg = Config()


# ------------------------------------------------------------------ Lakebase
def _pg_connect():
    import psycopg2
    from databricks.sdk import WorkspaceClient

    base = _cfg.host
    h = _cfg.authenticate()
    inst = requests.get(
        f"{base}/api/2.0/database/instances/{INSTANCE}", headers=h, timeout=15
    ).json()
    host = inst["read_write_dns"]
    cred = requests.post(
        f"{base}/api/2.0/database/credentials",
        headers=h,
        json={"instance_names": [INSTANCE], "request_id": str(uuid.uuid4())},
        timeout=15,
    ).json()
    token = cred["token"]
    user = WorkspaceClient().current_user.me().user_name
    return psycopg2.connect(
        host=host, port=5432, dbname=PG_DB, user=user,
        password=token, sslmode="require", connect_timeout=10,
    )


class ReviewStore:
    """Review-cases store with Lakebase primary and Delta fallback."""

    def __init__(self):
        self.mode = "lakebase"
        self.detail = ""
        try:
            conn = _pg_connect()
            conn.close()
        except Exception as e:  # noqa: BLE001
            self.mode = "delta"
            self.detail = str(e).splitlines()[0][:200]
            self._ensure_delta_table()

    # -- fallback table bootstrap --
    def _ensure_delta_table(self):
        D.execute(f"""
            CREATE TABLE IF NOT EXISTS {FALLBACK_TABLE} (
                case_id STRING, policy_id STRING, gap_type STRING, status STRING,
                assigned_analyst STRING, recommendation_json STRING,
                financial_impact_json STRING, created_at TIMESTAMP
            ) USING DELTA
        """)

    # -------- reads --------
    def list_cases(self) -> pd.DataFrame:
        if self.mode == "lakebase":
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT case_id, policy_id, gap_type, status, assigned_analyst,
                                   recommendation_json, financial_impact_json, created_at
                            FROM {PG_SCHEMA}.policy_review_cases
                            ORDER BY created_at DESC""")
                    cols = [c[0] for c in cur.description]
                    rows = cur.fetchall()
            finally:
                conn.close()
            return pd.DataFrame([list(r) for r in rows], columns=cols)
        # delta fallback
        return D.run_query(f"""
            SELECT case_id, policy_id, gap_type, status, assigned_analyst,
                   recommendation_json, financial_impact_json, created_at
            FROM {FALLBACK_TABLE}
            ORDER BY created_at DESC
        """)

    # -------- writes --------
    def create_case(self, policy_id, gap_type, assigned_analyst,
                    recommendation: dict, financial_impact: dict, status="open"):
        case_id = f"CASE-{policy_id}-{uuid.uuid4().hex[:6].upper()}"
        rec = json.dumps(recommendation)
        fin = json.dumps(financial_impact)
        if self.mode == "lakebase":
            conn = _pg_connect()
            try:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(
                        f"""INSERT INTO {PG_SCHEMA}.policy_review_cases
                            (case_id, policy_id, gap_type, status, assigned_analyst,
                             recommendation_json, financial_impact_json, created_at)
                            VALUES (%s,%s,%s,%s,%s,%s,%s, now())""",
                        (case_id, policy_id, gap_type, status, assigned_analyst, rec, fin),
                    )
            finally:
                conn.close()
        else:
            now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            def q(s):
                return "'" + str(s).replace("'", "''") + "'"
            D.execute(f"""
                INSERT INTO {FALLBACK_TABLE}
                (case_id, policy_id, gap_type, status, assigned_analyst,
                 recommendation_json, financial_impact_json, created_at)
                VALUES ({q(case_id)},{q(policy_id)},{q(gap_type)},{q(status)},
                        {q(assigned_analyst)},{q(rec)},{q(fin)}, TIMESTAMP {q(now)})
            """)
        return case_id
