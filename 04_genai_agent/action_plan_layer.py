# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Level-up B: NL action-plan layer (SHAP-grounded recommendation memos)
# MAGIC
# MAGIC Turns each gold `policy_gap_alerts` row into an analyst-ready recommendation memo, grounded in
# MAGIC the policy's comparison features **and the financial-impact model's per-policy SHAP drivers**,
# MAGIC drafted by Claude via the governed Unity Gateway model service, and logged to an auditable
# MAGIC inference table `arjoon_ws_catalog.policylens_ml.gap_action_plans`.
# MAGIC All data synthetic; EBCBS is a code name. Policy administration only — no clinical/cost-based advice.

# COMMAND ----------

# MAGIC %pip install mlflow lightgbm shap openai --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import json, datetime
import numpy as np, pandas as pd, mlflow
from openai import OpenAI

rep = EvidenceReport("10_action_plan", "Level-up B — SHAP-grounded action-plan memos")

# --- load the financial-impact model (logged in Step 4) + rebuild its features for SHAP ---
FIN_RUN_ID = "fbff52c30ec748758313ec624e46fbe9"
reg = mlflow.lightgbm.load_model(f"runs:/{FIN_RUN_ID}/model")
feat_order = list(reg.booster_.feature_name())

util = spark.table(f"{CATALOG}.{SILVER}.silver_utilization").toPandas()
cpt = spark.table(f"{CATALOG}.{SILVER}.silver_cpt_code").toPandas()
df = util.merge(cpt, on="cpt_code", how="left")
df["month_index"] = df["year_month"].str.slice(0,4).astype(int)*12 + df["year_month"].str.slice(5,7).astype(int)
df["month_index"] = df["month_index"] - df["month_index"].min()
df["month_of_year"] = df["year_month"].str.slice(5,7).astype(int)
FEATURES_NUM = ["avg_national_cost","cms_rvu","prior_auth_rate","denial_rate","month_index","month_of_year"]
X = pd.concat([df[FEATURES_NUM], pd.get_dummies(df["category"], prefix="cat")], axis=1)
for c in feat_order:            # align to the model's training feature order
    if c not in X.columns: X[c] = 0
X = X[feat_order]

import shap
explainer = shap.TreeExplainer(reg)
shap_vals = explainer.shap_values(X)                      # (rows, features)
shap_df = pd.DataFrame(shap_vals, columns=feat_order)
shap_df["cpt_code"] = df["cpt_code"].values

# EBCBS policy -> its covered CPTs (for per-policy SHAP aggregation)
pol = spark.table(f"{CATALOG}.{SILVER}.silver_medical_policy").toPandas()
ebcbs = pol[pol.payer == "EBCBS"]
policy_cpts = {r.policy_id: list(r.cpt_codes_covered) for r in ebcbs.itertuples()}

def top_shap_drivers(policy_id, k=3):
    cpts = policy_cpts.get(policy_id, [])
    sub = shap_df[shap_df.cpt_code.isin(cpts)]
    if sub.empty: return []
    imp = sub[feat_order].abs().mean().sort_values(ascending=False).head(k)
    return [(f, round(float(v), 3)) for f, v in imp.items()]

rep.h("Setup").kv("model_run", FIN_RUN_ID).kv("features", len(feat_order)).kv("shap_rows", len(shap_df))

# COMMAND ----------

# MAGIC %md ## Draft memos via the governed Unity Gateway model service

# COMMAND ----------

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
DBX_HOST = ctx.apiUrl().get(); DBX_TOKEN = ctx.apiToken().get()
client = OpenAI(api_key=DBX_TOKEN, base_url=f"{DBX_HOST}/ai-gateway/mlflow/v1")
MODEL_SVC = f"{CATALOG}.{ML}.policylens_copilot"

alerts = spark.table(f"{CATALOG}.{GOLD}.policy_gap_alerts").toPandas()
pcf = spark.table(f"{CATALOG}.{GOLD}.policy_comparison_features").toPandas().set_index("policy_id")

SYSTEM = ("You are the PolicyLens policy-administration analyst assistant for EBCBS (a health plan). "
          "Write a concise, analyst-ready recommendation memo for a medical-policy gap, grounded ONLY in the "
          "provided data. Advise on policy ADMINISTRATION (coverage competitiveness, utilization-management "
          "levers, documentation), never clinical/individual-patient decisions, and never frame value as cost "
          "savings. Structure: **Finding**, **Evidence** (cite the metrics + SHAP drivers), **Recommended action**, "
          "**Financial context** (budget exposure, not savings), **Caveat**. <=180 words.")

rows = []
for a in alerts.itertuples():
    pid = a.policy_id
    feats = pcf.loc[pid].to_dict() if pid in pcf.index else {}
    drivers = top_shap_drivers(pid)
    user = json.dumps({
        "policy_id": pid, "policy_name": a.policy_name, "gap_type": a.gap_type, "severity": a.severity,
        "gap_description": a.description,
        "comparison_features": {k: feats.get(k) for k in
            ["prior_auth_required","n_exclusive_cpts","denial_rate","appeal_rate",
             "avg_competitor_restrictiveness","total_allowed"]},
        "financial_model_shap_drivers": drivers,
    }, default=str)
    r = client.chat.completions.create(model=MODEL_SVC, max_tokens=700,
        messages=[{"role":"system","content":SYSTEM},{"role":"user","content":user}])
    memo = r.choices[0].message.content
    rows.append({
        "policy_id": pid, "policy_name": a.policy_name, "gap_type": a.gap_type, "severity": a.severity,
        "shap_drivers": json.dumps(drivers), "inputs_json": user, "memo_text": memo,
        "model_run_id": FIN_RUN_ID, "llm_model_service": MODEL_SVC,
        "generated_at": datetime.datetime.utcnow().isoformat(),
    })

memos = pd.DataFrame(rows)

# COMMAND ----------

# MAGIC %md ## Log to the auditable inference table + show samples

# COMMAND ----------

sdf = spark.createDataFrame(memos)
sdf.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable(
    f"{CATALOG}.{ML}.gap_action_plans")
n = spark.table(f"{CATALOG}.{ML}.gap_action_plans").count()

rep.h("Action-plan inference table").kv("table", f"{CATALOG}.{ML}.gap_action_plans").kv("memos", n)
rep.kv("also audit-logged via gateway", f"{CATALOG}.{ML}.policylens_copilot_payload")
for m in rows:
    rep.h(f"Memo — {m['policy_id']} ({m['gap_type']}, {m['severity']})")
    rep.kv("SHAP drivers", m["shap_drivers"])
    rep.line(m["memo_text"][:1400])

path = rep.save()
dbutils.notebook.exit(f"STEP_B_OK memos={n} table={CATALOG}.{ML}.gap_action_plans evidence={path}")
