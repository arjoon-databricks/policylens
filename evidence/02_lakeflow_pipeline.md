# Step 2 — Lakeflow Declarative Pipeline + Unity Catalog Governance

_Synthetic data; EBCBS is a code name. Executed on `fevm-arjoon-ws` (serverless)._

## Lakeflow Declarative Pipeline

- **Pipeline**: `policylens-medallion` (id `ae2a1555-e03c-45ec-aa34-dcc66e2c4ab8`), serverless, Photon, UC-enabled
- **Source**: `01_lakeflow_pipeline/bronze_silver_pipeline.py`
- **Ingest**: Auto Loader (`cloudFiles`, parquet) from `/Volumes/arjoon_ws_catalog/policylens_bronze/raw/`
- **Final update state**: **COMPLETED** (full refresh)
- **Lineage**: captured automatically by Unity Catalog — `raw/ Volume → bronze_* → silver_*`

### Tables produced (`arjoon_ws_catalog.policylens_silver`)

| Table | Layer | Rows |
| --- | --- | --- |
| bronze_claims | bronze | 1,994,425 |
| bronze_prior_auth | bronze | 40,000 |
| bronze_utilization | bronze | 2,088 |
| bronze_cpt | bronze | 58 |
| bronze_medical_policy | bronze | 90 |
| bronze_competitor_policy | bronze | 72 |
| silver_claims | silver | 1,994,425 |
| silver_prior_auth | silver | 40,000 |
| silver_utilization | silver | 2,088 |
| silver_cpt_code | silver | 58 |
| silver_medical_policy | silver | 90 |
| silver_competitor_policy | silver | 72 |

Silver counts equal bronze — no rows dropped (synthetic data satisfies all `expect_or_drop` gates).

### Data-quality expectations enforced (silver)

| Table | Expectation | Rule | Action |
| --- | --- | --- | --- |
| silver_claims | valid_claim_id | `claim_id IS NOT NULL` | drop |
| silver_claims | nonneg_allowed | `allowed_amount >= 0` | drop |
| silver_claims | valid_service_date | `service_date >= '2022-01-01'` | drop |
| silver_claims | paid_le_allowed | `paid_amount <= allowed_amount` | warn |
| silver_prior_auth | valid_decision | `decision IN (approved,denied,pending)` | drop |
| silver_prior_auth | decision_after_request | `decision_date IS NULL OR decision_date >= request_date` | warn |
| silver_utilization | rate_bounds | `prior_auth_rate/denial_rate BETWEEN 0 AND 1` | warn |
| silver_medical_policy | valid_policy_id / valid_payer | not-null keys | drop |
| silver_competitor_policy | score_bounds | `restrictiveness_score BETWEEN 0 AND 1` | warn |

## Unity Catalog governance (`02_unity_catalog/governance.sql`)

- **Column mask** `mask_member_id` applied to `silver_claims.member_id` and `silver_prior_auth.member_id`.
  Verified — non-privileged reads return redacted ids:

  | member_id | cpt_code | region |
  | --- | --- | --- |
  | M****98 | 99213 | Central NY |
  | M****61 | 84443 | Southern Tier |
  | M****00 | 70553 | Rochester |

- **Row filter** `claims_region_filter` on `silver_claims(region)` — RLS restricting `policylens_restricted`
  group members to their region; owner sees all (verified: 5 regions, 1,994,425 rows).
- **Tags**: `member_id` tagged `classification = confidential` (metastore enforces a tag-governance
  policy — `pii` and other keys reject non-allowlisted values, which we surfaced and complied with).

## Seeded gaps survive into silver (governed layer)

| Metric | Value |
| --- | --- |
| Spine PA denial rate | 0.323 |
| Baseline PA denial rate | 0.110 |
| Cardiac denial rate — Rochester | 0.098 |
| Cardiac denial rate — Utica-Mohawk | 0.384 |
| Cardiac regional spread | 0.286 |
