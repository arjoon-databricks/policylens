# Databricks notebook source
# MAGIC %md
# MAGIC # PolicyLens — Step 1: Synthetic Data Generator
# MAGIC
# MAGIC Generates the **synthetic** EBCBS medical-policy dataset and lands raw files in the
# MAGIC UC Volume `arjoon_ws_catalog.policylens_bronze.raw` for Lakeflow / Auto Loader ingestion.
# MAGIC
# MAGIC **No real customer data.** "EBCBS" is a code name for a Blue Cross Blue Shield plan.
# MAGIC
# MAGIC Tables produced (raw landing):
# MAGIC - `dim_cpt_code`, `dim_medical_policy`, `dim_competitor_policy`
# MAGIC - `fact_claims` (~2M rows, monthly-partitioned parquet)
# MAGIC - `fact_prior_auth` (~40K), `fact_utilization` (CPT × month, aggregated for consistency)
# MAGIC
# MAGIC **3 seeded gaps** (consistent across every table):
# MAGIC 1. `P-2024-KNEE-01` knee arthroscopy — EBCBS covers 5 CPTs 3/4 competitors exclude; vague criteria; high util, low denial → **overly permissive**
# MAGIC 2. `P-2024-SPINE-01` spinal fusion — EBCBS criteria stricter than all competitors → high denial + high appeals → **overly restrictive**
# MAGIC 3. `P-2024-CARD-01` cardiac imaging — ambiguous language → inconsistent PA decisions, high **regional variance**

# COMMAND ----------

# MAGIC %run ./policylens_common

# COMMAND ----------

import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
RAW = RAW_VOLUME  # /Volumes/arjoon_ws_catalog/policylens_bronze/raw
for sub in ["cpt", "policies", "competitor_policies", "claims", "prior_auth", "utilization"]:
    os.makedirs(f"{RAW}/{sub}", exist_ok=True)

MONTHS = pd.period_range("2023-01", "2025-12", freq="M")   # 36 months
REGIONS = ["Rochester", "Central NY", "Southern Tier", "Utica-Mohawk", "Finger Lakes"]
REGION_W = np.array([0.32, 0.24, 0.16, 0.14, 0.14])
N_MEMBERS = 250_000
N_PROVIDERS = 6_000
TOTAL_CLAIMS = 2_000_000

rep = EvidenceReport("01_data_generation", "Step 1 — Synthetic Data Generation (EBCBS)")
rep.kv("seed", 42).kv("months", f"{MONTHS[0]}..{MONTHS[-1]} ({len(MONTHS)})").kv(
    "target_claims", f"{TOTAL_CLAIMS:,}").kv("members_pool", f"{N_MEMBERS:,}").kv(
    "providers_pool", f"{N_PROVIDERS:,}")

# COMMAND ----------

# MAGIC %md ## dim_cpt_code — curated realistic CPT reference

# COMMAND ----------

# (cpt, description, category, subcategory, avg_national_cost, freq_weight)
CPTS = [
    # --- knee arthroscopy (KNEE gap) ---
    ("29880", "Arthroscopy knee, meniscectomy medial AND lateral", "surgical", "orthopedic", 5200, 6),
    ("29881", "Arthroscopy knee, meniscectomy medial OR lateral", "surgical", "orthopedic", 4800, 8),
    ("29882", "Arthroscopy knee, meniscus repair", "surgical", "orthopedic", 6100, 3),
    ("29883", "Arthroscopy knee, meniscus repair medial AND lateral", "surgical", "orthopedic", 7300, 2),
    ("29866", "Arthroscopy knee, osteochondral autograft", "surgical", "orthopedic", 8900, 2),
    ("29867", "Arthroscopy knee, osteochondral allograft", "surgical", "orthopedic", 9600, 2),
    ("29868", "Arthroscopy knee, meniscal transplantation", "surgical", "orthopedic", 11200, 1),
    ("27447", "Total knee arthroplasty", "surgical", "orthopedic", 32000, 3),
    # --- spinal fusion (SPINE gap) ---
    ("22633", "Lumbar spinal fusion, posterior + interbody, single level", "surgical", "spine", 41000, 3),
    ("22634", "Lumbar spinal fusion, each additional level", "surgical", "spine", 12000, 2),
    ("22612", "Lumbar spinal fusion, posterior", "surgical", "spine", 38000, 2),
    ("22630", "Lumbar spinal fusion, posterior interbody", "surgical", "spine", 39000, 2),
    ("63047", "Laminectomy/decompression, lumbar single segment", "surgical", "spine", 22000, 3),
    ("22551", "Cervical spinal fusion, anterior interbody", "surgical", "spine", 44000, 2),
    # --- cardiac imaging (CARD gap) ---
    ("75574", "CT angiography, heart with contrast", "diagnostic", "cardiac_imaging", 1400, 5),
    ("78452", "Myocardial perfusion imaging, SPECT multiple", "diagnostic", "cardiac_imaging", 1600, 6),
    ("93306", "Transthoracic echocardiography, complete w/ Doppler", "diagnostic", "cardiac_imaging", 700, 9),
    ("75561", "Cardiac MRI with contrast", "diagnostic", "cardiac_imaging", 2100, 3),
    ("71275", "CT angiography, chest", "diagnostic", "cardiac_imaging", 1300, 4),
    ("78451", "Myocardial perfusion imaging, SPECT single", "diagnostic", "cardiac_imaging", 1200, 4),
    ("93350", "Stress echocardiography", "diagnostic", "cardiac_imaging", 1100, 5),
    ("93458", "Cardiac catheterization, left heart w/ angiography", "diagnostic", "cardiac_imaging", 3800, 3),
    # --- other surgical ---
    ("27130", "Total hip arthroplasty", "surgical", "orthopedic", 34000, 3),
    ("29827", "Arthroscopy shoulder, rotator cuff repair", "surgical", "orthopedic", 9800, 3),
    ("66984", "Cataract removal with intraocular lens", "surgical", "ophthalmology", 3200, 7),
    ("47562", "Laparoscopic cholecystectomy", "surgical", "general", 11500, 4),
    ("49505", "Repair inguinal hernia", "surgical", "general", 6400, 4),
    ("58150", "Total abdominal hysterectomy", "surgical", "gynecology", 14000, 2),
    ("43644", "Laparoscopic gastric bypass", "surgical", "bariatric", 24000, 2),
    ("43775", "Laparoscopic sleeve gastrectomy", "surgical", "bariatric", 18000, 2),
    # --- diagnostic imaging ---
    ("70553", "MRI brain with and without contrast", "diagnostic", "imaging", 1500, 6),
    ("72148", "MRI lumbar spine without contrast", "diagnostic", "imaging", 1200, 9),
    ("72141", "MRI cervical spine without contrast", "diagnostic", "imaging", 1200, 6),
    ("74177", "CT abdomen and pelvis with contrast", "diagnostic", "imaging", 1100, 8),
    ("71260", "CT chest with contrast", "diagnostic", "imaging", 900, 6),
    ("77067", "Screening mammography, bilateral", "diagnostic", "imaging", 250, 12),
    ("76700", "Ultrasound abdomen, complete", "diagnostic", "imaging", 300, 8),
    # --- diagnostic procedures ---
    ("45380", "Colonoscopy with biopsy", "diagnostic", "gastroenterology", 1600, 8),
    ("45378", "Colonoscopy, diagnostic", "diagnostic", "gastroenterology", 1200, 9),
    ("43239", "Upper GI endoscopy with biopsy", "diagnostic", "gastroenterology", 1400, 6),
    ("95810", "Polysomnography, sleep study (attended)", "diagnostic", "sleep", 2400, 5),
    ("95811", "Polysomnography with CPAP titration", "diagnostic", "sleep", 2600, 4),
    # --- therapeutic ---
    ("64483", "Transforaminal epidural injection, lumbar", "therapeutic", "pain", 1300, 6),
    ("62323", "Epidural injection, lumbar with imaging", "therapeutic", "pain", 1100, 6),
    ("20610", "Arthrocentesis/injection major joint", "therapeutic", "orthopedic", 250, 12),
    ("97110", "Therapeutic exercise, physical therapy", "therapeutic", "rehab", 120, 20),
    ("97140", "Manual therapy techniques", "therapeutic", "rehab", 110, 16),
    # --- pharmaceutical (physician-administered) ---
    ("96413", "Chemotherapy infusion, up to 1 hour", "pharmaceutical", "oncology", 900, 5),
    ("96372", "Therapeutic injection, subcutaneous/IM", "pharmaceutical", "medicine", 90, 14),
    # --- evaluation & management (high frequency, no policy) ---
    ("99213", "Office visit, established patient, low complexity", "evaluation_management", "office", 120, 40),
    ("99214", "Office visit, established patient, moderate complexity", "evaluation_management", "office", 180, 38),
    ("99204", "Office visit, new patient, moderate complexity", "evaluation_management", "office", 210, 18),
    ("99215", "Office visit, established patient, high complexity", "evaluation_management", "office", 260, 12),
    # --- laboratory (high frequency, no policy) ---
    ("80053", "Comprehensive metabolic panel", "laboratory", "chemistry", 45, 30),
    ("85025", "Complete blood count with differential", "laboratory", "hematology", 35, 32),
    ("83036", "Hemoglobin A1c", "laboratory", "chemistry", 40, 22),
    ("84443", "Thyroid stimulating hormone (TSH)", "laboratory", "chemistry", 50, 18),
    ("80061", "Lipid panel", "laboratory", "chemistry", 42, 24),
]
cpt_df = pd.DataFrame(CPTS, columns=["cpt_code", "description", "category", "subcategory", "avg_national_cost", "freq_weight"])
# CMS RVU ~ cost-scaled with mild noise
cpt_df["cms_rvu"] = np.round(cpt_df["avg_national_cost"] / 55.0 * rng.uniform(0.85, 1.15, len(cpt_df)), 2)
cpt_df["avg_national_cost"] = cpt_df["avg_national_cost"].astype(float)

cpt_out = cpt_df.drop(columns=["freq_weight"])
cpt_out.to_parquet(f"{RAW}/cpt/dim_cpt_code.parquet", index=False)
rep.h("dim_cpt_code").kv("rows", len(cpt_out)).kv("categories", ", ".join(sorted(cpt_df.category.unique())))
rep.table(cpt_out.head(6))

# COMMAND ----------

# MAGIC %md ## dim_medical_policy + dim_competitor_policy — with seeded gaps

# COMMAND ----------

KNEE = ["29880", "29881", "29882", "29883", "29866", "29867", "29868", "27447"]
SPINE = ["22633", "22634", "22612", "22630", "63047", "22551"]
CARD = ["75574", "78452", "93306", "75561", "71275", "78451", "93350", "93458"]

# Competitors A/B/C exclude the 5 EBCBS-permissive knee codes; D covers all.
KNEE_COMPETITOR_COVERAGE = {
    "Competitor_A": ["29880", "29881", "27447"],
    "Competitor_B": ["29880", "29881", "29882", "27447"],
    "Competitor_C": ["29880", "29881", "27447"],
    "Competitor_D": KNEE,
}
KNEE_EBCBS_EXCLUSIVE = ["29883", "29866", "29867", "29868", "29882"]  # 5 codes 3/4 competitors exclude

VAGUE_KNEE = ("Arthroscopic knee procedures, including debridement and chondroplasty, may be considered "
              "medically necessary when the treating physician deems it appropriate. Prior authorization is not required.")
STRICT_KNEE = ("Arthroscopic knee surgery is covered only for meniscal tears confirmed by MRI with documented "
               "mechanical symptoms persisting at least 3 months after conservative therapy. Debridement or "
               "chondroplasty for osteoarthritis is considered not medically necessary.")
STRICT_SPINE = ("Lumbar spinal fusion requires ALL of: at least 12 months of failed conservative therapy, confirmed "
                "instability on flexion-extension imaging, psychological evaluation clearance, BMI under 40, and "
                "documented smoking cessation for at least 6 weeks. Prior authorization required.")
LOOSE_SPINE = ("Lumbar spinal fusion is covered for documented instability or spondylolisthesis after at least 6 months "
               "of conservative therapy. Prior authorization required.")
AMBIG_CARD = ("Advanced cardiac imaging may be approved when clinically indicated and supported by appropriate "
              "documentation, as determined on a case-by-case basis.")
CLEAR_CARD = ("Cardiac imaging (stress echo, myocardial perfusion, cardiac CT/MRI) is covered for intermediate or high "
              "pretest probability of coronary artery disease per a validated risk score; low-risk asymptomatic "
              "screening is not covered.")

# topic -> (name, category, cpts, ebcbs_pa_required, ebcbs_criteria, competitor_criteria)
TOPICS = {
    "KNEE": ("Knee Arthroscopy", "surgical", KNEE, False, VAGUE_KNEE, STRICT_KNEE),
    "SPINE": ("Lumbar Spinal Fusion", "surgical", SPINE, True, STRICT_SPINE, LOOSE_SPINE),
    "CARD": ("Advanced Cardiac Imaging", "diagnostic", CARD, True, AMBIG_CARD, CLEAR_CARD),
    "HIP": ("Total Hip Replacement", "surgical", ["27130"], True, None, None),
    "SHOULDER": ("Shoulder Arthroscopy", "surgical", ["29827"], True, None, None),
    "CATARACT": ("Cataract Surgery", "surgical", ["66984"], True, None, None),
    "CHOLE": ("Laparoscopic Cholecystectomy", "surgical", ["47562"], False, None, None),
    "HERNIA": ("Inguinal Hernia Repair", "surgical", ["49505"], False, None, None),
    "HYSTERECTOMY": ("Hysterectomy", "surgical", ["58150"], True, None, None),
    "BARIATRIC": ("Bariatric Surgery", "surgical", ["43644", "43775"], True, None, None),
    "MRILUMBAR": ("Lumbar Spine MRI", "diagnostic", ["72148"], True, None, None),
    "MRIBRAIN": ("Brain MRI", "diagnostic", ["70553"], True, None, None),
    "CTABD": ("CT Abdomen/Pelvis", "diagnostic", ["74177"], False, None, None),
    "COLON": ("Colonoscopy", "diagnostic", ["45380", "45378"], False, None, None),
    "SLEEP": ("Sleep Study", "diagnostic", ["95810", "95811"], True, None, None),
    "EPIDURAL": ("Epidural Steroid Injection", "therapeutic", ["64483", "62323"], True, None, None),
    "CHEMO": ("Chemotherapy Infusion", "pharmaceutical", ["96413"], True, None, None),
    "MAMMO": ("Screening Mammography", "diagnostic", ["77067"], False, None, None),
}

GENERIC_STRICT = "Prior authorization is required. Coverage is subject to documented medical necessity per plan clinical criteria."
GENERIC_OPEN = "Covered when medically necessary and consistent with accepted standards of care."

PAYER_SUFFIX = {"EBCBS": "01", "Competitor_A": "CA", "Competitor_B": "CB", "Competitor_C": "CC", "Competitor_D": "CD"}

pol_rows, comp_rows = [], []
cpt_to_policy = {}  # EBCBS cpt -> policy_id (for claims/PA linkage)

for topic, (name, cat, cpts, ebcbs_pa, ebcbs_crit, comp_crit) in TOPICS.items():
    for payer in PAYERS:
        pid = f"P-2024-{topic}-{PAYER_SUFFIX[payer]}"
        # coverage
        if topic == "KNEE" and payer != "EBCBS":
            covered = KNEE_COMPETITOR_COVERAGE[payer]
        else:
            covered = cpts
        # criteria + PA
        if payer == "EBCBS":
            criteria = ebcbs_crit or (GENERIC_STRICT if ebcbs_pa else GENERIC_OPEN)
            pa_required = ebcbs_pa
            cpt_to_policy.update({c: pid for c in cpts})
        else:
            if topic == "KNEE":
                criteria, pa_required = (comp_crit, True)
            elif topic == "SPINE":
                criteria, pa_required = (comp_crit, True)
            elif topic == "CARD":
                criteria, pa_required = (comp_crit, True)
            else:
                criteria, pa_required = ((GENERIC_STRICT if ebcbs_pa else GENERIC_OPEN), ebcbs_pa)
        pol_rows.append({
            "policy_id": pid, "policy_name": f"{name} Medical Policy", "policy_category": cat,
            "effective_date": "2024-01-01", "expiration_date": "2026-12-31", "payer": payer,
            "cpt_codes_covered": covered, "prior_auth_required": bool(pa_required),
            "criteria_text": criteria,
            "policy_document_path": f"{RAW}/policy_pdfs/{payer}/{pid}.pdf",
        })
        # competitor detail table with restrictiveness score
        if payer != "EBCBS":
            if topic == "KNEE":       # competitors more restrictive than permissive EBCBS
                rscore = float(np.round(rng.uniform(0.75, 0.90), 2))
            elif topic == "SPINE":    # competitors looser than restrictive EBCBS
                rscore = float(np.round(rng.uniform(0.30, 0.45), 2))
            elif topic == "CARD":
                rscore = float(np.round(rng.uniform(0.55, 0.70), 2))
            else:
                rscore = float(np.round(rng.uniform(0.45, 0.65), 2))
            comp_rows.append({
                "competitor_id": pid, "policy_name": f"{name} Medical Policy", "policy_category": cat,
                "cpt_codes_covered": covered, "criteria_text": criteria, "restrictiveness_score": rscore,
            })

pol_df = pd.DataFrame(pol_rows)
comp_df = pd.DataFrame(comp_rows)
pol_df.to_parquet(f"{RAW}/policies/dim_medical_policy.parquet", index=False)
comp_df.to_parquet(f"{RAW}/competitor_policies/dim_competitor_policy.parquet", index=False)

rep.h("dim_medical_policy").kv("rows", len(pol_df)).kv("topics", len(TOPICS)).kv("payers", len(PAYERS))
rep.h("dim_competitor_policy").kv("rows", len(comp_df))

# PA-eligible EBCBS cpts (policy requires PA) — used for prior-auth generation
ebcbs_pa_cpts = sorted({c for t, (_, _, cpts, pa, *_ ) in TOPICS.items() if pa for c in cpts})
rep.kv("ebcbs_pa_required_cpts", len(ebcbs_pa_cpts))

# COMMAND ----------

# MAGIC %md ## fact_claims — ~2M EBCBS member claims (monthly-partitioned parquet)

# COMMAND ----------

cpt_codes = cpt_df["cpt_code"].to_numpy()
cpt_cost = cpt_df.set_index("cpt_code")["avg_national_cost"].to_dict()
cpt_cat = cpt_df.set_index("cpt_code")["category"].to_dict()
freq = cpt_df["freq_weight"].to_numpy(dtype=float).copy()
# Boost knee codes -> "high utilization" permissive signal
knee_idx = np.isin(cpt_codes, KNEE)
freq[knee_idx] *= 2.3
probs = freq / freq.sum()

ICD_BY_CAT = {
    "surgical": ["M17.11", "M23.205", "M43.16", "M16.11", "K80.20", "K40.90", "E66.01"],
    "diagnostic": ["I25.10", "R07.9", "R10.9", "G47.33", "Z12.11", "R51.9"],
    "therapeutic": ["M54.5", "M25.561", "M79.7"],
    "pharmaceutical": ["C50.911", "C34.90", "D64.9"],
    "evaluation_management": ["Z00.00", "I10", "E11.9", "E78.5"],
    "laboratory": ["Z00.00", "E11.9", "E78.5", "E03.9"],
}

def gen_month(period, n):
    idx = rng.choice(len(cpt_codes), size=n, p=probs)
    codes = cpt_codes[idx]
    cats = np.array([cpt_cat[c] for c in codes])
    base = np.array([cpt_cost[c] for c in codes], dtype=float)
    allowed = np.round(base * np.exp(rng.normal(0, 0.22, n)), 2)
    paid_frac = np.clip(rng.normal(0.86, 0.06, n), 0.55, 0.98)
    paid = np.round(allowed * paid_frac, 2)
    cost_share = np.round(allowed - paid, 2)
    members = np.array(["M%06d" % i for i in rng.integers(0, N_MEMBERS, n)])
    providers = np.array(["PR%05d" % i for i in rng.integers(0, N_PROVIDERS, n)])
    regions = rng.choice(REGIONS, size=n, p=REGION_W)
    dx = np.array([rng.choice(ICD_BY_CAT.get(c, ICD_BY_CAT["evaluation_management"])) for c in cats])
    # service date within the month
    start = period.start_time.to_datetime64()
    days = (period.end_time.normalize() - period.start_time.normalize()).days + 1
    svc = start + rng.integers(0, days, n).astype("timedelta64[D]")
    policy_ids = np.array([cpt_to_policy.get(c) for c in codes], dtype=object)
    # prior_auth_id only where the governing EBCBS policy requires PA
    pa_needed = np.isin(codes, ebcbs_pa_cpts)
    pa_ids = np.where(
        pa_needed & (rng.random(n) < 0.9),
        np.array(["PA%08d" % i for i in rng.integers(0, 5_000_000, n)], dtype=object),
        None,
    )
    ym = str(period)
    df = pd.DataFrame({
        "claim_id": [f"CLM-{ym}-{i:07d}" for i in range(n)],
        "member_id": members, "provider_id": providers, "cpt_code": codes,
        "diagnosis_code": dx, "service_date": pd.to_datetime(svc),
        "allowed_amount": allowed, "paid_amount": paid, "member_cost_share": cost_share,
        "policy_id": policy_ids, "prior_auth_id": pa_ids, "region": regions, "year_month": ym,
    })
    return df

n_per = TOTAL_CLAIMS // len(MONTHS)
claims_agg_parts = []
total_written = 0
for i, period in enumerate(MONTHS):
    n = n_per + (TOTAL_CLAIMS - n_per * len(MONTHS) if i == 0 else 0)
    # mild growth trend over time
    n = int(n * (0.9 + 0.2 * i / len(MONTHS)))
    df = gen_month(period, n)
    df.to_parquet(f"{RAW}/claims/claims_{period}.parquet", index=False)
    total_written += len(df)
    g = df.groupby("cpt_code").agg(
        procedure_count=("claim_id", "size"),
        unique_members=("member_id", "nunique"),
        total_allowed=("allowed_amount", "sum"),
        total_paid=("paid_amount", "sum"),
    ).reset_index()
    g["year_month"] = str(period)
    claims_agg_parts.append(g)

claims_agg = pd.concat(claims_agg_parts, ignore_index=True)
rep.h("fact_claims").kv("rows_written", f"{total_written:,}").kv("monthly_files", len(MONTHS)).kv(
    "path", f"{RAW}/claims/claims_YYYY-MM.parquet")

# COMMAND ----------

# MAGIC %md ## fact_prior_auth — ~40K requests with gap-specific denial / appeal / regional logic

# COMMAND ----------

N_PA = 40_000
# sample PA cpts from PA-required EBCBS cpts, weighted by frequency
pa_pool = np.array([c for c in cpt_codes if c in set(ebcbs_pa_cpts)])
pa_freq = np.array([cpt_df.set_index("cpt_code")["freq_weight"].to_dict()[c] for c in pa_pool], dtype=float)
pa_probs = pa_freq / pa_freq.sum()

pa_codes = rng.choice(pa_pool, size=N_PA, p=pa_probs)
pa_regions = rng.choice(REGIONS, size=N_PA, p=REGION_W)
pa_month = rng.choice(len(MONTHS), size=N_PA)
pa_req_date = np.array([MONTHS[m].start_time.to_datetime64() for m in pa_month]) + rng.integers(0, 27, N_PA).astype("timedelta64[D]")

# base denial ~12%; SPINE ~35% + high appeals; KNEE ~5% (permissive); CARD varies by region
CARD_REGION_DENIAL = {"Rochester": 0.10, "Central NY": 0.38, "Southern Tier": 0.22, "Utica-Mohawk": 0.41, "Finger Lakes": 0.15}
spine_set, knee_set, card_set = set(SPINE), set(KNEE), set(CARD)

denial_p = np.full(N_PA, 0.12)
for i in range(N_PA):
    c = pa_codes[i]
    if c in spine_set:
        denial_p[i] = 0.35
    elif c in knee_set:
        denial_p[i] = 0.05
    elif c in card_set:
        denial_p[i] = CARD_REGION_DENIAL[pa_regions[i]]

roll = rng.random(N_PA)
pending = rng.random(N_PA) < 0.05
denied = (roll < denial_p) & ~pending
approved = ~denied & ~pending
decision = np.where(pending, "pending", np.where(denied, "denied", "approved"))

DENIAL_REASONS = ["Not medically necessary", "Insufficient documentation", "Criteria not met",
                  "Experimental/investigational", "Conservative therapy not documented"]
denial_reason = np.where(denied, rng.choice(DENIAL_REASONS, size=N_PA), None)
# spine appeals high (~60% of denials), others ~25%
appeal_base = np.where(np.isin(pa_codes, SPINE), 0.60, 0.25)
appeal_flag = denied & (rng.random(N_PA) < appeal_base)
decision_date = np.where(pending, np.datetime64("NaT"),
                         pa_req_date + rng.integers(2, 21, N_PA).astype("timedelta64[D]"))

pa_df = pd.DataFrame({
    "pa_id": [f"PA-{i:08d}" for i in range(N_PA)],
    "member_id": np.array(["M%06d" % i for i in rng.integers(0, N_MEMBERS, N_PA)]),
    "provider_id": np.array(["PR%05d" % i for i in rng.integers(0, N_PROVIDERS, N_PA)]),
    "cpt_code": pa_codes,
    "policy_id": np.array([cpt_to_policy.get(c) for c in pa_codes], dtype=object),
    "request_date": pd.to_datetime(pa_req_date),
    "decision": decision,
    "decision_date": pd.to_datetime(decision_date),
    "denial_reason": denial_reason,
    "appeal_flag": appeal_flag,
    "region": pa_regions,
    "year_month": [str(MONTHS[m]) for m in pa_month],
})
pa_df.to_parquet(f"{RAW}/prior_auth/fact_prior_auth.parquet", index=False)
rep.h("fact_prior_auth").kv("rows", f"{len(pa_df):,}").kv("approved", int(approved.sum())).kv(
    "denied", int(denied.sum())).kv("pending", int(pending.sum())).kv("appeals", int(appeal_flag.sum()))

# COMMAND ----------

# MAGIC %md ## fact_utilization — CPT × month, aggregated from claims + PA (consistent)

# COMMAND ----------

pa_agg = pa_df.groupby(["cpt_code", "year_month"]).agg(
    pa_count=("pa_id", "size"),
    denied_count=("decision", lambda s: (s == "denied").sum()),
).reset_index()

util = claims_agg.merge(pa_agg, on=["cpt_code", "year_month"], how="left")
util["pa_count"] = util["pa_count"].fillna(0)
util["denied_count"] = util["denied_count"].fillna(0)
util["avg_cost_per_procedure"] = np.round(util["total_allowed"] / util["procedure_count"], 2)
util["prior_auth_rate"] = np.round(np.minimum(util["pa_count"] / util["procedure_count"], 1.0), 4)
util["denial_rate"] = np.round(np.where(util["pa_count"] > 0, util["denied_count"] / util["pa_count"], 0.0), 4)
util["total_allowed"] = np.round(util["total_allowed"], 2)
util["total_paid"] = np.round(util["total_paid"], 2)
util = util[["cpt_code", "year_month", "procedure_count", "unique_members", "total_allowed",
             "total_paid", "avg_cost_per_procedure", "prior_auth_rate", "denial_rate"]]
util.to_parquet(f"{RAW}/utilization/fact_utilization.parquet", index=False)
rep.h("fact_utilization").kv("rows", f"{len(util):,}").kv("grain", "cpt_code × year_month")

# COMMAND ----------

# MAGIC %md ## Gap verification — prove the 3 seeded patterns are present

# COMMAND ----------

rep.h("GAP 1 — Knee arthroscopy (overly permissive)")
ebcbs_knee = set(pol_df[(pol_df.payer == "EBCBS") & (pol_df.policy_id == GAP_KNEE)].iloc[0]["cpt_codes_covered"])
excl_counts = {}
for c in KNEE_EBCBS_EXCLUSIVE:
    n_excl = sum(1 for p in PAYERS if p != "EBCBS" and c not in set(
        pol_df[(pol_df.payer == p) & (pol_df.policy_id == f"P-2024-KNEE-{PAYER_SUFFIX[p]}")].iloc[0]["cpt_codes_covered"]))
    excl_counts[c] = n_excl
rep.kv("EBCBS knee CPTs covered", len(ebcbs_knee))
rep.kv("CPTs excluded by >=3 of 4 competitors", ", ".join(f"{c}({n}/4)" for c, n in excl_counts.items()))
knee_dr = util[util.cpt_code.isin(KNEE)]["denial_rate"].mean()
rep.kv("avg knee PA denial rate", f"{knee_dr:.3f}  (low → permissive)")

rep.h("GAP 2 — Spinal fusion (overly restrictive)")
spine_pa = pa_df[pa_df.cpt_code.isin(SPINE)]
base_pa = pa_df[~pa_df.cpt_code.isin(SPINE + KNEE + CARD)]
rep.kv("spine denial rate", f"{(spine_pa.decision=='denied').mean():.3f}")
rep.kv("baseline denial rate", f"{(base_pa.decision=='denied').mean():.3f}")
rep.kv("spine appeal rate (of denials)", f"{spine_pa[spine_pa.decision=='denied']['appeal_flag'].mean():.3f}")

rep.h("GAP 3 — Cardiac imaging (ambiguous → regional variance)")
card_pa = pa_df[pa_df.cpt_code.isin(CARD)]
by_region = card_pa.groupby("region")["decision"].apply(lambda s: round((s == "denied").mean(), 3))
rep.table(by_region.reset_index().rename(columns={"decision": "denial_rate"}), n=10)
rep.kv("regional denial-rate spread", f"{by_region.max()-by_region.min():.3f}  (high → inconsistent)")

# COMMAND ----------

rep.h("Raw landing summary")
rep.kv("volume_root", RAW)
for sub in ["cpt", "policies", "competitor_policies", "claims", "prior_auth", "utilization"]:
    files = [f.name for f in dbutils.fs.ls(f"{RAW}/{sub}")]
    rep.kv(sub, f"{len(files)} file(s)")
path = rep.save()
dbutils.notebook.exit(f"STEP1_OK claims={total_written} policies={len(pol_df)} pa={len(pa_df)} util={len(util)} evidence={path}")
