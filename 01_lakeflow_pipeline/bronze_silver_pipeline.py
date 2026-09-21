# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Step 2: Lakeflow Declarative Pipeline (bronze → silver)
# MAGIC
# MAGIC Spark Declarative Pipeline that ingests the raw Volume via **Auto Loader** and
# MAGIC builds the medallion with **data-quality expectations**. Published to
# MAGIC `arjoon_ws_catalog.policylens_silver` (layer prefixes `bronze_` / `silver_`).
# MAGIC
# MAGIC Lineage: `raw/ Volume`  →  `bronze_*` (typed ingest)  →  `silver_*` (curated + DQ).
# MAGIC All data synthetic; EBCBS is a code name.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

RAW = "/Volumes/arjoon_ws_catalog/policylens_bronze/raw"

# ---------------------------------------------------------------------------
# BRONZE — Auto Loader ingest of each raw source (parquet) as streaming tables
# ---------------------------------------------------------------------------
RAW_SOURCES = {
    "claims": "claims",
    "prior_auth": "prior_auth",
    "utilization": "utilization",
    "cpt": "cpt",
    "medical_policy": "policies",
    "competitor_policy": "competitor_policies",
}


def _make_bronze(subdir: str):
    def ingest():
        return (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .option("cloudFiles.inferColumnTypes", "true")
            .load(f"{RAW}/{subdir}/")
            .withColumn("_ingest_ts", F.current_timestamp())
            .withColumn("_source_file", F.col("_metadata.file_path"))
        )
    return ingest


for tbl, subdir in RAW_SOURCES.items():
    dlt.table(
        name=f"bronze_{tbl}",
        comment=f"Bronze: raw {tbl} ingested via Auto Loader from {RAW}/{subdir}/",
        table_properties={
            "quality": "bronze",
            "pipelines.reset.allowed": "true",
            # generated datetimes land as TIMESTAMP_NTZ -> enable the Delta feature
            "delta.feature.timestampNtz": "supported",
        },
    )(_make_bronze(subdir))


# ---------------------------------------------------------------------------
# SILVER — curated, typed, deduplicated, with DQ expectations
# ---------------------------------------------------------------------------
@dlt.table(name="silver_claims", comment="Silver: curated EBCBS claims", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_claim_id", "claim_id IS NOT NULL")
@dlt.expect_or_drop("nonneg_allowed", "allowed_amount >= 0")
@dlt.expect_or_drop("valid_service_date", "service_date >= '2022-01-01'")
@dlt.expect("paid_le_allowed", "paid_amount <= allowed_amount")
@dlt.expect("has_cpt", "cpt_code IS NOT NULL")
def silver_claims():
    return (
        dlt.read_stream("bronze_claims")
        .withColumn("service_date", F.col("service_date").cast("date"))
        .withColumn("allowed_amount", F.col("allowed_amount").cast("double"))
        .withColumn("paid_amount", F.col("paid_amount").cast("double"))
        .withColumn("member_cost_share", F.col("member_cost_share").cast("double"))
        .dropDuplicates(["claim_id"])
    )


@dlt.table(name="silver_prior_auth", comment="Silver: curated prior-auth requests", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_pa_id", "pa_id IS NOT NULL")
@dlt.expect_or_drop("valid_decision", "decision IN ('approved','denied','pending')")
@dlt.expect("decision_after_request", "decision_date IS NULL OR decision_date >= request_date")
def silver_prior_auth():
    return (
        dlt.read_stream("bronze_prior_auth")
        .withColumn("request_date", F.col("request_date").cast("date"))
        .withColumn("decision_date", F.col("decision_date").cast("date"))
        .withColumn("appeal_flag", F.col("appeal_flag").cast("boolean"))
        .dropDuplicates(["pa_id"])
    )


@dlt.table(name="silver_utilization", comment="Silver: CPT x month utilization", table_properties={"quality": "silver"})
@dlt.expect_or_drop("nonneg_count", "procedure_count >= 0")
@dlt.expect("rate_bounds", "prior_auth_rate BETWEEN 0 AND 1 AND denial_rate BETWEEN 0 AND 1")
def silver_utilization():
    return (
        dlt.read_stream("bronze_utilization")
        .withColumn("procedure_count", F.col("procedure_count").cast("long"))
        .withColumn("total_allowed", F.col("total_allowed").cast("double"))
        .withColumn("total_paid", F.col("total_paid").cast("double"))
    )


@dlt.table(name="silver_cpt_code", comment="Silver: CPT reference dimension", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_cpt", "cpt_code IS NOT NULL")
@dlt.expect("nonneg_cost", "avg_national_cost >= 0")
def silver_cpt_code():
    return dlt.read("bronze_cpt").dropDuplicates(["cpt_code"])


@dlt.table(name="silver_medical_policy", comment="Silver: medical policies (EBCBS + competitors)", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_policy_id", "policy_id IS NOT NULL")
@dlt.expect_or_drop("valid_payer", "payer IS NOT NULL")
def silver_medical_policy():
    return (
        dlt.read("bronze_medical_policy")
        .withColumn("prior_auth_required", F.col("prior_auth_required").cast("boolean"))
        .withColumn("effective_date", F.col("effective_date").cast("date"))
        .withColumn("expiration_date", F.col("expiration_date").cast("date"))
        .dropDuplicates(["policy_id"])
    )


@dlt.table(name="silver_competitor_policy", comment="Silver: competitor policy detail", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_competitor_id", "competitor_id IS NOT NULL")
@dlt.expect("score_bounds", "restrictiveness_score BETWEEN 0 AND 1")
def silver_competitor_policy():
    return dlt.read("bronze_competitor_policy").dropDuplicates(["competitor_id"])
