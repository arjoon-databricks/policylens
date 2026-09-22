-- PolicyLens — Level-up C: payment-integrity UC function tools over the SAME gold/silver layer.
-- Proves the reusable pattern: a second agent's tools built on the existing governed tables.
-- All data synthetic; EBCBS is a code name. Payment-integrity = adjudication accuracy / admin efficiency
-- (reducing improper payments and rework) — not clinical decisions, not cost-savings framing.

-- Tool: prior-auth adjudication-friction outliers (high denial AND appeal => potential improper denials / rework)
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.pi_denial_appeal_outliers()
RETURNS TABLE(policy_id STRING, cpt_code STRING, pa_requests BIGINT, denial_rate DOUBLE,
              appeal_rate DOUBLE, friction_score DOUBLE)
COMMENT 'Top prior-auth adjudication-friction outliers: high denial AND appeal rates, signalling potential improper denials or avoidable rework.'
RETURN
  SELECT policy_id, cpt_code, COUNT(*) AS pa_requests,
         ROUND(AVG(CASE WHEN decision='denied' THEN 1 ELSE 0 END),4) AS denial_rate,
         ROUND(AVG(CASE WHEN appeal_flag THEN 1 ELSE 0 END),4) AS appeal_rate,
         ROUND(AVG(CASE WHEN decision='denied' THEN 1 ELSE 0 END)
             + AVG(CASE WHEN appeal_flag THEN 1 ELSE 0 END),4) AS friction_score
  FROM arjoon_ws_catalog.policylens_silver.silver_prior_auth
  GROUP BY policy_id, cpt_code HAVING COUNT(*) > 100
  ORDER BY friction_score DESC LIMIT 15;

-- Tool: CPT cost-per-procedure anomalies vs their category median (payment-accuracy review flags)
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.pi_cost_anomalies()
RETURNS TABLE(cpt_code STRING, description STRING, category STRING, avg_cost_per_procedure DOUBLE,
              category_median DOUBLE, cost_ratio DOUBLE, total_allowed DOUBLE)
COMMENT 'CPTs whose average cost per procedure most exceeds their category median — payment-accuracy review flags.'
RETURN
  WITH med AS (
    SELECT category, percentile_approx(avg_cost_per_procedure, 0.5) AS cat_med
    FROM arjoon_ws_catalog.policylens_gold.cpt_utilization_summary GROUP BY category)
  SELECT c.cpt_code, c.description, c.category, c.avg_cost_per_procedure,
         ROUND(m.cat_med,2) AS category_median,
         ROUND(c.avg_cost_per_procedure / NULLIF(m.cat_med,0),2) AS cost_ratio,
         c.total_allowed
  FROM arjoon_ws_catalog.policylens_gold.cpt_utilization_summary c
  JOIN med m USING (category)
  ORDER BY cost_ratio DESC LIMIT 15;
