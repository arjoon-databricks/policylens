"""Helper for run_notebook.sh — build/parse Jobs API JSON from stdin/args."""
import json
import sys

mode = sys.argv[1]

if mode == "submit_body":
    ws_path, run_name = sys.argv[2], sys.argv[3]
    body = {
        "run_name": run_name,
        "tasks": [
            {
                "task_key": "main",
                "notebook_task": {"notebook_path": ws_path, "source": "WORKSPACE"},
            }
        ],
    }
    print(json.dumps(body))
    sys.exit(0)

data = json.load(sys.stdin)

if mode == "run_id":
    print(data["run_id"])
elif mode == "life_cycle":
    print(data.get("state", {}).get("life_cycle_state", "UNKNOWN"))
elif mode == "result":
    st = data.get("state", {})
    print(st.get("result_state", "") + "|" + st.get("state_message", "").replace("\n", " ")[:400])
elif mode == "task_run_id":
    tasks = data.get("tasks", [])
    print(tasks[0]["run_id"] if tasks else "")
elif mode == "run_page":
    print(data.get("run_page_url", ""))
elif mode == "notebook_output":
    # from jobs get-run-output
    out = data.get("notebook_output", {})
    res = out.get("result", "")
    truncated = out.get("truncated", False)
    print(res)
    if truncated:
        sys.stderr.write("[notebook_output truncated]\n")
else:
    sys.stderr.write("unknown mode: " + mode + "\n")
    sys.exit(2)
