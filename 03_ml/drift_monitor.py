# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Level-up D: financial-impact model drift monitor
# MAGIC
# MAGIC Runs monthly (see the scheduled job). As new claim-months land it checks:
# MAGIC - **Feature drift** — PSI of recent vs baseline window for key utilization features
# MAGIC - **Prediction drift** — batch-prediction MAPE trend (recent vs baseline)
# MAGIC and logs metrics to `arjoon_ws_catalog.policylens_ml.model_drift_metrics` with a
# MAGIC `retrain_recommended` flag, so the SHAP-driven story stays current.
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import datetime
import numpy as np, pandas as pd

RECENT_MONTHS = 6
PSI_THRESHOLD = 0.20          # >0.2 = moderate population shift
MAPE_RATIO_THRESHOLD = 1.5    # recent MAPE > 1.5x baseline => degradation

rep = EvidenceReport("11_drift_monitor", "Level-up D — financial-impact model drift monitor")

util = spark.table(f"{CATALOG}.{SILVER}.silver_utilization").toPandas()
preds = spark.table(f"{CATALOG}.{ML}.financial_impact_predictions").toPandas()

months = sorted(util["year_month"].unique())
recent = set(months[-RECENT_MONTHS:]); baseline = set(months[:-RECENT_MONTHS])
rep.h("Windows").kv("baseline_months", f"{months[0]}..{months[-RECENT_MONTHS-1]} ({len(baseline)})")
rep.kv("recent_months", f"{months[-RECENT_MONTHS]}..{months[-1]} ({len(recent)})")

def psi(base, rec, bins=10):
    base, rec = np.asarray(base, float), np.asarray(rec, float)
    q = np.quantile(base, np.linspace(0, 1, bins + 1)); q[0], q[-1] = -np.inf, np.inf
    b = np.clip(np.histogram(base, q)[0] / max(len(base), 1), 1e-4, None)
    r = np.clip(np.histogram(rec, q)[0] / max(len(rec), 1), 1e-4, None)
    return float(np.sum((r - b) * np.log(r / b)))

# COMMAND ----------

# MAGIC %md ## Feature drift (PSI) + prediction-error drift (MAPE)

# COMMAND ----------

now = datetime.datetime.utcnow().isoformat()
rows = []
FEATURES = ["procedure_count", "avg_cost_per_procedure", "prior_auth_rate", "denial_rate"]
rep.h("Feature drift (PSI)")
for f in FEATURES:
    b = util[util.year_month.isin(baseline)][f]; r = util[util.year_month.isin(recent)][f]
    val = round(psi(b, r), 4); flag = val > PSI_THRESHOLD
    rows.append(dict(metric="feature_psi", subject=f, value=val, threshold=PSI_THRESHOLD,
                     retrain_recommended=flag, window=f"recent{RECENT_MONTHS}", checked_at=now))
    rep.kv(f, f"PSI={val} ({'DRIFT' if flag else 'stable'})")

# prediction error (MAPE) per month, recent vs baseline
preds = preds[preds.actual_allowed > 0].copy()
preds["ape"] = (preds.actual_allowed - preds.predicted_allowed).abs() / preds.actual_allowed
mape_by_month = preds.groupby("year_month")["ape"].mean()
base_mape = float(mape_by_month[mape_by_month.index.isin(baseline)].mean())
rec_mape = float(mape_by_month[mape_by_month.index.isin(recent)].mean())
ratio = round(rec_mape / base_mape, 3) if base_mape else 0.0
mape_flag = ratio > MAPE_RATIO_THRESHOLD
rows.append(dict(metric="prediction_mape_ratio", subject="financial_impact_model",
                 value=ratio, threshold=MAPE_RATIO_THRESHOLD, retrain_recommended=mape_flag,
                 window=f"recent{RECENT_MONTHS}", checked_at=now))
rep.h("Prediction drift (MAPE)")
rep.kv("baseline MAPE", round(base_mape, 4)).kv("recent MAPE", round(rec_mape, 4))
rep.kv("recent/baseline ratio", f"{ratio} ({'DEGRADED' if mape_flag else 'stable'})")

# COMMAND ----------

# MAGIC %md ## Log metrics + overall retrain decision

# COMMAND ----------

metrics = pd.DataFrame(rows)
retrain = bool(metrics["retrain_recommended"].any())
metrics["run_retrain_recommended"] = retrain
spark.createDataFrame(metrics).write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(
    f"{CATALOG}.{ML}.model_drift_metrics")

rep.h("Decision")
rep.kv("retrain_recommended", retrain)
rep.kv("action", "trigger monthly retraining job" if retrain else "no retrain needed — model current")
rep.kv("metrics_table", f"{CATALOG}.{ML}.model_drift_metrics")
rep.table(metrics[["metric", "subject", "value", "threshold", "retrain_recommended"]])

path = rep.save()
dbutils.notebook.exit(f"STEP_D_OK retrain={retrain} metrics_logged={len(metrics)} evidence={path}")
