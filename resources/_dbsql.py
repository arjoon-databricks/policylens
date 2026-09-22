"""Helper for dbsql.sh — parse SQL Statement Execution API JSON from stdin.

Modes:
  req <warehouse> <statement>  -> emit request JSON body
  state                        -> print status.state from a response
  sid                          -> print statement_id from a response
  print                        -> pretty-print columns+rows, or error to stderr (exit 1)
"""
import json
import sys

mode = sys.argv[1]

if mode == "req":
    body = {
        "warehouse_id": sys.argv[2],
        "statement": sys.argv[3],
        "wait_timeout": "50s",
        "on_wait_timeout": "CONTINUE",
        "disposition": "INLINE",
        "format": "JSON_ARRAY",
    }
    print(json.dumps(body))
    sys.exit(0)

data = json.load(sys.stdin)

if mode == "state":
    print(data["status"]["state"])
elif mode == "sid":
    print(data["statement_id"])
elif mode == "print":
    state = data["status"]["state"]
    if state != "SUCCEEDED":
        err = data["status"].get("error", {})
        sys.stderr.write("[" + state + "] " + err.get("message", "") + "\n")
        sys.exit(1)
    result = data.get("result", {})
    manifest = data.get("manifest", {})
    cols = [c["name"] for c in manifest.get("schema", {}).get("columns", [])]
    rows = result.get("data_array", []) or []
    if cols:
        print(" | ".join(cols))
    for row in rows[:200]:
        print(" | ".join("NULL" if v is None else str(v) for v in row))
    print("(" + str(len(rows)) + " row(s), state=" + state + ")")
else:
    sys.stderr.write("unknown mode: " + mode + "\n")
    sys.exit(2)
