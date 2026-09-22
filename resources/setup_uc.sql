-- PolicyLens (EBCBS) — Unity Catalog setup
-- Run via resources/dbsql.sh (SQL Statement Execution API). All data is synthetic.
--
-- NOTE: this workspace user lacks CREATE CATALOG on the metastore, so PolicyLens
-- lives in the existing workspace catalog `arjoon_ws_catalog` with policylens_* schemas
-- (medallion bronze/silver/gold + ml), instead of a dedicated `policylens_demo` catalog.

CREATE SCHEMA IF NOT EXISTS arjoon_ws_catalog.policylens_bronze
  COMMENT 'PolicyLens (EBCBS) synthetic demo — bronze (raw ingest). All data synthetic.';
CREATE SCHEMA IF NOT EXISTS arjoon_ws_catalog.policylens_silver
  COMMENT 'PolicyLens (EBCBS) synthetic demo — silver (cleaned/governed).';
CREATE SCHEMA IF NOT EXISTS arjoon_ws_catalog.policylens_gold
  COMMENT 'PolicyLens (EBCBS) synthetic demo — gold (features/marts).';
CREATE SCHEMA IF NOT EXISTS arjoon_ws_catalog.policylens_ml
  COMMENT 'PolicyLens (EBCBS) synthetic demo — ML models & scores.';

-- Raw landing zone for Auto Loader / Spark Declarative Pipelines.
CREATE VOLUME IF NOT EXISTS arjoon_ws_catalog.policylens_bronze.raw
  COMMENT 'Raw landing zone for Auto Loader / SDP ingestion';
