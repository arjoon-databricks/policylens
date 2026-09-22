# Level-up D — financial-impact model drift monitor

_Generated 2026-09-22 03:58 UTC — synthetic data; EBCBS is a code name._


## Windows

- **baseline_months**: 2023-01..2025-06 (30)
- **recent_months**: 2025-07..2025-12 (6)

## Feature drift (PSI)

- **procedure_count**: PSI=0.081 (stable)
- **avg_cost_per_procedure**: PSI=0.0045 (stable)
- **prior_auth_rate**: PSI=0.0579 (stable)
- **denial_rate**: PSI=0.0138 (stable)

## Prediction drift (MAPE)

- **baseline MAPE**: 0.0257
- **recent MAPE**: 0.0236
- **recent/baseline ratio**: 0.92 (stable)

## Decision

- **retrain_recommended**: False
- **action**: no retrain needed — model current
- **metrics_table**: arjoon_ws_catalog.policylens_ml.model_drift_metrics
| metric | subject | value | threshold | retrain_recommended |
| --- | --- | --- | --- | --- |
| feature_psi | procedure_count | 0.081 | 0.2 | False |
| feature_psi | avg_cost_per_procedure | 0.0045 | 0.2 | False |
| feature_psi | prior_auth_rate | 0.0579 | 0.2 | False |
| feature_psi | denial_rate | 0.0138 | 0.2 | False |
| prediction_mape_ratio | financial_impact_model | 0.92 | 1.5 | False |

## Monthly cadence (wired)
Scheduled Databricks Job **`policylens-monthly-drift-monitor`** (job_id 143951555848051) runs this
monitor on the 1st of each month (06:00 America/New_York, serverless). When `retrain_recommended`
is true it flags the financial-impact model for retraining, so the SHAP-driven story stays current
as new claim-months land. First run (this execution): **retrain=False — model stable**.
