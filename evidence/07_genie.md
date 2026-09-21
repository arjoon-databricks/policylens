# Step 7 — Genie + Metric Views (semantic self-serve)

_Synthetic data; EBCBS is a code name._

## Metric View (semantic layer) — `arjoon_ws_catalog.policylens_gold.mv_policy_metrics`

UC Metric View over `util_enriched` (silver_utilization ⋈ silver_cpt_code).
- **Dimensions**: CPT Code, Category, Month
- **Measures**: Total Procedures, Total Allowed, Avg Denial Rate, Avg Prior Auth Rate

Verified with a semantic `MEASURE()` query:

| Category | Total Allowed |
| --- | --- |
| surgical | $5.12B |
| diagnostic | $591M |
| therapeutic | $81.5M |
| evaluation_management | $69.9M |
| pharmaceutical | $21.8M |

## Genie Space — "PolicyLens - Medical Policy Intelligence (EBCBS)"

- **space_id**: `01f1b60efe501b9f9c318dfa6d59059b`
- **7 governed tables**: policy_comparison_features, cpt_utilization_summary, util_enriched,
  policy_gap_alerts (gold) + silver_prior_auth, silver_medical_policy, silver_cpt_code (silver)
- **8 curated sample questions** (from the Build Plan), including
  "Show denial rate by region for policy P-2024-KNEE-01" and
  "What is the PMPM cost trend for procedures requiring prior authorization?"
- **Instructions/guardrail**: advise on policy administration only, never clinical decisions,
  never frame value as cost savings.

### End-to-end NL query test (Conversation API)

**Question:** "Show denial rate by region for policy P-2024-CARD-01" → status **COMPLETED**.

Genie generated this SQL over the governed table:
```sql
SELECT `region`, try_divide(100.0 * SUM(CASE WHEN `decision` ILIKE '%denied%' THEN 1 ELSE 0 END), COUNT(*)) AS `denial_rate`
FROM `arjoon_ws_catalog`.`policylens_silver`.`silver_prior_auth`
WHERE `policy_id` = 'P-2024-CARD-01' AND `region` IS NOT NULL
GROUP BY `region` ORDER BY `region`
```

And answered:
> For policy P-2024-CARD-01, the denial rate varies across 5 regions — Utica-Mohawk **38.43%**,
> Central NY **37.05%**, Southern Tier **20.87%**, Finger Lakes **13.63%**, Rochester **9.82%**.
> The highest is Utica-Mohawk and the lowest is Rochester, showing a wide regional spread.

This confirms the semantic self-serve layer surfaces the seeded cardiac-imaging regional-variance gap through natural language.
