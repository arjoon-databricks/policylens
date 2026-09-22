# Step 3 — Gold Feature Tables

_Synthetic data; EBCBS is a code name. Built from silver via `02_unity_catalog/gold_features.sql`._

## Tables (`arjoon_ws_catalog.policylens_gold`)

| Table | Rows | Grain / purpose |
| --- | --- | --- |
| cpt_utilization_summary | 58 | per-CPT rollup (procedures, cost, PA & denial rates) |
| policy_comparison_features | 18 | one row / EBCBS policy — coverage vs competitors, denial/appeal, restrictiveness (feeds gap classifier + comparison view) |
| financial_impact_scenarios | 41 | annualized baseline per EBCBS policy CPT (feeds financial simulator + ML) |
| policy_gap_alerts | 5 | rule-based gap detection (feeds app + agent) |

## Gap detection surfaced all 3 seeded gaps

| policy_id | gap_type | severity | metric |
| --- | --- | --- | --- |
| P-2024-KNEE-01 | more_permissive | high | 4 exclusive CPTs |
| P-2024-KNEE-01 | ambiguous_language | medium | — |
| P-2024-SPINE-01 | more_restrictive | high | 0.323 denial |
| P-2024-CARD-01 | more_restrictive | medium | 0.226 denial |
| P-2024-CARD-01 | ambiguous_language | medium | — |

## Comparison features for the 3 gap policies

| policy_id | pa_req | ebcbs_cpts | exclusive | denial_rate | appeal_rate | competitor_restrictiveness | total_procedures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P-2024-KNEE-01 | false | 8 | 4 | 0.000 | 0.000 | 0.803 | 228,177 |
| P-2024-SPINE-01 | true | 6 | 0 | 0.323 | 0.189 | 0.392 | 51,336 |
| P-2024-CARD-01 | true | 8 | 0 | 0.226 | 0.059 | 0.600 | 142,974 |

Reads exactly as designed: **knee** — EBCBS covers 4 CPTs competitors exclude, no prior auth, while
competitors are far more restrictive (0.80) → permissive. **Spine** — EBCBS denies 32% with 19% appeals
while competitors are looser (0.39) → restrictive. **Cardiac** — ambiguous criteria + mid denial.
