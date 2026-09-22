# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Level-up A (step 1): register the financial-impact model in UC
# MAGIC Tests whether the metastore's registered-model quota has been freed, and if so
# MAGIC registers the model logged earlier (by run id) so it can be served.
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------

# MAGIC %pip install mlflow --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import mlflow
mlflow.set_registry_uri("databricks-uc")

FIN_RUN_ID = "fbff52c30ec748758313ec624e46fbe9"  # from Step 4 evidence (evidence/04_ml.md)
NAME = f"{CATALOG}.{ML}.financial_impact_model"

# Fall back to discovering the latest financial_impact_model run if the id is stale.
model_uri = f"runs:/{FIN_RUN_ID}/model"
try:
    mlflow.artifacts.list_artifacts(run_id=FIN_RUN_ID)
except Exception as e:
    print("known run id not usable, searching experiment:", str(e)[:150])
    exp = mlflow.set_experiment(f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/policylens_ml")
    runs = mlflow.search_runs(experiment_ids=[exp.experiment_id],
                              filter_string="attributes.run_name = 'financial_impact_model'",
                              order_by=["start_time DESC"], max_results=1)
    FIN_RUN_ID = runs.iloc[0]["run_id"]
    model_uri = f"runs:/{FIN_RUN_ID}/model"
    print("using discovered run:", FIN_RUN_ID)

try:
    mv = mlflow.register_model(model_uri, NAME)
    result = f"REGISTERED name={NAME} version={mv.version} run={FIN_RUN_ID}"
except Exception as e:
    result = "REGISTER_FAILED " + str(e).splitlines()[0][:260]

print(result)
dbutils.notebook.exit(result)
