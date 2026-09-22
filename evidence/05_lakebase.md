# Step 5 — Lakebase operational serving

_Generated 2026-09-21 21:59 UTC — synthetic data; EBCBS is a code name._

- **instance**: policylens-oltp
- **pg_version**: PG_VERSION_16
- **read_write_dns**: ep-falling-silence-d2mtzv14.database.us-east-1.cloud.databricks.com
- **database.schema**: databricks_postgres.policylens

## Read path (gold -> Postgres)

- **policy_comparison_current**: 18
- **cpt_utilization_current**: 58
- **policy_gap_alerts**: 5

## Write path (OLTP)

- **policy_review_cases seeded**: 5
- **recommendation_actions table**: created (empty, written by app)

## Sample serving read

- **gap alerts read latency**: 3 ms
- **rows**: 5
  - P-2024-CARD-01 | ambiguous_language | medium
  - P-2024-CARD-01 | more_restrictive | medium
  - P-2024-KNEE-01 | ambiguous_language | medium
  - P-2024-KNEE-01 | more_permissive | high
  - P-2024-SPINE-01 | more_restrictive | high