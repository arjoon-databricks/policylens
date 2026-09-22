#!/usr/bin/env python3
"""Build PolicyLens FE Bar submission deck — 12 slides, Databricks dark theme."""
import json, subprocess, sys

PRES_ID = "1rm7bVjmwpJm9V0Dq8oEM0eA5gwH_C74xKYnYlG8mxMs"
QUOTA   = "gcp-sandbox-field-eng"
INCH    = 914400
W       = 9144000   # 10"
H       = 5143125   # 5.625"

# ── brand ──────────────────────────────────────────────────────────────────
NAVY    = {"red": 0.071, "green": 0.165, "blue": 0.271}   # #122A45
RED     = {"red": 1.0,   "green": 0.212, "blue": 0.129}   # #FF3621
ORANGE  = {"red": 1.0,   "green": 0.439, "blue": 0.200}   # #FF7033
YELLOW  = {"red": 0.984, "green": 0.702, "blue": 0.000}   # #FBB300
WHITE   = {"red": 1.0,   "green": 1.0,   "blue": 1.0}
LGRAY   = {"red": 0.78,  "green": 0.82,  "blue": 0.87}
MGRAY   = {"red": 0.45,  "green": 0.50,  "blue": 0.56}

def tok():
    return subprocess.check_output(
        ["python3", "/Users/arjoon.jeyapaalan/.vibe/marketplace/plugins/"
         "fe-google-tools/skills/google-auth/resources/google_auth.py","token"],
        text=True).strip()

def batch(requests):
    t = tok()
    body = json.dumps({"requests": requests})
    r = subprocess.run([
        "curl","-s","-X","POST",
        f"https://slides.googleapis.com/v1/presentations/{PRES_ID}:batchUpdate",
        "-H",f"Authorization: Bearer {t}",
        "-H",f"x-goog-user-project: {QUOTA}",
        "-H","Content-Type: application/json",
        "-d",body
    ], capture_output=True, text=True)
    d = json.loads(r.stdout)
    if "error" in d:
        print("ERROR:", json.dumps(d["error"], indent=2))
        sys.exit(1)
    return d

def emu(inches): return int(inches * INCH)

def bg(page_id, color):
    return {"updatePageProperties":{
        "objectId": page_id,
        "pageProperties":{"pageBackgroundFill":{"solidFill":{"color":{"rgbColor":color}}}},
        "fields":"pageBackgroundFill"
    }}

def box(page_id, oid, x, y, w, h):
    return {"createShape":{
        "objectId": oid,
        "shapeType":"TEXT_BOX",
        "elementProperties":{
            "pageObjectId": page_id,
            "size":{"width":{"magnitude":emu(w),"unit":"EMU"},
                    "height":{"magnitude":emu(h),"unit":"EMU"}},
            "transform":{"scaleX":1,"scaleY":1,
                         "translateX":emu(x),"translateY":emu(y),"unit":"EMU"}
        }
    }}

def rect(page_id, oid, x, y, w, h, color, alpha=1.0):
    return {"createShape":{
        "objectId": oid,
        "shapeType":"RECTANGLE",
        "elementProperties":{
            "pageObjectId": page_id,
            "size":{"width":{"magnitude":emu(w),"unit":"EMU"},
                    "height":{"magnitude":emu(h),"unit":"EMU"}},
            "transform":{"scaleX":1,"scaleY":1,
                         "translateX":emu(x),"translateY":emu(y),"unit":"EMU"}
        }
    }}, {"updateShapeProperties":{
        "objectId": oid,
        "shapeProperties":{"shapeBackgroundFill":{"solidFill":{
            "color":{"rgbColor":color},"alpha":alpha
        }},"outline":{"propertyState":"NOT_RENDERED"}},
        "fields":"shapeBackgroundFill,outline"
    }}

ALIGN_MAP = {"LEFT":"START","CENTER":"CENTER","RIGHT":"END","START":"START","END":"END"}

def txt(oid, text, sz=14, bold=False, color=WHITE, align="LEFT", idx=0):
    style = {"fontSize":{"magnitude":sz,"unit":"PT"},
             "foregroundColor":{"opaqueColor":{"rgbColor":color}},
             "bold": bold,
             "fontFamily":"Inter"}
    api_align = ALIGN_MAP.get(align, "START")
    return [
        {"insertText":{"objectId":oid,"text":text,"insertionIndex":idx}},
        {"updateTextStyle":{"objectId":oid,"textRange":{"type":"ALL"},"style":style,
                            "fields":"fontSize,foregroundColor,bold,fontFamily"}},
        {"updateParagraphStyle":{"objectId":oid,"textRange":{"type":"ALL"},
                                 "style":{"alignment":api_align,"lineSpacing":140,
                                          "spaceAbove":{"magnitude":0,"unit":"PT"},
                                          "spaceBelow":{"magnitude":4,"unit":"PT"}},
                                 "fields":"alignment,lineSpacing,spaceAbove,spaceBelow"}}
    ]

def add_slide(insert_index=None):
    req = {"createSlide":{}}
    if insert_index is not None:
        req["createSlide"]["insertionIndex"] = insert_index
    return req

# ── Step 1: slide IDs already exist ─────────────────────────────────────────
slide_ids = [
    "p",
    "SLIDES_API23336363_0",
    "SLIDES_API23336363_3",
    "SLIDES_API23336363_6",
    "SLIDES_API23336363_9",
    "SLIDES_API23336363_12",
    "SLIDES_API23336363_15",
    "SLIDES_API23336363_18",
    "SLIDES_API23336363_21",
    "SLIDES_API23336363_24",
    "SLIDES_API23336363_27",
    "SLIDES_API23336363_30",
]
print("Slide IDs:", slide_ids)

# ── Step 2: build each slide ─────────────────────────────────────────────────

all_reqs = []

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1: TITLE
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[0]
all_reqs.append(bg(s, NAVY))
# red top bar
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.08, RED)))
# title
all_reqs.append(box(s, f"{s}_title", 0.6, 1.5, 8.8, 1.2))
all_reqs.extend(txt(f"{s}_title", "PolicyLens: Medical Policy\nIntelligence Platform",
                    sz=36, bold=True, color=WHITE, align="LEFT"))
# subtitle
all_reqs.append(box(s, f"{s}_sub", 0.6, 2.85, 8.0, 0.55))
all_reqs.extend(txt(f"{s}_sub",
    "AI-assisted medical-policy review for a Blue Cross Blue Shield plan (EBCBS)",
    sz=16, bold=False, color=LGRAY, align="LEFT"))
# orange accent line
all_reqs.extend(list(rect(s, f"{s}_accent", 0.6, 2.75, 1.4, 0.06, ORANGE)))
# footer bar
all_reqs.extend(list(rect(s, f"{s}_fbar", 0, 4.9, 10, 0.55, {"red":0.04,"green":0.09,"blue":0.16})))
all_reqs.append(box(s, f"{s}_foot", 0.3, 4.93, 9.4, 0.45))
all_reqs.extend(txt(f"{s}_foot",
    "Databricks Field Engineering  ·  Bar Submission  ·  Synthetic data",
    sz=11, bold=False, color=MGRAY, align="LEFT"))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2: EXECUTIVE PROBLEM
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[1]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
# heading
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "The Executive Problem", sz=22, bold=True, color=WHITE))
# problem bullets
all_reqs.append(box(s, f"{s}_body", 0.5, 0.85, 8.8, 1.9))
all_reqs.extend(txt(f"{s}_body",
    "• Medical-policy analysts review 200+ policies annually — by hand\n"
    "• Reviews are disconnected from claims & utilization data\n"
    "• Competitor policy comparisons are slow and inconsistent\n"
    "• Financial impact of policy changes is guesswork",
    sz=14, color=LGRAY))
# orange outcome banner
all_reqs.extend(list(rect(s, f"{s}_banner", 0.4, 2.95, 9.2, 1.85,
                           {"red":0.55,"green":0.22,"blue":0.05}, alpha=0.85)))
all_reqs.extend(list(rect(s, f"{s}_bl", 0.4, 2.95, 0.07, 1.85, ORANGE)))
all_reqs.append(box(s, f"{s}_btext", 0.6, 3.05, 8.9, 1.65))
all_reqs.extend(txt(f"{s}_btext",
    "Review 200 policies in 1 week instead of 12, surface 3× more gaps, and\n"
    "simulate financial impact in real time — redirecting ~2,000 analyst\n"
    "hours per cycle to higher-value work.",
    sz=15, bold=True, color=WHITE))
# footer
all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3: STATUS QUO
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[2]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "The Status Quo — Manual, Fragmented, Slow",
                    sz=22, bold=True, color=WHITE))
all_reqs.append(box(s, f"{s}_sub", 0.5, 0.78, 9.0, 0.32))
all_reqs.extend(txt(f"{s}_sub", "Annual policy review baseline — before PolicyLens",
                    sz=13, color=LGRAY))

# 5 KPI tiles in a row
kpis = [
    ("12\nweeks", "Annual review\ncycle"),
    ("~8 hrs", "Per-policy\ncomparison"),
    ("~2 wks", "Actuarial sim\nturnaround"),
    ("~15", "Gaps found\nper cycle"),
    ("~2,400\nhrs", "Analyst hours\nper cycle"),
]
tile_w = 1.65
tile_gap = 0.175
tile_x0 = 0.35
tile_y  = 1.25
tile_h  = 2.9

for i, (big, label) in enumerate(kpis):
    tx = tile_x0 + i*(tile_w + tile_gap)
    oid_bg  = f"{s}_tile{i}_bg"
    oid_num = f"{s}_tile{i}_num"
    oid_lbl = f"{s}_tile{i}_lbl"
    all_reqs.extend(list(rect(s, oid_bg, tx, tile_y, tile_w, tile_h,
                               {"red":0.04,"green":0.1,"blue":0.18})))
    all_reqs.extend(list(rect(s, f"{s}_tac{i}", tx, tile_y, tile_w, 0.07, ORANGE)))
    all_reqs.append(box(s, oid_num, tx+0.1, tile_y+0.22, tile_w-0.2, 1.4))
    all_reqs.extend(txt(oid_num, big, sz=28, bold=True, color=ORANGE, align="CENTER"))
    all_reqs.append(box(s, oid_lbl, tx+0.08, tile_y+1.75, tile_w-0.16, 1.0))
    all_reqs.extend(txt(oid_lbl, label, sz=11, color=LGRAY, align="CENTER"))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4: WHAT WE BUILT — architecture flow
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[3]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "What We Built — One Connected Data Journey",
                    sz=22, bold=True, color=WHITE))

# Flow boxes
flow = [
    ("Lakeflow\nIngest", ORANGE),
    ("Unity\nCatalog", {"red":0.4,"green":0.6,"blue":1.0}),
    ("Gold\nFeatures", {"red":0.2,"green":0.7,"blue":0.5}),
    ("ML · Vector\nSearch · Metric", {"red":0.7,"green":0.4,"blue":0.9}),
    ("PolicyLens\nCopilot + Genie", RED),
    ("Command\nCenter App", YELLOW),
]
bw = 1.35; bh = 1.05; by = 1.1; bx0 = 0.22; bgap = 0.12
for i,(lbl,col) in enumerate(flow):
    bx = bx0 + i*(bw+bgap)
    oid_b = f"{s}_fb{i}"
    oid_t = f"{s}_ft{i}"
    all_reqs.extend(list(rect(s, oid_b, bx, by, bw, bh, col, alpha=0.25)))
    all_reqs.extend(list(rect(s, f"{s}_fbt{i}", bx, by, bw, 0.06, col)))
    all_reqs.append(box(s, oid_t, bx+0.06, by+0.1, bw-0.12, bh-0.15))
    all_reqs.extend(txt(oid_t, lbl, sz=11, bold=True, color=WHITE, align="CENTER"))
    if i < len(flow)-1:
        ax = bx + bw + 0.01; ay = by + bh/2 - 0.12
        all_reqs.append(box(s, f"{s}_arr{i}", ax, ay, bgap+0.03, 0.24))
        all_reqs.extend(txt(f"{s}_arr{i}", "→", sz=14, bold=True,
                            color=ORANGE, align="CENTER"))

# Lakebase label underneath
all_reqs.extend(list(rect(s, f"{s}_lb_bg", 0.22, 2.35, 9.35, 0.45,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.append(box(s, f"{s}_lb_txt", 0.35, 2.38, 9.1, 0.38))
all_reqs.extend(txt(f"{s}_lb_txt",
    "Lakebase serving the app  ·  All six Databricks-native layers, integrated end-to-end",
    sz=11, color=LGRAY, align="CENTER"))

# caption
all_reqs.append(box(s, f"{s}_cap", 0.5, 2.95, 9.0, 1.85))
all_reqs.extend(txt(f"{s}_cap",
    "One platform, six layers:\n"
    "• Lakeflow — declarative ingestion, Auto Loader, bronze→silver DQ expectations\n"
    "• Unity Catalog — lineage, column masking on member PII, row-level security\n"
    "• Gold Features — ML-ready curated tables\n"
    "• ML · Vector Search · Metric View — LightGBM impact model, RAG, governed metrics\n"
    "• PolicyLens Copilot (Claude / FMA) + Genie — agent loop + NL self-serve\n"
    "• Command Center App — Databricks Apps, Lakebase-backed",
    sz=12, color=LGRAY))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5: DATA FOUNDATION & GOVERNANCE
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[4]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Show — Data Foundation & Governance",
                    sz=22, bold=True, color=WHITE))

# left column: ingestion
all_reqs.extend(list(rect(s, f"{s}_lbg", 0.4, 0.85, 4.45, 3.75,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_lac", 0.4, 0.85, 4.45, 0.06, ORANGE)))
all_reqs.append(box(s, f"{s}_lh", 0.55, 0.95, 4.1, 0.4))
all_reqs.extend(txt(f"{s}_lh", "Lakeflow Pipeline", sz=14, bold=True, color=ORANGE))
all_reqs.append(box(s, f"{s}_lb", 0.55, 1.42, 4.15, 3.0))
all_reqs.extend(txt(f"{s}_lb",
    "~2M synthetic claims + medical policies,\n"
    "prior-auth & utilization records ingested\n"
    "via Declarative Pipeline\n\n"
    "Auto Loader → Bronze → Silver\n"
    "  · Data-quality expectations on every layer\n"
    "  · Streaming-ready, incremental by default\n\n"
    "3 realistic policy gaps seeded:\n"
    "  · Knee arthroscopy (overly permissive)\n"
    "  · Spinal fusion (overly restrictive)\n"
    "  · Cardiac imaging (ambiguous language)",
    sz=12, color=LGRAY))

# right column: governance
all_reqs.extend(list(rect(s, f"{s}_rbg", 5.15, 0.85, 4.45, 3.75,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_rac", 5.15, 0.85, 4.45, 0.06,
                           {"red":0.4,"green":0.6,"blue":1.0})))
all_reqs.append(box(s, f"{s}_rh", 5.3, 0.95, 4.1, 0.4))
all_reqs.extend(txt(f"{s}_rh", "Unity Catalog Governance",
                    sz=14, bold=True,
                    color={"red":0.6,"green":0.78,"blue":1.0}))
all_reqs.append(box(s, f"{s}_rb", 5.3, 1.42, 4.15, 3.0))
all_reqs.extend(txt(f"{s}_rb",
    "End-to-end data lineage — column to\n"
    "dashboard, automatically tracked\n\n"
    "Column masking on member PII:\n"
    "  · member_id, dob, zip masked for\n"
    "    non-privileged analysts\n\n"
    "Row-level security:\n"
    "  · Analysts see only their region's\n"
    "    claims unless VP+ role\n\n"
    "Audit trail for all policy edits\n"
    "and review-case state changes",
    sz=12, color=LGRAY))

all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6: ML INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[5]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Show — ML Intelligence", sz=22, bold=True, color=WHITE))

# model metrics box (left)
all_reqs.extend(list(rect(s, f"{s}_mbg", 0.4, 0.85, 4.45, 2.15,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_mac", 0.4, 0.85, 4.45, 0.06, ORANGE)))
all_reqs.append(box(s, f"{s}_mh", 0.55, 0.95, 4.1, 0.38))
all_reqs.extend(txt(f"{s}_mh", "Financial-Impact Model (LightGBM)",
                    sz=13, bold=True, color=ORANGE))
all_reqs.append(box(s, f"{s}_mb", 0.55, 1.38, 4.1, 1.45))
all_reqs.extend(txt(f"{s}_mb",
    "Predicts annualized financial impact of\n"
    "adding / removing CPT codes\n\n"
    "  R²   ≈  0.998\n"
    "  MAE  ≈  $151K / month\n"
    "  SHAP explanations for every prediction",
    sz=12, color=LGRAY))

# gap detection box (right)
all_reqs.extend(list(rect(s, f"{s}_gbg", 5.15, 0.85, 4.45, 2.15,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_gac", 5.15, 0.85, 4.45, 0.06,
                           {"red":0.2,"green":0.7,"blue":0.5})))
all_reqs.append(box(s, f"{s}_gh", 5.3, 0.95, 4.1, 0.38))
all_reqs.extend(txt(f"{s}_gh", "Rule-Based Gap Detection",
                    sz=13, bold=True,
                    color={"red":0.3,"green":0.85,"blue":0.6}))
all_reqs.append(box(s, f"{s}_gb", 5.3, 1.38, 4.1, 1.45))
all_reqs.extend(txt(f"{s}_gb",
    "All 3 seeded gaps surfaced:\n\n"
    "  ·  Knee arthroscopy — overly permissive\n"
    "     (broad prior-auth approval pattern)\n"
    "  ·  Spinal fusion — overly restrictive\n"
    "     (denial rate 2× industry benchmark)\n"
    "  ·  Cardiac imaging — ambiguous language\n"
    "     (regional denial variance 9.8–38.4%)",
    sz=12, color=LGRAY))

# insight box bottom
all_reqs.extend(list(rect(s, f"{s}_ibg", 0.4, 3.2, 9.2, 1.5,
                           {"red":0.04,"green":0.12,"blue":0.20})))
all_reqs.extend(list(rect(s, f"{s}_iac", 0.4, 3.2, 0.07, 1.5, YELLOW)))
all_reqs.append(box(s, f"{s}_ib", 0.6, 3.3, 8.85, 1.28))
all_reqs.extend(txt(f"{s}_ib",
    "SHAP outputs explain which CPT-code clusters and prior-auth patterns drive each "
    "prediction — giving analysts the 'why' behind every financial-impact estimate. "
    "Budget-exposure context, not a recommendation to change coverage based on cost.",
    sz=13, color=WHITE))
all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7: THE AGENT LOOP
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[6]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Show — PolicyLens Copilot Agent Loop",
                    sz=22, bold=True, color=WHITE))

# centre: agent core
all_reqs.extend(list(rect(s, f"{s}_core", 3.5, 1.0, 3.0, 1.25,
                           {"red":0.55,"green":0.1,"blue":0.05}, alpha=0.9)))
all_reqs.extend(list(rect(s, f"{s}_coretop", 3.5, 1.0, 3.0, 0.06, RED)))
all_reqs.append(box(s, f"{s}_ct", 3.62, 1.08, 2.76, 1.05))
all_reqs.extend(txt(f"{s}_ct",
    "PolicyLens Copilot\nClaude (FMA) + RAG\n+ 6 Governed Tools",
    sz=12, bold=True, color=WHITE, align="CENTER"))

# tools box left
tools = [
    "compare_policies(p1, p2)",
    "get_utilization_data(cpt, region)",
    "analyze_prior_auth(policy_id)",
    "simulate_financial_impact(cpt_delta)",
    "get_industry_guidelines(cpt)",
    "create_review_case(policy_id, rec)",
]
all_reqs.extend(list(rect(s, f"{s}_tbg", 0.25, 1.0, 3.0, 2.9,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_tac", 0.25, 1.0, 3.0, 0.06, ORANGE)))
all_reqs.append(box(s, f"{s}_th", 0.38, 1.1, 2.7, 0.35))
all_reqs.extend(txt(f"{s}_th", "Governed Tools", sz=12, bold=True, color=ORANGE))
all_reqs.append(box(s, f"{s}_tb", 0.32, 1.5, 2.88, 2.28))
all_reqs.extend(txt(f"{s}_tb", "\n".join(f"· {t}" for t in tools),
                    sz=10, color=LGRAY))

# guardrails box right
all_reqs.extend(list(rect(s, f"{s}_gbg", 6.75, 1.0, 2.95, 2.9,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_gac", 6.75, 1.0, 2.95, 0.06,
                           {"red":0.2,"green":0.7,"blue":0.5})))
all_reqs.append(box(s, f"{s}_gh", 6.88, 1.1, 2.7, 0.35))
all_reqs.extend(txt(f"{s}_gh", "Agent Scope & Guardrails",
                    sz=12, bold=True,
                    color={"red":0.3,"green":0.85,"blue":0.6}))
all_reqs.append(box(s, f"{s}_gb", 6.82, 1.5, 2.78, 2.28))
all_reqs.extend(txt(f"{s}_gb",
    "Scoped to policy admin\nquestions only\n\n"
    "Declines individual\nclinical / patient-care\nquestions\n\n"
    "Never frames value as\ncost savings — always\nadmin efficiency or\nbetter-informed decisions\n\n"
    "Vector Search RAG over\npolicy document corpus",
    sz=10, color=LGRAY))

# flow labels
all_reqs.append(box(s, f"{s}_al", 3.5, 2.35, 3.0, 0.28))
all_reqs.extend(txt(f"{s}_al", "↓  opens review cases in Lakebase",
                    sz=10, color=LGRAY, align="CENTER"))

# bottom outcome
all_reqs.extend(list(rect(s, f"{s}_obar", 0.4, 4.1, 9.2, 0.72,
                           {"red":0.04,"green":0.12,"blue":0.20})))
all_reqs.extend(list(rect(s, f"{s}_obac", 0.4, 4.1, 0.07, 0.72, RED)))
all_reqs.append(box(s, f"{s}_ot", 0.6, 4.17, 8.85, 0.58))
all_reqs.extend(txt(f"{s}_ot",
    "Compares EBCBS vs competitors · grounds in utilization/prior-auth/ML data · "
    "drafts recommendations · opens review cases in Lakebase",
    sz=12, color=WHITE))
all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 8: GENIE + THE APP
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[7]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Show — Genie + The Command Center App",
                    sz=22, bold=True, color=WHITE))

# genie panel left
all_reqs.extend(list(rect(s, f"{s}_gbg", 0.35, 0.85, 4.5, 3.1,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_gac", 0.35, 0.85, 4.5, 0.06,
                           {"red":0.984,"green":0.702,"blue":0.0})))
all_reqs.append(box(s, f"{s}_gh", 0.5, 0.95, 4.2, 0.38))
all_reqs.extend(txt(f"{s}_gh", "Genie — Natural Language Self-Serve",
                    sz=13, bold=True, color=YELLOW))
all_reqs.append(box(s, f"{s}_gb", 0.5, 1.38, 4.25, 2.42))
all_reqs.extend(txt(f"{s}_gb",
    "Governed Metric View powers NL queries\n"
    "without raw table access\n\n"
    'Example: "Show denial rate by region\n'
    '          for policy P-2024-CARD-01"\n\n'
    "Result:\n"
    "  · Rochester:     9.8% denial rate\n"
    "  · Syracuse:    17.2%\n"
    "  · Albany:      24.6%\n"
    "  · Utica-Mohawk:  38.4%  ← gap exposed\n\n"
    "Ambiguous-criteria gap surfaces\nautomatically via variance signal",
    sz=11, color=LGRAY))

# app panel right
all_reqs.extend(list(rect(s, f"{s}_abg", 5.15, 0.85, 4.5, 3.1,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_aac", 5.15, 0.85, 4.5, 0.06, RED)))
all_reqs.append(box(s, f"{s}_ah", 5.3, 0.95, 4.2, 0.38))
all_reqs.extend(txt(f"{s}_ah", "PolicyLens Command Center App",
                    sz=13, bold=True, color=RED))
all_reqs.append(box(s, f"{s}_ab", 5.3, 1.38, 4.25, 2.42))
all_reqs.extend(txt(f"{s}_ab",
    "Databricks App + Lakebase backend\n\n"
    "Modules:\n"
    "  · Executive KPI tiles\n"
    "  · Policy dashboard & search\n"
    "  · EBCBS vs. competitor comparison\n"
    "  · Real-time financial simulator\n"
    "  · Embedded Genie copilot\n"
    "  · Review-case management\n\n"
    "Sub-second response — Lakebase\n"
    "Postgres serves app queries directly",
    sz=11, color=LGRAY))

all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 9: IMPACT TABLE
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[8]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Impact — Before vs. After", sz=22, bold=True, color=WHITE))

# Table: 6 rows x 3 cols
# We'll build this with rectangles and text boxes for full control
headers = ["KPI", "Manual Baseline", "With PolicyLens"]
rows = [
    ("Annual review cycle",       "~12 weeks",         "< 1 week"),
    ("Time per policy comparison", "~8 hours",          "~30 minutes"),
    ("Financial simulation",      "~2 weeks",          "Real-time"),
    ("Policy gaps per cycle",     "~15",               "~50"),
    ("Analyst hours per cycle",   "~2,400",            "~400  (~2,000 redirected)"),
]
col_widths = [3.8, 2.5, 2.8]
col_x = [0.4, 4.3, 6.9]
row_h = 0.47
row_y0 = 0.85

# header row
for ci, (hdr, cw, cx) in enumerate(zip(headers, col_widths, col_x)):
    hcol = NAVY if ci==0 else RED if ci==2 else {"red":0.15,"green":0.18,"blue":0.26}
    all_reqs.extend(list(rect(s, f"{s}_h{ci}", cx, row_y0, cw, row_h+0.05, RED if ci==2 else {"red":0.15,"green":0.22,"blue":0.35})))
    all_reqs.append(box(s, f"{s}_ht{ci}", cx+0.1, row_y0+0.05, cw-0.2, row_h-0.08))
    all_reqs.extend(txt(f"{s}_ht{ci}", hdr, sz=13, bold=True, color=WHITE, align="CENTER"))

# data rows
for ri, (kpi, before, after) in enumerate(rows):
    ry = row_y0 + (ri+1)*(row_h+0.04)
    stripe = {"red":0.04,"green":0.1,"blue":0.18} if ri%2==0 else {"red":0.06,"green":0.14,"blue":0.22}
    for ci, (val, cw, cx) in enumerate(zip([kpi,before,after], col_widths, col_x)):
        all_reqs.extend(list(rect(s, f"{s}_r{ri}c{ci}", cx, ry, cw, row_h, stripe)))
        tcol = LGRAY if ci<2 else {"red":0.3,"green":0.95,"blue":0.6}
        tsz = 12 if ci<2 else 12
        all_reqs.append(box(s, f"{s}_rt{ri}{ci}", cx+0.1, ry+0.05, cw-0.2, row_h-0.1))
        all_reqs.extend(txt(f"{s}_rt{ri}{ci}", val, sz=tsz, color=tcol,
                            align="LEFT" if ci==0 else "CENTER"))

# headline
all_reqs.extend(list(rect(s, f"{s}_hl", 0.4, 4.3, 9.2, 0.55,
                           {"red":0.04,"green":0.12,"blue":0.20})))
all_reqs.extend(list(rect(s, f"{s}_hlac", 0.4, 4.3, 0.07, 0.55, ORANGE)))
all_reqs.append(box(s, f"{s}_hlt", 0.6, 4.36, 8.85, 0.42))
all_reqs.extend(txt(f"{s}_hlt",
    "A 12-week manual cycle becomes a < 1-week governed, AI-assisted workflow.",
    sz=13, bold=True, color=WHITE))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 10: VALUE FOR BOTH PERSONAS
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[9]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "Value for Both Personas", sz=22, bold=True, color=WHITE))

# Executive left
all_reqs.extend(list(rect(s, f"{s}_ebg", 0.4, 0.85, 4.45, 3.85,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_eac", 0.4, 0.85, 4.45, 0.07, RED)))
all_reqs.append(box(s, f"{s}_et", 0.55, 0.97, 4.1, 0.42))
all_reqs.extend(txt(f"{s}_et", "VP Medical Policy / CMO",
                    sz=14, bold=True, color=RED))
all_reqs.append(box(s, f"{s}_eb", 0.55, 1.45, 4.15, 3.0))
all_reqs.extend(txt(f"{s}_eb",
    "Policy competitiveness\n"
    "  Stay current with competitor policies,\n"
    "  reviewed continuously not annually\n\n"
    "Fewer appeals & admin overhead\n"
    "  Clear, defensible policy language\n"
    "  reduces ambiguity-driven denials\n\n"
    "Admin efficiency\n"
    "  ~2,000 analyst hours/cycle redirected\n"
    "  to clinical quality & member programs\n\n"
    "Better-informed decisions\n"
    "  Grounded in plan's own utilization data,\n"
    "  not guesswork",
    sz=11, color=LGRAY))

# Domain owner right
all_reqs.extend(list(rect(s, f"{s}_dbg", 5.15, 0.85, 4.45, 3.85,
                           {"red":0.04,"green":0.1,"blue":0.18})))
all_reqs.extend(list(rect(s, f"{s}_dac", 5.15, 0.85, 4.45, 0.07, ORANGE)))
all_reqs.append(box(s, f"{s}_dt", 5.3, 0.97, 4.1, 0.42))
all_reqs.extend(txt(f"{s}_dt", "Medical Policy Analyst Lead",
                    sz=14, bold=True, color=ORANGE))
all_reqs.append(box(s, f"{s}_db", 5.3, 1.45, 4.15, 3.0))
all_reqs.extend(txt(f"{s}_db",
    "Accurate comparisons in ~30 min\n"
    "  Structured side-by-side with\n"
    "  competitor data, not manual search\n\n"
    "Real-time financial simulation\n"
    "  Instant impact estimate for any\n"
    "  CPT-code change, with SHAP context\n\n"
    "Recommendations grounded in data\n"
    "  Plan's own claims, utilization &\n"
    "  prior-auth patterns, not anecdote\n\n"
    "Review cases auto-opened in Lakebase\n"
    "  No manual tracking spreadsheet",
    sz=11, color=LGRAY))

all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 11: HOW IT SCALES
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[10]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.06, RED)))
all_reqs.append(box(s, f"{s}_h", 0.5, 0.15, 9.0, 0.55))
all_reqs.extend(txt(f"{s}_h", "How It Scales — A Reusable Governed Pattern",
                    sz=22, bold=True, color=WHITE))

# anchor box
all_reqs.extend(list(rect(s, f"{s}_anc", 0.4, 0.82, 9.2, 0.85,
                           {"red":0.04,"green":0.12,"blue":0.20})))
all_reqs.extend(list(rect(s, f"{s}_anl", 0.4, 0.82, 0.07, 0.85, ORANGE)))
all_reqs.append(box(s, f"{s}_ant", 0.6, 0.88, 8.85, 0.72))
all_reqs.extend(txt(f"{s}_ant",
    "PolicyLens is built on a governed pattern: one lakehouse (Unity Catalog), "
    "Genie for self-serve, specialized agents composed over governed data. "
    "The same pattern extends across payer workflows.",
    sz=13, color=WHITE))

# 3 extension tiles
ext = [
    ("Payment Integrity",
     "Detect billing anomalies &\noverpayments using the same\nGold features + ML model pattern.\nClaims data already governed\nin Unity Catalog.",
     ORANGE),
    ("Appeals & Grievances",
     "Agent-assisted case research:\nRAG over policy docs + member\nclaims history. Analysts get a\ndraft response in minutes,\nnot days.",
     {"red":0.4,"green":0.6,"blue":1.0}),
    ("Provider Experience",
     "Self-serve prior-auth status\nvia Genie. Analysts answer\nprovider queries with governed\nmetrics, not manual lookup.",
     {"red":0.2,"green":0.7,"blue":0.5}),
]
tw = 2.85; tgap = 0.18; tx0 = 0.4; ty = 1.88; th = 2.65
for i,(title,body,col) in enumerate(ext):
    tx = tx0 + i*(tw+tgap)
    all_reqs.extend(list(rect(s, f"{s}_ext{i}", tx, ty, tw, th,
                               {"red":0.04,"green":0.1,"blue":0.18})))
    all_reqs.extend(list(rect(s, f"{s}_extac{i}", tx, ty, tw, 0.07, col)))
    all_reqs.append(box(s, f"{s}_exth{i}", tx+0.1, ty+0.14, tw-0.2, 0.4))
    all_reqs.extend(txt(f"{s}_exth{i}", title, sz=13, bold=True, color=WHITE))
    all_reqs.append(box(s, f"{s}_extb{i}", tx+0.1, ty+0.6, tw-0.2, 1.95))
    all_reqs.extend(txt(f"{s}_extb{i}", body, sz=11, color=LGRAY))

all_reqs.extend(list(rect(s, f"{s}_fb", 0, 4.93, 10, 0.22,
                           {"red":0.04,"green":0.09,"blue":0.16})))

# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 12: CLOSE
# ═══════════════════════════════════════════════════════════════════════════
s = slide_ids[11]
all_reqs.append(bg(s, NAVY))
all_reqs.extend(list(rect(s, f"{s}_topbar", 0, 0, 10, 0.08, RED)))

# big statement
all_reqs.append(box(s, f"{s}_stmt", 0.7, 0.9, 8.6, 2.3))
all_reqs.extend(txt(f"{s}_stmt",
    '"PolicyLens turns a 12-week manual cycle into\na governed, AI-assisted workflow:\nbetter-informed policy decisions,\nmade faster, on one Databricks platform."',
    sz=24, bold=True, color=WHITE, align="CENTER"))

# accent
all_reqs.extend(list(rect(s, f"{s}_div", 3.5, 3.3, 3.0, 0.06, ORANGE)))

# 6-layer note
all_reqs.append(box(s, f"{s}_note", 1.0, 3.5, 8.0, 0.7))
all_reqs.extend(txt(f"{s}_note",
    "All six Databricks layers built end-to-end:\n"
    "Lakeflow · Unity Catalog · Lakebase · ML/Gen AI · Genie · Databricks Apps",
    sz=12, color=LGRAY, align="CENTER"))

# small disclaimer
all_reqs.append(box(s, f"{s}_disc", 1.5, 4.25, 7.0, 0.45))
all_reqs.extend(txt(f"{s}_disc",
    "All data synthetic · EBCBS is a code name · FE Bar submission",
    sz=10, color=MGRAY, align="CENTER"))

# Databricks wordmark bar
all_reqs.extend(list(rect(s, f"{s}_fbar", 0, 4.85, 10, 0.55,
                           {"red":0.04,"green":0.09,"blue":0.16})))
all_reqs.append(box(s, f"{s}_ftext", 0.3, 4.88, 9.4, 0.45))
all_reqs.extend(txt(f"{s}_ftext", "DATABRICKS  ·  Field Engineering",
                    sz=13, bold=True, color=RED, align="CENTER"))

# ── fire the mega-batch ─────────────────────────────────────────────────────
print(f"Sending {len(all_reqs)} requests...")
result = batch(all_reqs)
print("Done. Replies:", len(result.get("replies",[])))
print(f"\nPresentation URL: https://docs.google.com/presentation/d/{PRES_ID}/edit")
