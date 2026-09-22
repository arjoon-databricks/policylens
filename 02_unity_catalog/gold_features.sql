-- PolicyLens — Step 3: Gold feature tables (arjoon_ws_catalog.policylens_gold)
-- Built from the governed silver layer. UC captures table-level lineage silver -> gold.
-- All data synthetic; EBCBS is a code name.

-- ============================================================================
-- 1) cpt_utilization_summary — per-CPT rollup across all months
-- ============================================================================
CREATE OR REPLACE TABLE arjoon_ws_catalog.policylens_gold.cpt_utilization_summary AS
SELECT
  u.cpt_code, c.description, c.category, c.avg_national_cost,
  SUM(u.procedure_count)                                   AS total_procedures,
  ROUND(SUM(u.total_allowed), 2)                           AS total_allowed,
  ROUND(SUM(u.total_paid), 2)                              AS total_paid,
  ROUND(SUM(u.total_allowed) / NULLIF(SUM(u.procedure_count), 0), 2) AS avg_cost_per_procedure,
  ROUND(AVG(u.prior_auth_rate), 4)                         AS avg_prior_auth_rate,
  ROUND(AVG(u.denial_rate), 4)                             AS avg_denial_rate,
  COUNT(DISTINCT u.year_month)                             AS months_active
FROM arjoon_ws_catalog.policylens_silver.silver_utilization u
JOIN arjoon_ws_catalog.policylens_silver.silver_cpt_code c USING (cpt_code)
GROUP BY u.cpt_code, c.description, c.category, c.avg_national_cost;

-- ============================================================================
-- 2) policy_comparison_features — EBCBS policy vs competitors (one row / EBCBS policy)
-- ============================================================================
CREATE OR REPLACE TABLE arjoon_ws_catalog.policylens_gold.policy_comparison_features AS
WITH pol AS (
  SELECT policy_id, policy_name, policy_category, payer, cpt_codes_covered,
         prior_auth_required, criteria_text,
         regexp_extract(policy_id, '^P-2024-(.+)-[^-]+$', 1) AS topic
  FROM arjoon_ws_catalog.policylens_silver.silver_medical_policy
),
ebcbs AS (SELECT * FROM pol WHERE payer = 'EBCBS'),
ebcbs_cpt AS (SELECT policy_id, topic, explode(cpt_codes_covered) AS cpt_code FROM ebcbs),
comp_cpt AS (
  SELECT topic, explode(cpt_codes_covered) AS cpt_code
  FROM pol WHERE payer <> 'EBCBS'
),
cpt_cover AS (
  SELECT e.policy_id, e.topic, e.cpt_code, COUNT(cc.cpt_code) AS competitors_covering
  FROM ebcbs_cpt e
  LEFT JOIN comp_cpt cc ON e.topic = cc.topic AND e.cpt_code = cc.cpt_code
  GROUP BY e.policy_id, e.topic, e.cpt_code
),
excl AS (
  SELECT policy_id,
         COUNT(*) AS n_ebcbs_cpts,
         SUM(CASE WHEN competitors_covering < 2 THEN 1 ELSE 0 END) AS n_exclusive_cpts
  FROM cpt_cover GROUP BY policy_id
),
comp_cnt AS (SELECT topic, COUNT(*) AS n_competitors FROM pol WHERE payer <> 'EBCBS' GROUP BY topic),
pa AS (
  SELECT policy_id, COUNT(*) AS pa_requests,
         ROUND(AVG(CASE WHEN decision = 'denied' THEN 1 ELSE 0 END), 4) AS denial_rate,
         ROUND(AVG(CASE WHEN appeal_flag THEN 1 ELSE 0 END), 4)         AS appeal_rate
  FROM arjoon_ws_catalog.policylens_silver.silver_prior_auth GROUP BY policy_id
),
comp_r AS (
  SELECT regexp_extract(competitor_id, '^P-2024-(.+)-[^-]+$', 1) AS topic,
         ROUND(AVG(restrictiveness_score), 3) AS avg_competitor_restrictiveness
  FROM arjoon_ws_catalog.policylens_silver.silver_competitor_policy GROUP BY topic
),
util AS (
  SELECT ec.policy_id, SUM(cus.total_procedures) AS total_procedures,
         ROUND(SUM(cus.total_allowed), 2) AS total_allowed
  FROM ebcbs_cpt ec
  JOIN arjoon_ws_catalog.policylens_gold.cpt_utilization_summary cus USING (cpt_code)
  GROUP BY ec.policy_id
)
SELECT e.policy_id, e.policy_name, e.policy_category, e.topic, e.prior_auth_required,
       x.n_ebcbs_cpts, x.n_exclusive_cpts, cc.n_competitors,
       COALESCE(p.pa_requests, 0)  AS pa_requests,
       COALESCE(p.denial_rate, 0)  AS denial_rate,
       COALESCE(p.appeal_rate, 0)  AS appeal_rate,
       cr.avg_competitor_restrictiveness,
       COALESCE(u.total_procedures, 0) AS total_procedures,
       COALESCE(u.total_allowed, 0)    AS total_allowed,
       e.criteria_text
FROM ebcbs e
JOIN excl x USING (policy_id)
LEFT JOIN comp_cnt cc ON e.topic = cc.topic
LEFT JOIN pa p        ON e.policy_id = p.policy_id
LEFT JOIN comp_r cr   ON e.topic = cr.topic
LEFT JOIN util u      ON e.policy_id = u.policy_id;

-- ============================================================================
-- 3) financial_impact_scenarios — annualized baseline per EBCBS policy CPT (feeds simulator/ML)
-- ============================================================================
CREATE OR REPLACE TABLE arjoon_ws_catalog.policylens_gold.financial_impact_scenarios AS
WITH ebcbs_cpt AS (
  SELECT policy_id, explode(cpt_codes_covered) AS cpt_code
  FROM arjoon_ws_catalog.policylens_silver.silver_medical_policy WHERE payer = 'EBCBS'
)
SELECT ec.policy_id, ec.cpt_code, c.description, c.category,
       ROUND(cus.total_allowed / 3.0, 2)      AS annual_allowed,
       ROUND(cus.total_paid / 3.0, 2)         AS annual_paid,
       CAST(ROUND(cus.total_procedures / 3.0, 0) AS BIGINT) AS annual_procedures,
       cus.avg_cost_per_procedure, cus.avg_denial_rate, cus.avg_prior_auth_rate
FROM ebcbs_cpt ec
JOIN arjoon_ws_catalog.policylens_gold.cpt_utilization_summary cus USING (cpt_code)
JOIN arjoon_ws_catalog.policylens_silver.silver_cpt_code c USING (cpt_code);

-- ============================================================================
-- 4) policy_gap_alerts — rule-based gap detection (feeds the app + agent + gap classifier)
-- ============================================================================
CREATE OR REPLACE TABLE arjoon_ws_catalog.policylens_gold.policy_gap_alerts AS
SELECT policy_id, policy_name, 'more_permissive' AS gap_type,
       -- WHERE below already requires >= 3 exclusive; tier high at >= 4 so severity is meaningful
       CASE WHEN n_exclusive_cpts >= 4 THEN 'high' ELSE 'medium' END AS severity,
       CONCAT('EBCBS covers ', n_exclusive_cpts, ' CPT code(s) that fewer than 2 of ',
              n_competitors, ' competitors cover, and prior authorization is not required.') AS description,
       CAST(n_exclusive_cpts AS DOUBLE) AS detail_metric
FROM arjoon_ws_catalog.policylens_gold.policy_comparison_features
WHERE n_exclusive_cpts >= 3 AND prior_auth_required = false
UNION ALL
SELECT policy_id, policy_name, 'more_restrictive',
       CASE WHEN denial_rate > 0.25 THEN 'high' ELSE 'medium' END,
       CONCAT('EBCBS prior-auth denial rate ', ROUND(denial_rate * 100, 1), '% and appeal rate ',
              ROUND(appeal_rate * 100, 1), '% — stricter than competitor norms.'),
       CAST(denial_rate AS DOUBLE)
FROM arjoon_ws_catalog.policylens_gold.policy_comparison_features
WHERE denial_rate > 0.20
UNION ALL
SELECT policy_id, policy_name, 'ambiguous_language', 'medium',
       'Policy criteria contains vague/subjective language that can drive inconsistent decisions across regions.',
       CAST(NULL AS DOUBLE)
FROM arjoon_ws_catalog.policylens_gold.policy_comparison_features
WHERE LOWER(criteria_text) RLIKE '(case-by-case|deems|may be approved|as determined|appropriate documentation)';
