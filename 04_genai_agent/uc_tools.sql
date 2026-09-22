-- PolicyLens — Step 6: Unity Catalog function tools for the Gen AI agent.
-- Registered as UC functions in policylens_gold so the agent can call them as governed tools.
-- (RAG tools compare_policies / search_industry_guidelines use the Vector Search index; the
--  create_review_case tool writes to Lakebase — both live in the agent notebook.)
-- All data synthetic; EBCBS is a code name.

-- Tool: utilization + cost for a CPT code
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.get_utilization_data(cpt STRING)
RETURNS TABLE(cpt_code STRING, description STRING, total_procedures BIGINT, total_allowed DOUBLE,
              avg_cost_per_procedure DOUBLE, avg_prior_auth_rate DOUBLE, avg_denial_rate DOUBLE)
COMMENT 'Return utilization and cost metrics for a single CPT code from the gold utilization summary.'
RETURN SELECT cpt_code, description, total_procedures, total_allowed, avg_cost_per_procedure,
              avg_prior_auth_rate, avg_denial_rate
       FROM arjoon_ws_catalog.policylens_gold.cpt_utilization_summary WHERE cpt_code = cpt;

-- Tool: prior-auth analysis for a policy, broken out by region (reveals regional variance)
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.get_prior_auth_analysis(policy STRING)
RETURNS TABLE(policy_id STRING, region STRING, pa_requests BIGINT, denial_rate DOUBLE, appeal_rate DOUBLE)
COMMENT 'Return prior-authorization denial and appeal rates by region for a given policy_id.'
RETURN SELECT policy_id, region, COUNT(*) AS pa_requests,
              ROUND(AVG(CASE WHEN decision='denied' THEN 1 ELSE 0 END),4) AS denial_rate,
              ROUND(AVG(CASE WHEN appeal_flag THEN 1 ELSE 0 END),4) AS appeal_rate
       FROM arjoon_ws_catalog.policylens_silver.silver_prior_auth WHERE policy_id = policy
       GROUP BY policy_id, region;

-- Tool: competitor coverage comparison for an EBCBS policy
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.compare_policy_coverage(ebcbs_policy STRING)
RETURNS TABLE(policy_id STRING, policy_name STRING, prior_auth_required BOOLEAN, n_ebcbs_cpts INT,
              n_exclusive_cpts INT, n_competitors INT, denial_rate DOUBLE, appeal_rate DOUBLE,
              avg_competitor_restrictiveness DOUBLE, total_allowed DOUBLE)
COMMENT 'Return EBCBS-vs-competitor comparison features for a given EBCBS policy_id.'
RETURN SELECT policy_id, policy_name, prior_auth_required, n_ebcbs_cpts, n_exclusive_cpts,
              n_competitors, denial_rate, appeal_rate, avg_competitor_restrictiveness, total_allowed
       FROM arjoon_ws_catalog.policylens_gold.policy_comparison_features WHERE policy_id = ebcbs_policy;

-- Tool: simulate financial impact of adding/removing a CPT (grounded in ML batch predictions)
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_gold.simulate_financial_impact(
    policy STRING, change_type STRING, cpt STRING)
RETURNS TABLE(policy_id STRING, cpt_code STRING, change_type STRING,
              predicted_annual_allowed DOUBLE, estimated_impact DOUBLE)
COMMENT 'Estimate annualized financial impact of adding or removing a CPT code, using ML-predicted annual allowed $.'
RETURN
  WITH pred AS (
    SELECT ROUND(SUM(predicted_allowed)/3.0, 2) AS predicted_annual_allowed
    FROM arjoon_ws_catalog.policylens_ml.financial_impact_predictions WHERE cpt_code = cpt)
  SELECT policy AS policy_id, cpt AS cpt_code, change_type,
         pred.predicted_annual_allowed,
         CASE WHEN lower(change_type)='remove' THEN -pred.predicted_annual_allowed
              WHEN lower(change_type)='add'    THEN  pred.predicted_annual_allowed
              ELSE 0 END AS estimated_impact
  FROM pred;
