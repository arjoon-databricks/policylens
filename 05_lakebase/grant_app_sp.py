# Databricks notebook source
# MAGIC %md
# MAGIC # Grant the PolicyLens app service principal privileges on the Lakebase `policylens` schema
# MAGIC One-time admin utility. Connects to Lakebase `policylens-oltp` as the current user
# MAGIC (schema owner) and grants read/write to the app SP's auto-provisioned Postgres role.
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------
# MAGIC %pip install psycopg2-binary --quiet
# MAGIC %restart_python

# COMMAND ----------
import uuid, requests, psycopg2
from databricks.sdk import WorkspaceClient

INSTANCE = "policylens-oltp"
PG_DB = "databricks_postgres"
SCHEMA = "policylens"
SP_CLIENT_ID = "ea440edc-9f62-4670-8d34-d234330093da"  # app-29e86p policylens-command-center

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
HOST = ctx.apiUrl().get(); TOKEN = ctx.apiToken().get(); H = {"Authorization": f"Bearer {TOKEN}"}
inst = requests.get(f"{HOST}/api/2.0/database/instances/{INSTANCE}", headers=H).json()
host = inst["read_write_dns"]
cred = requests.post(f"{HOST}/api/2.0/database/credentials", headers=H,
                     json={"instance_names": [INSTANCE], "request_id": str(uuid.uuid4())}).json()
token = cred["token"]
user = WorkspaceClient().current_user.me().user_name

conn = psycopg2.connect(host=host, port=5432, dbname=PG_DB, user=user,
                        password=token, sslmode="require")
conn.autocommit = True
cur = conn.cursor()

# Discover the SP's Postgres role
cur.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg\\_%' ORDER BY rolname")
roles = [r[0] for r in cur.fetchall()]
print("Non-system roles:", roles)
target = next((r for r in roles if SP_CLIENT_ID in r), SP_CLIENT_ID)
print("Target SP role:", target)

def g(sql):
    try:
        cur.execute(sql); print("OK  :", sql)
    except Exception as e:  # noqa: BLE001
        print("ERR :", sql, "->", str(e).splitlines()[0])

g(f'GRANT USAGE ON SCHEMA {SCHEMA} TO "{target}"')
g(f'GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO "{target}"')
g(f'GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {SCHEMA} TO "{target}"')
g(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {SCHEMA} TO "{target}"')
g(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} '
  f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{target}"')

cur.execute(f"SELECT count(*) FROM {SCHEMA}.policy_review_cases")
print("policy_review_cases rows:", cur.fetchone()[0])
cur.close(); conn.close()
dbutils.notebook.exit(f"GRANTS_DONE target={target} roles={len(roles)}")
