"""PolicyLens Command Center — FE Bar demo (Streamlit on Databricks Apps).

All data is SYNTHETIC. The health plan is referred to ONLY as "EBCBS".
Value is framed as admin workflow automation, faster time-to-decision, and
better-informed policy decisions -- NEVER as cost savings. Dollar figures are
budget-exposure / financial-impact context for policy administration.
"""
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data as D
import genie as G
from lakebase import ReviewStore

st.set_page_config(page_title="PolicyLens Command Center", page_icon="🩺",
                   layout="wide", initial_sidebar_state="collapsed")

# --------------------------------------------------------------- styling
PRIMARY = "#0057B8"   # EBCBS blue
ACCENT = "#00A3E0"
INK = "#0B2545"
st.markdown(f"""
<style>
  .stApp {{ background:#F4F7FB; color:{INK}; }}
  #MainMenu, footer {{ visibility:hidden; }}
  /* --- high-contrast hardening: dark ink on light everywhere by default --- */
  .stApp, .stApp p, .stApp li, .stApp label,
  [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
  [data-testid="stHeader"] {{ color:{INK}; }}
  .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color:{INK}; }}
  /* captions / help text a touch lighter but still AA on #F4F7FB */
  [data-testid="stCaptionContainer"], .stApp small,
  [data-testid="stCaptionContainer"] p {{ color:#3B4A5E !important; }}
  /* tab labels */
  .stTabs [data-baseweb="tab"] {{ color:{INK} !important; }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color:{PRIMARY} !important; }}
  /* metrics */
  [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color:#3B4A5E !important; }}
  [data-testid="stMetricValue"] {{ color:{INK} !important; }}
  /* inputs / selects: dark text on white fields */
  .stApp input, .stApp textarea,
  [data-baseweb="select"] div, [data-baseweb="input"] input,
  [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{ color:{INK} !important; }}
  [data-baseweb="select"] {{ background:#fff; }}
  /* dataframe (DOM fallback if not canvas): dark cells on white */
  [data-testid="stDataFrame"] * {{ color:{INK}; }}
  /* expander + alert bodies */
  [data-testid="stExpander"] p, [data-testid="stExpander"] summary {{ color:{INK}; }}
  /* keep hero + pills readable (they define their own colors) */
  .pl-hero, .pl-hero * {{ color:#fff !important; }}
  .pl-hero {{
     background:linear-gradient(120deg,{INK} 0%,{PRIMARY} 55%,{ACCENT} 130%);
     padding:22px 30px; border-radius:16px; color:#fff; margin-bottom:6px;
     box-shadow:0 8px 24px rgba(11,37,69,.18); }}
  .pl-hero h1 {{ margin:0; font-size:30px; font-weight:800; letter-spacing:-.5px; }}
  .pl-hero p {{ margin:6px 0 0; opacity:.92; font-size:14px; }}
  .pl-badge {{ display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35);
     padding:3px 10px; border-radius:999px; font-size:11px; margin-right:8px; }}
  .kpi {{ background:#fff; border:1px solid #E4EBF3; border-radius:14px; padding:16px 18px;
     box-shadow:0 2px 10px rgba(11,37,69,.05); height:100%; }}
  .kpi .lbl {{ font-size:12px; color:#5B6B7F; font-weight:600; text-transform:uppercase; letter-spacing:.4px; }}
  .kpi .now {{ font-size:30px; font-weight:800; color:{PRIMARY}; line-height:1.05; margin-top:6px; }}
  .kpi .was {{ font-size:12px; color:#5B6B7F; margin-top:4px; }}
  .kpi .tag {{ font-size:11px; color:#0A8A5F; font-weight:700; margin-top:8px; }}
  .card {{ background:#fff; border:1px solid #E4EBF3; border-radius:14px; padding:18px 20px;
     box-shadow:0 2px 10px rgba(11,37,69,.05); margin-bottom:14px; }}
  .pill {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:700; }}
  .p-high {{ background:#FDE7E7; color:#C0392B; }}
  .p-med {{ background:#FFF4DE; color:#B7791F; }}
  .p-low {{ background:#E7F5EC; color:#1E8E5A; }}
  .stTabs [data-baseweb="tab-list"] {{ gap:4px; }}
  .stTabs [data-baseweb="tab"] {{ font-weight:600; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pl-hero">
  <h1>🩺 PolicyLens Command Center</h1>
  <p><span class="pl-badge">EBCBS · synthetic demo</span>
     <span class="pl-badge">Medical Policy Intelligence</span>
     Faster, better-informed medical-policy administration on the Databricks Lakehouse.</p>
</div>
""", unsafe_allow_html=True)

SEEDED = {"P-2024-KNEE-01", "P-2024-SPINE-01", "P-2024-CARD-01"}


@st.cache_resource
def get_store():
    return ReviewStore()


def sev_pill(sev):
    cls = {"high": "p-high", "medium": "p-med"}.get(sev, "p-low")
    return f'<span class="pill {cls}">{sev.upper()}</span>'


t1, t2, t3, t4, t5, t6 = st.tabs([
    "📊 Executive KPIs", "📋 Policy Dashboard", "⚖️ Comparison",
    "💵 Financial Simulator", "🤖 Copilot", "🗂️ Review Cases",
])

# ============================================================ 1. KPI tiles
with t1:
    st.markdown("#### Operating-model impact — policy administration workflow")
    st.caption("Target outcomes from automating the medical-policy review workflow. "
               "Value is measured as faster time-to-decision and analyst capacity "
               "redirected to higher-value review — not cost reduction.")
    tiles = [
        ("Annual review cycle", "< 1 week", "was 12 weeks", "~12x faster"),
        ("Time per policy comparison", "30 min", "was 8 hours", "~16x faster"),
        ("Financial-impact simulation", "Real-time", "was 2 weeks", "on-demand"),
        ("Coverage gaps surfaced", "50", "was 15", "+233% visibility"),
        ("Analyst hours / cycle", "~400", "was 2,400", "~2,000 hrs redirected"),
    ]
    cols = st.columns(5)
    for c, (lbl, now, was, tag) in zip(cols, tiles):
        c.markdown(f"""<div class="kpi"><div class="lbl">{lbl}</div>
            <div class="now">{now}</div><div class="was">{was}</div>
            <div class="tag">▲ {tag}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    try:
        pol = D.get_policies()
        gaps = D.get_gap_alerts()
        a, b, c, d = st.columns(4)
        a.metric("EBCBS policies analyzed", len(pol))
        b.metric("Gap alerts detected", len(gaps))
        c.metric("High-severity gaps", int((gaps["severity"] == "high").sum()))
        d.metric("Policies with prior-auth", int(pol["prior_auth_required"].astype(str)
                                                  .str.lower().eq("true").sum()))
    except Exception as e:  # noqa: BLE001
        st.warning(f"Live metrics unavailable: {e}")

    st.caption("Cycle-time and hours figures are illustrative target outcomes for "
               "this demo. Policy/gap counts are live from the governed gold layer.")

# ============================================================ 2. Dashboard
with t2:
    st.markdown("#### EBCBS medical-policy portfolio & detected coverage gaps")
    try:
        pol = D.get_policies()
        gaps = D.get_gap_alerts()
        gap_by_policy = gaps.groupby("policy_id").size().to_dict()

        left, right = st.columns([1, 1])
        with left:
            st.markdown("**Coverage gap alerts** (competitor-benchmarked)")
            for _, g in gaps.iterrows():
                star = " ⭐" if g["policy_id"] in SEEDED else ""
                st.markdown(f"""<div class="card">
                    {sev_pill(g['severity'])} &nbsp;<b>{g['policy_id']}</b>{star}
                    &nbsp;·&nbsp;<span style="color:#5B6B7F">{g['gap_type'].replace('_',' ')}</span>
                    <div style="margin-top:6px;font-size:13px;color:#334">{g['description']}</div>
                    </div>""", unsafe_allow_html=True)
        with right:
            st.markdown("**Denial rate vs. competitor restrictiveness**")
            fig = go.Figure()
            seeded = pol[pol["policy_id"].isin(SEEDED)]
            other = pol[~pol["policy_id"].isin(SEEDED)]
            fig.add_trace(go.Scatter(
                x=other["avg_competitor_restrictiveness"].astype(float),
                y=other["denial_rate"].astype(float), mode="markers",
                marker=dict(size=10, color="#B7C6D9"), name="Other policies",
                text=other["policy_id"]))
            fig.add_trace(go.Scatter(
                x=seeded["avg_competitor_restrictiveness"].astype(float),
                y=seeded["denial_rate"].astype(float), mode="markers+text",
                marker=dict(size=16, color=PRIMARY, line=dict(width=2, color="#fff")),
                name="Featured gaps", text=seeded["policy_id"], textposition="top center"))
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Avg competitor restrictiveness",
                              yaxis_title="EBCBS denial rate", plot_bgcolor="#fff",
                              legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Policy portfolio**")
        show = pol.copy()
        show["gaps"] = show["policy_id"].map(lambda p: gap_by_policy.get(p, 0))
        show["featured"] = show["policy_id"].map(lambda p: "⭐" if p in SEEDED else "")
        st.dataframe(
            show[["featured", "policy_id", "policy_name", "policy_category",
                  "prior_auth_required", "denial_rate", "appeal_rate",
                  "n_exclusive_cpts", "gaps"]],
            use_container_width=True, hide_index=True,
            column_config={
                "denial_rate": st.column_config.NumberColumn("denial_rate", format="%.3f"),
                "appeal_rate": st.column_config.NumberColumn("appeal_rate", format="%.3f"),
            })
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load policy dashboard: {e}")

# ============================================================ 3. Comparison
with t3:
    st.markdown("#### EBCBS vs. Competitor_A–D coverage & criteria")
    try:
        pol = D.get_policies()
        names = pol.set_index("policy_id")["policy_name"].to_dict()
        pid = st.selectbox("Select an EBCBS policy",
                           options=list(names.keys()),
                           format_func=lambda p: f"{p} — {names[p]}"
                           + (" ⭐" if p in SEEDED else ""))
        pname = names[pid]
        comp = D.get_policy_by_name(pname)
        feat = pol[pol["policy_id"] == pid].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("EBCBS denial rate", f"{float(feat['denial_rate'])*100:.1f}%")
        c2.metric("EBCBS appeal rate", f"{float(feat['appeal_rate'])*100:.1f}%")
        c3.metric("EBCBS-exclusive CPTs", int(feat["n_exclusive_cpts"]))
        c4.metric("Competitor restrictiveness",
                  f"{float(feat['avg_competitor_restrictiveness']):.2f}")

        st.markdown("**Coverage & prior-auth by payer**")
        disp = comp.copy()
        disp["payer"] = disp["payer"].map(lambda x: f"⭐ {x}" if x == "EBCBS" else x)
        st.dataframe(disp[["payer", "policy_id", "prior_auth_required",
                           "n_cpts", "cpt_codes"]],
                     use_container_width=True, hide_index=True)

        fig = go.Figure(go.Bar(
            x=comp["payer"], y=comp["n_cpts"].astype(int),
            marker_color=[PRIMARY if p == "EBCBS" else "#B7C6D9" for p in comp["payer"]],
            text=comp["n_cpts"], textposition="outside"))
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                          yaxis_title="# CPT codes covered", plot_bgcolor="#fff",
                          title="Breadth of covered CPT codes")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("EBCBS policy criteria text"):
            ebcbs = comp[comp["payer"] == "EBCBS"]
            st.write(ebcbs.iloc[0]["criteria_text"] if len(ebcbs) else "n/a")
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load comparison: {e}")

# ============================================================ 4. Simulator
with t4:
    st.markdown("#### Financial-impact simulator")
    st.caption("Estimated annualized **budget exposure** of a coverage change, from "
               "ML-predicted allowed amounts. This is decision context for policy "
               "administration — not a cost-savings target.")
    try:
        pol = D.get_policies()
        names = pol.set_index("policy_id")["policy_name"].to_dict()
        cc = st.columns([2, 2, 1])
        pid = cc[0].selectbox("Policy", options=list(names.keys()),
                              format_func=lambda p: f"{p} — {names[p]}",
                              key="sim_pol")
        cpts = D.get_cpts_for_policy(pid)
        if len(cpts):
            cpt_lbl = {r["cpt_code"]: f"{r['cpt_code']} — {r['description']}"
                       for _, r in cpts.iterrows()}
            cpt = cc[1].selectbox("CPT code", options=list(cpt_lbl.keys()),
                                  format_func=lambda c: cpt_lbl[c], key="sim_cpt")
            change = cc[2].selectbox("Change", ["remove", "add"], key="sim_chg")
            if st.button("Simulate impact", type="primary"):
                res = D.simulate_financial_impact(pid, change, cpt)
                if len(res) and pd.notna(res.iloc[0]["predicted_annual_allowed"]):
                    r = res.iloc[0]
                    impact = float(r["estimated_impact"])
                    pred = float(r["predicted_annual_allowed"])
                    m1, m2 = st.columns(2)
                    m1.metric("Predicted annual allowed (this CPT)", f"${pred:,.0f}")
                    m2.metric(f"Est. annual budget-exposure change ({change})",
                              f"${impact:,.0f}",
                              delta=f"{'increase' if impact>0 else 'reduction'} in exposure")
                    st.info(f"Removing/adding **{cpt}** on **{pid}** shifts modeled "
                            f"annual budget exposure by **${impact:,.0f}**. Use as "
                            f"context alongside clinical guidelines when deciding "
                            f"policy coverage.")
                else:
                    st.warning("No prediction available for that CPT.")
            st.markdown("**CPTs in scope for this policy**")
            st.dataframe(cpts, use_container_width=True, hide_index=True,
                         column_config={"annual_allowed": st.column_config.NumberColumn(
                             "annual_allowed", format="$%.0f")})
        else:
            st.warning("No CPT scenarios found for this policy.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not run simulator: {e}")

# ============================================================ 5. Copilot
with t5:
    st.markdown("#### Copilot — ask about EBCBS policies in natural language")
    st.caption("Powered by the governed Genie space over the same synthetic data. "
               "Advises on policy administration only, never clinical decisions. "
               "The first question after an idle period can take up to ~2-3 min "
               "while the serverless warehouse warms up; later questions are fast.")
    examples = [
        "Which policies have the highest gap score vs competitors?",
        "How many policies are more restrictive than competitors?",
        "What is the prior authorization denial rate for knee arthroscopy policies?",
        "Show denial rate by region for policy P-2024-CARD-01",
    ]
    picked = st.selectbox("Pick an example, or type your own below",
                          ["(type my own question below)"] + examples)
    # Use a form so the typed value commits atomically on submit.
    with st.form("copilot_form"):
        typed = st.text_input(
            "Your question",
            placeholder="e.g. Which EBCBS policies are more restrictive than competitors?")
        submitted = st.form_submit_button("Ask Copilot", type="primary")

    if submitted:
        q = typed.strip() if typed and typed.strip() else (
            picked if picked in examples else "")
        if not q:
            st.warning("Type a question or pick an example, then click Ask Copilot.")
        else:
            with st.spinner("Genie is analyzing the governed data (first call after "
                            "idle can take a couple of minutes)..."):
                try:
                    out = G.ask(q)
                except Exception as e:  # noqa: BLE001
                    out = {"status": "ERROR", "error": str(e), "text": "", "sql": None,
                           "columns": None, "rows": None}
            out["question"] = q
            st.session_state["copilot_out"] = out

    # Render persisted result (survives Streamlit reruns).
    out = st.session_state.get("copilot_out")
    if out:
        st.markdown(f"**Q:** {out.get('question','')}")
        if out["status"] == "COMPLETED":
            if out["text"]:
                st.markdown(out["text"])
            if out.get("columns") and out.get("rows"):
                st.dataframe(pd.DataFrame(out["rows"], columns=out["columns"]),
                             use_container_width=True, hide_index=True)
            if not out["text"] and not out.get("rows"):
                st.info("Genie completed but returned no content for this question.")
            if out.get("sql"):
                with st.expander("Generated SQL"):
                    st.code(out["sql"], language="sql")
        else:
            st.error(f"Copilot could not answer ({out['status']}): "
                     f"{out.get('error') or 'no response'}")

# ============================================================ 6. Review cases
with t6:
    st.markdown("#### Policy review cases")
    store = get_store()
    if store.mode == "lakebase":
        st.success("Connected to Lakebase (operational Postgres · policylens-oltp).")
    else:
        st.warning("Lakebase auth unavailable for the app principal — using Delta "
                   f"fallback `{store.mode}` at `{__import__('lakebase').FALLBACK_TABLE}`. "
                   f"({store.detail})")

    st.markdown("**Open a new review case from a detected gap**")
    try:
        gaps = D.get_gap_alerts()
        with st.form("new_case"):
            opts = [f"{r['policy_id']} · {r['gap_type']} · {r['severity']}"
                    for _, r in gaps.iterrows()]
            idx = st.selectbox("Gap to review", range(len(opts)),
                               format_func=lambda i: opts[i])
            analyst = st.text_input("Assign analyst", value="policy.analyst@ebcbs.demo")
            note = st.text_area("Recommendation note",
                                value="Benchmark criteria against competitor norms; "
                                      "align prior-auth language for consistent regional decisions.")
            submitted = st.form_submit_button("Create review case", type="primary")
        if submitted:
            g = gaps.iloc[idx]
            rec = {"gap_type": g["gap_type"], "severity": g["severity"], "note": note}
            fin = {"detail_metric": None if pd.isna(g["detail_metric"])
                   else float(g["detail_metric"])}
            cid = store.create_case(g["policy_id"], g["gap_type"], analyst, rec, fin)
            st.success(f"Created review case **{cid}** for {g['policy_id']}.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not create case: {e}")

    st.markdown("**Current review cases**")
    try:
        cases = store.list_cases()
        if len(cases):
            st.dataframe(cases, use_container_width=True, hide_index=True)
        else:
            st.info("No review cases yet — create one above.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not list cases: {e}")

st.caption("All data synthetic · health plan = EBCBS (code name) · Databricks Apps + "
           "SQL Warehouse + Lakebase + Genie · policy administration support only.")
