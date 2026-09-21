# Databricks notebook source
# MAGIC %md
# MAGIC # policylens_common — shared config + evidence helpers
# MAGIC `%run ./policylens_common` from any PolicyLens step notebook.
# MAGIC
# MAGIC All data in this project is **synthetic**. "EBCBS" is a code name; no real
# MAGIC customer data or names appear anywhere.

# COMMAND ----------

# ---- Unity Catalog naming (arjoon_ws_catalog; no CREATE CATALOG on metastore) ----
CATALOG = "arjoon_ws_catalog"
BRONZE = "policylens_bronze"
SILVER = "policylens_silver"
GOLD = "policylens_gold"
ML = "policylens_ml"

RAW_VOLUME = f"/Volumes/{CATALOG}/{BRONZE}/raw"
EVIDENCE_DIR = f"{RAW_VOLUME}/_evidence"

PAYERS = ["EBCBS", "Competitor_A", "Competitor_B", "Competitor_C", "Competitor_D"]

# Seeded gap policy ids (consistent across all tables / steps).
GAP_KNEE = "P-2024-KNEE-01"      # overly permissive
GAP_SPINE = "P-2024-SPINE-01"    # overly restrictive
GAP_CARDIAC = "P-2024-CARD-01"   # ambiguous language

# COMMAND ----------

import datetime


class EvidenceReport:
    """Accumulates a markdown report, prints as it goes, and saves to the Volume.

    The saved .md is pulled into the repo `evidence/` folder as readable text
    evidence (the FE Bar evaluator reads text, not screenshots)."""

    def __init__(self, step: str, title: str):
        self.step = step
        self.path = f"{EVIDENCE_DIR}/{step}.md"
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        self.lines = [f"# {title}", "", f"_Generated {ts} — synthetic data; EBCBS is a code name._", ""]
        print(f"===== {title} =====")

    def h(self, text: str):
        self.lines += ["", f"## {text}", ""]
        print(f"\n## {text}")
        return self

    def kv(self, key, val):
        self.lines.append(f"- **{key}**: {val}")
        print(f"  - {key}: {val}")
        return self

    def line(self, text=""):
        self.lines.append(str(text))
        print(text)
        return self

    def table(self, df, n: int = 20):
        """Render a spark or pandas DataFrame head as a markdown table."""
        try:
            pdf = df.limit(n).toPandas() if hasattr(df, "limit") else df.head(n)
        except Exception:
            pdf = df.head(n)
        cols = list(pdf.columns)
        self.lines.append("| " + " | ".join(str(c) for c in cols) + " |")
        self.lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in pdf.iterrows():
            self.lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        self.lines.append("")
        print(pdf.to_string(index=False))
        return self

    def save(self) -> str:
        dbutils.fs.mkdirs(EVIDENCE_DIR)  # noqa: F821
        dbutils.fs.put(self.path, "\n".join(self.lines), True)  # noqa: F821
        print(f"\n>> evidence saved: {self.path}")
        return self.path
