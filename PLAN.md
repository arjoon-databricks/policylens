# PLAN.md — PolicyLens FE Bar plan

All data synthetic; "EBCBS" is a code name for a Blue Cross Blue Shield plan.

## Objective

A working, end-to-end AI prototype for medical-policy intelligence at a BCBS health plan, integrating all
six Databricks-native layers as one connected data journey — targeting **Strongly Passed** (Exceeds across
Product, Industry, Build + AI Mindset, and Customer Skills).

**Origin:** a vendor pitched an expensive fixed-report tool; PolicyLens is the interactive, AI-powered,
in-house alternative. **ROI is framed as admin efficiency and better-informed decisions — never cost savings.**

## Personas

- **Executive sponsor** — VP Medical Policy / CMO: policy competitiveness, regulatory compliance, member
  outcomes, admin efficiency; measured on review-cycle time, appeals rate, UM effectiveness.
- **Domain owner** — Medical Policy Analyst lead: accurate comparisons and defensible recommendations;
  measured on policies reviewed per cycle and time per comparison.

## Capabilities

1. **Compare** one or more EBCBS policies against 4 competitor plans (CPT coverage + criteria language).
2. **Identify gaps** — where EBCBS is more/less restrictive than competitors.
3. **Simulate** the historical + forecast financial impact of adding/removing CPT codes or changing criteria.
4. **Generate** AI-drafted recommendations grounded in utilization data and competitor analysis.

## Six layers → build sequence

| Step | Layer | Deliverable |
|---|---|---|
| 1 | Data foundation | Synthetic generator → raw Volume (claims, PA, utilization, policies, CPT) |
| 2 | Lakeflow + Unity Catalog | SDP medallion (bronze→silver, DQ) + governance (mask/RLS/tags/lineage) |
| 3 | Gold | Feature tables: comparison, utilization summary, financial scenarios, gap alerts |
| 4 | ML | Financial-impact regressor + policy-gap classifier (MLflow, SHAP, batch scores) |
| 5 | Lakebase | OLTP serving: gold read tables + transactional review-case tables |
| 6 | Gen AI Agent | Vector Search RAG + 6 UC/Lakebase tools + Claude, guardrailed |
| 7 | Genie | Metric View semantic layer + Genie space (8 curated questions) |
| 8 | Databricks App | PolicyLens Command Center (dashboard, comparison, simulator, copilot, KPIs) |
| 9 | Evidence | README/BUILD/PLAN, per-step evidence, presentation deck |

## Data model (synthetic)

`dim_cpt_code`, `dim_medical_policy` (EBCBS + Competitor_A..D), `dim_competitor_policy`,
`fact_claims` (~2M), `fact_prior_auth` (40K), `fact_utilization` (CPT × month).

## Seeded gaps (for realistic ML/agent signal)

1. **Knee arthroscopy** `P-2024-KNEE-01` — overly permissive (covers CPTs competitors exclude; no PA).
2. **Spinal fusion** `P-2024-SPINE-01` — overly restrictive (extra criteria; high denial + appeals).
3. **Cardiac imaging** `P-2024-CARD-01` — ambiguous language (inconsistent PA decisions by region).

## Target KPIs

| KPI | Manual baseline | With PolicyLens |
|---|---|---|
| Annual policy review cycle | ~12 weeks | < 1 week |
| Time per policy comparison | ~8 hours | ~30 minutes |
| Financial simulation turnaround | ~2 weeks | real-time |
| Policy gaps identified per cycle | ~15 | ~50 |
| Analyst hours per cycle | ~2,400 | ~400 (~2,000 saved) |

## Evidence gates

- All 6 layers present, functional, and integrated.
- Notebook cells committed with **text** outputs (screenshots don't count) → `evidence/*.md` + HTML renders.
- README/BUILD documenting workflow, AI tools, decisions/trade-offs.
- No real customer data; "EBCBS" throughout.
- Presentation deck exported to the shared Google Drive folder.
