# Step 1 — Synthetic Data Generation (EBCBS)

_Generated 2026-09-21 21:04 UTC — synthetic data; EBCBS is a code name._

- **seed**: 42
- **months**: 2023-01..2025-12 (36)
- **target_claims**: 2,000,000
- **members_pool**: 250,000
- **providers_pool**: 6,000

## dim_cpt_code

- **rows**: 58
- **categories**: diagnostic, evaluation_management, laboratory, pharmaceutical, surgical, therapeutic
| cpt_code | description | category | subcategory | avg_national_cost | cms_rvu |
| --- | --- | --- | --- | --- | --- |
| 29880 | Arthroscopy knee, meniscectomy medial AND lateral | surgical | orthopedic | 5200.0 | 102.32 |
| 29881 | Arthroscopy knee, meniscectomy medial OR lateral | surgical | orthopedic | 4800.0 | 85.67 |
| 29882 | Arthroscopy knee, meniscus repair | surgical | orthopedic | 6100.0 | 122.84 |
| 29883 | Arthroscopy knee, meniscus repair medial AND lateral | surgical | orthopedic | 7300.0 | 140.59 |
| 29866 | Arthroscopy knee, osteochondral autograft | surgical | orthopedic | 8900.0 | 142.12 |
| 29867 | Arthroscopy knee, osteochondral allograft | surgical | orthopedic | 9600.0 | 199.45 |


## dim_medical_policy

- **rows**: 90
- **topics**: 18
- **payers**: 5

## dim_competitor_policy

- **rows**: 72
- **ebcbs_pa_required_cpts**: 27

## fact_claims

- **rows_written**: 1,994,425
- **monthly_files**: 36
- **path**: /Volumes/arjoon_ws_catalog/policylens_bronze/raw/claims/claims_YYYY-MM.parquet

## fact_prior_auth

- **rows**: 40,000
- **approved**: 30939
- **denied**: 7080
- **pending**: 1981
- **appeals**: 2313

## fact_utilization

- **rows**: 2,088
- **grain**: cpt_code × year_month

## GAP 1 — Knee arthroscopy (overly permissive)

- **EBCBS knee CPTs covered**: 8
- **CPTs excluded by >=3 of 4 competitors**: 29883(3/4), 29866(3/4), 29867(3/4), 29868(3/4), 29882(2/4)
- **avg knee PA denial rate**: 0.000  (low → permissive)

## GAP 2 — Spinal fusion (overly restrictive)

- **spine denial rate**: 0.323
- **baseline denial rate**: 0.110
- **spine appeal rate (of denials)**: 0.583

## GAP 3 — Cardiac imaging (ambiguous → regional variance)

| region | denial_rate |
| --- | --- |
| Central NY | 0.37 |
| Finger Lakes | 0.136 |
| Rochester | 0.098 |
| Southern Tier | 0.209 |
| Utica-Mohawk | 0.384 |

- **regional denial-rate spread**: 0.286  (high → inconsistent)

## Raw landing summary

- **volume_root**: /Volumes/arjoon_ws_catalog/policylens_bronze/raw
- **cpt**: 1 file(s)
- **policies**: 1 file(s)
- **competitor_policies**: 1 file(s)
- **claims**: 36 file(s)
- **prior_auth**: 1 file(s)
- **utilization**: 1 file(s)