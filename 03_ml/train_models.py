# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Step 4: ML (financial-impact model + policy-gap classifier)
# MAGIC
# MAGIC Trains, evaluates, and registers two models (registry fallback noted below; batch scores land in UC `policylens_ml`):
# MAGIC 1. **financial_impact_model** — LightGBM regressor predicting monthly allowed $ for a CPT
# MAGIC    from its cost/category/utilization-management features (powers the financial simulator).
# MAGIC 2. **policy_gap_classifier** — multiclass model labeling each EBCBS-vs-competitor comparison
# MAGIC    as more_restrictive / less_restrictive / aligned.
# MAGIC
# MAGIC MLflow tracking; batch scores written to UC `policylens_ml`. (Model registration is
# MAGIC blocked by a metastore quota — see the note below — so models are logged, not registered.)
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------

# MAGIC %pip install lightgbm shap mlflow scikit-learn --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import numpy as np
import pandas as pd
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, f1_score, confusion_matrix
import lightgbm as lgb

# NOTE: this metastore is at its UC registered-model quota (5000) AND the legacy workspace
# registry is disabled, so models are LOGGED to MLflow (loadable via runs:/<id>/model) rather
# than registered. Batch scoring + the app/agent load models by run URI. See BUILD.md.
mlflow.set_experiment(f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/policylens_ml")
FIN_MODEL = "policylens_financial_impact_model"
GAP_MODEL = "policylens_policy_gap_classifier"

rep = EvidenceReport("04_ml", "Step 4 — ML: financial-impact model + gap classifier")

# COMMAND ----------

# MAGIC %md ## Model 1 — financial impact regressor (LightGBM)

# COMMAND ----------

util = spark.table(f"{CATALOG}.{SILVER}.silver_utilization").toPandas()
cpt = spark.table(f"{CATALOG}.{SILVER}.silver_cpt_code").toPandas()
df = util.merge(cpt, on="cpt_code", how="left")
df["month_index"] = df["year_month"].str.slice(0, 4).astype(int) * 12 + df["year_month"].str.slice(5, 7).astype(int)
df["month_index"] = df["month_index"] - df["month_index"].min()
df["month_of_year"] = df["year_month"].str.slice(5, 7).astype(int)

FEATURES_NUM = ["avg_national_cost", "cms_rvu", "prior_auth_rate", "denial_rate", "month_index", "month_of_year"]
cat_dummies = pd.get_dummies(df["category"], prefix="cat")
X = pd.concat([df[FEATURES_NUM], cat_dummies], axis=1)
FEAT_COLS = list(X.columns)
y = np.log1p(df["total_allowed"].astype(float))

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

with mlflow.start_run(run_name="financial_impact_model") as run:
    params = dict(n_estimators=400, learning_rate=0.05, num_leaves=31, max_depth=-1,
                  subsample=0.8, colsample_bytree=0.8, random_state=42)
    mlflow.log_params(params)
    reg = lgb.LGBMRegressor(**params)
    reg.fit(X_tr, y_tr)

    pred_log = reg.predict(X_te)
    pred = np.expm1(pred_log)
    actual = np.expm1(y_te)
    mae = mean_absolute_error(actual, pred)
    mape = float(np.mean(np.abs((actual - pred) / np.clip(actual, 1, None))))
    r2 = r2_score(y_te, pred_log)
    mlflow.log_metrics({"mae_dollars": mae, "mape": mape, "r2_log": r2})

    sig = infer_signature(X_tr, reg.predict(X_tr))
    mlflow.lightgbm.log_model(reg, "model", signature=sig, input_example=X_tr.head(3))

    # feature importance (gain) + SHAP if available
    imp = pd.DataFrame({"feature": FEAT_COLS, "gain": reg.booster_.feature_importance("gain")}
                       ).sort_values("gain", ascending=False).head(8)
    try:
        import shap
        expl = shap.TreeExplainer(reg)
        sv = np.abs(expl.shap_values(X_te.sample(min(300, len(X_te)), random_state=1))).mean(0)
        shap_imp = pd.DataFrame({"feature": FEAT_COLS, "mean_abs_shap": sv}).sort_values("mean_abs_shap", ascending=False).head(8)
        shap_ok = True
    except Exception as e:
        shap_ok = False
        shap_note = str(e)[:120]

fin_run_id = run.info.run_id
rep.h("Model 1 — financial_impact_model (LightGBM regressor)")
rep.kv("train/test rows", f"{len(X_tr)}/{len(X_te)}").kv("features", len(FEAT_COLS))
rep.kv("MAE ($ monthly allowed)", f"{mae:,.0f}").kv("MAPE", f"{mape:.3f}").kv("R2 (log)", f"{r2:.3f}")
rep.kv("logged model uri", f"runs:/{fin_run_id}/model").kv("run_id", fin_run_id)
rep.line("Top gain features:")
rep.table(imp)
if shap_ok:
    rep.line("Top SHAP features:")
    rep.table(shap_imp)
else:
    rep.kv("shap", f"skipped ({shap_note})")

# COMMAND ----------

# MAGIC %md ## Model 2 — policy gap classifier (EBCBS vs each competitor)

# COMMAND ----------

pol = spark.table(f"{CATALOG}.{SILVER}.silver_medical_policy").toPandas()
comp = spark.table(f"{CATALOG}.{SILVER}.silver_competitor_policy").toPandas()
pcf = spark.table(f"{CATALOG}.{GOLD}.policy_comparison_features").toPandas()

import re
def topic_of(pid):
    m = re.match(r"^P-2024-(.+)-[^-]+$", pid); return m.group(1) if m else pid

pol["topic"] = pol["policy_id"].map(topic_of)
comp["topic"] = comp["competitor_id"].map(topic_of)
ebcbs = pol[pol.payer == "EBCBS"].set_index("topic")
pcf["topic"] = pcf["policy_id"].map(topic_of)
pcf_idx = pcf.set_index("topic")

rows = []
for _, cr in comp.iterrows():
    t = cr["topic"]
    if t not in ebcbs.index:
        continue
    e = ebcbs.loc[t]
    ecov = set(e["cpt_codes_covered"]); ccov = set(cr["cpt_codes_covered"])
    coverage_delta = len(ecov) - len(ccov)
    n_exclusive = len(ecov - ccov)
    pa_req = 1 if bool(e["prior_auth_required"]) else 0
    denial = float(pcf_idx.loc[t, "denial_rate"]) if t in pcf_idx.index else 0.0
    crest = float(cr["restrictiveness_score"])
    # rule-derived 3-class label
    ebcbs_score = denial + 0.15 * pa_req - 0.02 * n_exclusive
    diff = ebcbs_score - crest
    label = "aligned"
    if diff < -0.15: label = "less_restrictive"
    elif diff > 0.15: label = "more_restrictive"
    rows.append(dict(topic=t, ebcbs_policy=e["policy_id"], competitor=cr["competitor_id"],
                     coverage_delta=coverage_delta, n_exclusive=n_exclusive, pa_required=pa_req,
                     ebcbs_denial_rate=denial, competitor_restrictiveness=crest, label=label))

gdf = pd.DataFrame(rows)
GAP_FEATS = ["coverage_delta", "n_exclusive", "pa_required", "ebcbs_denial_rate", "competitor_restrictiveness"]
classes = sorted(gdf["label"].unique())
cls_map = {c: i for i, c in enumerate(classes)}
Xg = gdf[GAP_FEATS]; yg = gdf["label"].map(cls_map)
Xg_tr, Xg_te, yg_tr, yg_te = train_test_split(Xg, yg, test_size=0.25, random_state=42)

with mlflow.start_run(run_name="policy_gap_classifier") as run2:
    clf = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1, num_leaves=15, random_state=42)
    clf.fit(Xg_tr, yg_tr)
    pg = clf.predict(Xg_te)
    acc = accuracy_score(yg_te, pg)
    f1 = f1_score(yg_te, pg, average="weighted")
    mlflow.log_params({"classes": ",".join(classes)})
    mlflow.log_metrics({"accuracy": acc, "f1_weighted": f1})
    sig2 = infer_signature(Xg_tr, clf.predict(Xg_tr))
    mlflow.lightgbm.log_model(clf, "model", signature=sig2, input_example=Xg_tr.head(3))

gap_run_id = run2.info.run_id
rep.h("Model 2 — policy_gap_classifier (LightGBM multiclass)")
rep.kv("comparison rows (EBCBS x competitor)", len(gdf)).kv("classes", ", ".join(classes))
rep.kv("label distribution", gdf["label"].value_counts().to_dict())
rep.kv("accuracy", f"{acc:.3f}").kv("f1_weighted", f"{f1:.3f}")
rep.kv("logged model uri", f"runs:/{gap_run_id}/model")

# COMMAND ----------

# MAGIC %md ## Batch scoring — financial impact predictions per CPT × month

# COMMAND ----------

df["predicted_allowed"] = np.expm1(reg.predict(X))
scored = df[["cpt_code", "year_month", "category", "total_allowed", "predicted_allowed"]].copy()
scored = scored.rename(columns={"total_allowed": "actual_allowed"})
scored["predicted_allowed"] = scored["predicted_allowed"].round(2)
sdf = spark.createDataFrame(scored)
sdf.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{CATALOG}.{ML}.financial_impact_predictions")

# per-policy annual predicted spend (feeds the simulator)
spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{ML}.policy_cpt_predicted_annual AS
SELECT p.policy_id, s.cpt_code,
       ROUND(SUM(s.predicted_allowed) / 3.0, 2) AS predicted_annual_allowed,
       ROUND(SUM(s.actual_allowed) / 3.0, 2)    AS actual_annual_allowed
FROM {CATALOG}.{ML}.financial_impact_predictions s
JOIN (SELECT policy_id, explode(cpt_codes_covered) cpt_code
      FROM {CATALOG}.{SILVER}.silver_medical_policy WHERE payer='EBCBS') p
  ON s.cpt_code = p.cpt_code
GROUP BY p.policy_id, s.cpt_code
""")

n_pred = spark.table(f"{CATALOG}.{ML}.financial_impact_predictions").count()
rep.h("Batch scoring")
rep.kv("financial_impact_predictions rows", f"{n_pred:,}")
rep.kv("policy_cpt_predicted_annual rows", spark.table(f"{CATALOG}.{ML}.policy_cpt_predicted_annual").count())
samp = spark.sql(f"SELECT cpt_code, year_month, actual_allowed, predicted_allowed FROM {CATALOG}.{ML}.financial_impact_predictions ORDER BY actual_allowed DESC LIMIT 6").toPandas()
rep.table(samp)

path = rep.save()
dbutils.notebook.exit(f"STEP4_OK fin_mae={mae:.0f} fin_r2={r2:.3f} clf_acc={acc:.3f} fin_run={fin_run_id} gap_run={gap_run_id} evidence={path}")
