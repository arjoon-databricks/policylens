-- PolicyLens — Step 2 (governance): Unity Catalog masking, row filters, PII tags.
-- Applied to the silver layer via resources/dbsql.sh. All data synthetic.
-- Lineage is captured automatically by UC from the Lakeflow pipeline (raw -> bronze_* -> silver_*).

-- 1) Column mask on member PII: only members of `policylens_pii_readers` see the raw id;
--    everyone else sees a redacted value. (Group need not exist — non-members get the mask.)
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_silver.mask_member_id(member_id STRING)
  RETURN CASE WHEN is_account_group_member('policylens_pii_readers') THEN member_id
              ELSE concat('M****', substr(member_id, -2)) END;

ALTER TABLE arjoon_ws_catalog.policylens_silver.silver_claims
  ALTER COLUMN member_id SET MASK arjoon_ws_catalog.policylens_silver.mask_member_id;
ALTER TABLE arjoon_ws_catalog.policylens_silver.silver_prior_auth
  ALTER COLUMN member_id SET MASK arjoon_ws_catalog.policylens_silver.mask_member_id;

-- 2) Row filter (row-level security): members of `policylens_restricted` see only their
--    region (Rochester); everyone else sees all rows. Demonstrates RLS without breaking analytics.
CREATE OR REPLACE FUNCTION arjoon_ws_catalog.policylens_silver.claims_region_filter(region STRING)
  RETURN NOT is_account_group_member('policylens_restricted') OR region = 'Rochester';

ALTER TABLE arjoon_ws_catalog.policylens_silver.silver_claims
  SET ROW FILTER arjoon_ws_catalog.policylens_silver.claims_region_filter ON (region);

-- 3) Governance tags on member identifiers.
--    NOTE: this metastore enforces tag-governance policies — the `classification` key
--    only permits [confidential, restricted, public, internal], so member_id is tagged
--    `confidential` (the `pii` key is reserved for [ssn, address]).
ALTER TABLE arjoon_ws_catalog.policylens_silver.silver_claims
  ALTER COLUMN member_id SET TAGS ('classification' = 'confidential');
ALTER TABLE arjoon_ws_catalog.policylens_silver.silver_prior_auth
  ALTER COLUMN member_id SET TAGS ('classification' = 'confidential');
