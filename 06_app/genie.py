"""Embedded Genie copilot for PolicyLens Command Center.

Uses the Genie Conversation API against the governed space over the same
synthetic EBCBS data. Auth is the app service principal (OAuth).
"""
import time
import requests
from databricks.sdk.core import Config

SPACE_ID = "01f1b60efe501b9f9c318dfa6d59059b"
_cfg = Config()


def _headers():
    h = _cfg.authenticate()
    h["Content-Type"] = "application/json"
    return h


def ask(question: str, timeout: int = 210) -> dict:
    """Ask Genie a question; poll to completion; return text + optional SQL/rows."""
    base = _cfg.host
    h = _headers()
    r = requests.post(
        f"{base}/api/2.0/genie/spaces/{SPACE_ID}/start-conversation",
        headers=h, json={"content": question}, timeout=30,
    )
    r.raise_for_status()
    j = r.json()
    conv_id = j["conversation_id"]
    msg_id = j["message_id"]

    deadline = time.time() + timeout
    msg = {}
    while time.time() < deadline:
        m = requests.get(
            f"{base}/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conv_id}/messages/{msg_id}",
            headers=h, timeout=30,
        )
        m.raise_for_status()
        msg = m.json()
        status = msg.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"):
            break
        time.sleep(1.5)

    out = {"status": msg.get("status", "TIMEOUT"), "text": "", "sql": None,
           "columns": None, "rows": None, "error": None}

    if out["status"] != "COMPLETED":
        out["error"] = msg.get("error", {}).get("error", out["status"])
        return out

    for att in msg.get("attachments", []) or []:
        if att.get("text") and att["text"].get("content"):
            out["text"] += att["text"]["content"] + "\n"
        if att.get("query"):
            out["sql"] = att["query"].get("query")
            att_id = att.get("attachment_id")
            if att_id:
                try:
                    qr = requests.get(
                        f"{base}/api/2.0/genie/spaces/{SPACE_ID}/conversations/"
                        f"{conv_id}/messages/{msg_id}/attachments/{att_id}/query-result",
                        headers=h, timeout=45,
                    ).json()
                    sr = qr.get("statement_response", {})
                    cols = [c["name"] for c in
                            sr.get("manifest", {}).get("schema", {}).get("columns", [])]
                    data = sr.get("result", {}).get("data_array", [])
                    if cols:
                        out["columns"] = cols
                        out["rows"] = data
                except Exception:  # noqa: BLE001
                    pass
    out["text"] = out["text"].strip()
    return out
