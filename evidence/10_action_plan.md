# Level-up B — SHAP-grounded action-plan memos

_Generated 2026-09-22 03:54 UTC — synthetic data; EBCBS is a code name._


## Setup

- **model_run**: fbff52c30ec748758313ec624e46fbe9
- **features**: 12
- **shap_rows**: 2088

## Action-plan inference table

- **table**: arjoon_ws_catalog.policylens_ml.gap_action_plans
- **memos**: 5
- **also audit-logged via gateway**: arjoon_ws_catalog.policylens_ml.policylens_copilot_payload

## Memo — P-2024-KNEE-01 (ambiguous_language, medium)

- **SHAP drivers**: [["cat_surgical", 1.021], ["avg_national_cost", 0.371], ["cms_rvu", 0.133]]
# Policy Administration Memo: P-2024-KNEE-01 (Knee Arthroscopy)

**Finding**
Policy P-2024-KNEE-01 contains ambiguous, subjectively-worded coverage criteria, creating risk of inconsistent adjudication across regions. Current administration lacks prior authorization despite this ambiguity.

**Evidence**
- No prior authorization requirement (prior_auth_required: false), removing a natural checkpoint to enforce consistent criteria application.
- 0% denial rate and 0% appeal rate suggest either highly permissive interpretation or lack of enforcement mechanism to test criteria against claims.
- Policy is notably less restrictive than peers (avg_competitor_restrictiveness: 0.803 vs. this policy's effectively unconstrained posture).
- SHAP drivers show surgical category (1.021) and national cost benchmarks (0.371) as dominant financial exposure drivers—ambiguity in a high-cost surgical category compounds inconsistent-application risk.

**Recommended action**
Revise policy language to replace subjective criteria with objective, measurable clinical documentation standards. Consider introducing prior authorization or retrospective audit protocols specifically for the 4 exclusive CPT codes to standardize regional decision-making without altering clinical thresholds.

**Financial context**
Total allowed amount under this policy is $2.135B, indicating substantial budget exposure where incon

## Memo — P-2024-CARD-01 (ambiguous_language, medium)

- **SHAP drivers**: [["cat_surgical", 0.573], ["avg_national_cost", 0.18], ["cms_rvu", 0.099]]
# Policy Administration Memo: P-2024-CARD-01 (Advanced Cardiac Imaging)

**Finding**
Policy P-2024-CARD-01 contains ambiguous/subjective criteria language, creating risk of inconsistent adjudication decisions across regions.

**Evidence**
- Denial rate of 22.64% against a modest appeal rate of 5.89% suggests reviewers may be applying subjective criteria inconsistently, with denials not being systematically challenged.
- No exclusive CPT codes (n=0) means criteria rely on descriptive/clinical language rather than discrete code-based triggers—the likely source of ambiguity.
- Competitor restrictiveness averages 0.60, indicating peer plans have tightened criteria; EBCBS's vaguer language may create both audit exposure and adjudication variance.
- SHAP drivers show `cat_surgical` (0.573) dominates financial risk modeling, with `avg_national_cost` (0.18) secondary—indicating surgical-category imaging claims are the primary driver of variability tied to this policy.

**Recommended action**
Revise policy language to incorporate specific CPT-code anchors and objective, measurable criteria (e.g., quantitative thresholds) for the surgical-category imaging subset. Consider requiring standardized documentation templates for prior-auth submissions to reduce subjective interpretation.

**Financial context**
Total allowed amount under this policy is $210.7M, indicating substantial exposure to

## Memo — P-2024-CARD-01 (more_restrictive, medium)

- **SHAP drivers**: [["cat_surgical", 0.573], ["avg_national_cost", 0.18], ["cms_rvu", 0.099]]
# Recommendation Memo: P-2024-CARD-01 — Advanced Cardiac Imaging Medical Policy

**Finding:** EBCBS applies materially stricter prior-authorization controls than competitor norms for advanced cardiac imaging, evidenced by a 22.6% denial rate against a 0.60 average competitor restrictiveness index, with a comparatively low 5.9% appeal rate suggesting under-contestation rather than justified denial volume.

**Evidence:** Denial rate (22.64%) and appeal rate (5.89%) indicate restrictiveness beyond peer norms; no exclusive CPT carve-outs (n_exclusive_cpts=0) suggest the policy's stringency stems from broad prior-auth criteria rather than targeted code exclusions. SHAP drivers show category (surgical, 0.573) and national cost benchmarks (0.18) as dominant drivers of financial model sensitivity, indicating the policy's restrictiveness is closely tied to cost-driven UM logic rather than clinical differentiation.

**Recommended action:** Review prior-auth criteria against competitor documentation standards; consider tiering requirements by CPT risk/cost rather than blanket restriction, and audit denial reason codes to confirm alignment with medical necessity guidelines vs. cost-avoidance patterns.

**Financial context:** Policy governs $210.7M in allowed charges; administrative tightening here carries meaningful exposure to member/provider appeals and abrasion risk at this volume.

**C

## Memo — P-2024-SPINE-01 (more_restrictive, high)

- **SHAP drivers**: [["cat_surgical", 1.108], ["avg_national_cost", 0.479], ["cms_rvu", 0.365]]
# Policy Administration Memo: P-2024-SPINE-01 (Lumbar Spinal Fusion)

**Finding:** EBCBS's prior-authorization criteria for lumbar spinal fusion are administratively stricter than the competitive market, driving elevated denial and appeal volumes relative to peer norms.

**Evidence:** Denial rate of 32.3% and appeal rate of 18.9% both exceed the average competitor restrictiveness benchmark of 0.392, flagging this policy as "more restrictive." SHAP drivers indicate the surgical category classification (cat_surgical, 1.108) is the dominant factor amplifying scrutiny, with avg_national_cost (0.479) and CMS RVU weight (0.365) compounding the high-cost-procedure profile that triggers stringent UM review. No exclusive CPT carve-outs (n_exclusive_cpts = 0) suggest the restrictiveness stems from documentation/criteria thresholds rather than coding scope.

**Recommended action:** Review prior-auth clinical criteria and documentation requirements against competitor benchmarks to identify specific thresholds (e.g., conservative-care duration, imaging requirements) driving the denial gap. Consider calibrating UM criteria closer to the 0.392 market-restrictiveness norm and streamlining appeal-triggering documentation gaps.

**Financial context:** Policy governs $1.71B in total allowed spend; misalignment in UM criteria carries budget exposure risk from administrative overhead (appeals proce

## Memo — P-2024-KNEE-01 (more_permissive, high)

- **SHAP drivers**: [["cat_surgical", 1.021], ["avg_national_cost", 0.371], ["cms_rvu", 0.133]]
# Recommendation Memo: P-2024-KNEE-01 (Knee Arthroscopy Medical Policy)

**Finding**
EBCBS coverage is materially more permissive than the competitive market: 4 CPT codes are covered exclusively (or near-exclusively) versus peers, with no prior authorization requirement, while average competitor restrictiveness sits at 0.803. This is a high-severity administrative gap.

**Evidence**
- 4 exclusive CPTs uncovered by ≥2 of 4 competitors; PA not required (vs. 0.803 avg competitor restrictiveness).
- Denial rate and appeal rate are both 0.0%, consistent with an absence of UM gating on these codes.
- SHAP drivers indicate the surgical category (cat_surgical, 1.021) is the dominant factor in financial exposure, amplified by avg_national_cost (0.371) and CMS RVU weight (0.133) — signaling these are high-cost surgical procedures with no administrative checkpoint.

**Recommended action**
Introduce prior authorization or documentation/medical-necessity criteria for the 4 exclusive CPT codes, aligned to competitor UM standards, to close the administrative gap without altering clinical coverage intent.

**Financial context**
Total allowed amount exposure across this policy is ~$2.14B; the 4 uncontrolled surgical CPTs represent a disproportionate share of this exposure per SHAP weighting, given high per-unit cost (cat_surgical, avg_national_cost).

**Caveat**
Analysis is based on aggregate c