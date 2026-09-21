-- PolicyLens — Step 7: semantic layer (Metric View) for Genie self-serve.
-- All data synthetic; EBCBS is a code name.

CREATE OR REPLACE VIEW arjoon_ws_catalog.policylens_gold.util_enriched AS
SELECT u.cpt_code, u.year_month, u.procedure_count, u.unique_members, u.total_allowed, u.total_paid,
       u.avg_cost_per_procedure, u.prior_auth_rate, u.denial_rate,
       c.category, c.description, c.avg_national_cost
FROM arjoon_ws_catalog.policylens_silver.silver_utilization u
JOIN arjoon_ws_catalog.policylens_silver.silver_cpt_code c USING (cpt_code);

-- Unity Catalog Metric View (semantic layer): governed dimensions + measures.
CREATE OR REPLACE VIEW arjoon_ws_catalog.policylens_gold.mv_policy_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 0.1
source: arjoon_ws_catalog.policylens_gold.util_enriched
dimensions:
  - name: CPT Code
    expr: cpt_code
  - name: Category
    expr: category
  - name: Month
    expr: year_month
measures:
  - name: Total Procedures
    expr: SUM(procedure_count)
  - name: Total Allowed
    expr: SUM(total_allowed)
  - name: Avg Denial Rate
    expr: AVG(denial_rate)
  - name: Avg Prior Auth Rate
    expr: AVG(prior_auth_rate)
$$;
