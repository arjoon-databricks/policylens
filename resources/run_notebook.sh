#!/usr/bin/env bash
# PolicyLens notebook runner — import a local .py notebook to the workspace,
# run it on serverless as a one-time job, wait, and capture outputs as evidence.
#
# Usage:
#   resources/run_notebook.sh <local_notebook.py> <run_name> [evidence_out.txt]
#
# It prints the run page URL, the notebook's dbutils.notebook.exit() value,
# and writes the HTML render (cells WITH outputs) to evidence_out.html when given.
#
# Env:
#   DBNB_PROFILE   CLI profile   (default: fe-vm-fevm-arjoon-ws)
#   DBNB_WSDIR     workspace dir (default: /Workspace/Users/<me>/policylens)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="${DBNB_PROFILE:-fe-vm-fevm-arjoon-ws}"
H="python3 $HERE/_runhelp.py"

LOCAL_NB="${1:?usage: run_notebook.sh <local.py> <run_name> [evidence_out]}"
RUN_NAME="${2:?run_name required}"
EVID="${3:-}"

ME="$(databricks current-user me --profile "$PROFILE" | python3 -c 'import json,sys;print(json.load(sys.stdin)["userName"])')"
WSDIR="${DBNB_WSDIR:-/Workspace/Users/$ME/policylens}"
BASENAME="$(basename "$LOCAL_NB" .py)"
WSPATH="$WSDIR/$BASENAME"

echo ">> importing $LOCAL_NB -> $WSPATH"
databricks workspace mkdirs "$WSDIR" --profile "$PROFILE" 2>/dev/null || true
databricks workspace import "$WSPATH" --file "$LOCAL_NB" \
  --format SOURCE --language PYTHON --overwrite --profile "$PROFILE"

# Always keep the shared helper next to step notebooks so `%run ./policylens_common` resolves.
COMMON="$HERE/policylens_common.py"
if [[ -f "$COMMON" && "$BASENAME" != "policylens_common" ]]; then
  databricks workspace import "$WSDIR/policylens_common" --file "$COMMON" \
    --format SOURCE --language PYTHON --overwrite --profile "$PROFILE"
fi

echo ">> submitting serverless run '$RUN_NAME'"
BODY=$($H submit_body "$WSPATH" "$RUN_NAME")
SUB=$(databricks jobs submit --json "$BODY" --no-wait --profile "$PROFILE")
RUN_ID=$(echo "$SUB" | $H run_id)
echo ">> run_id=$RUN_ID"

# Poll parent run until terminal.
LIFE="PENDING"
for _ in $(seq 1 400); do
  GR=$(databricks jobs get-run "$RUN_ID" --profile "$PROFILE")
  LIFE=$(echo "$GR" | $H life_cycle)
  case "$LIFE" in
    TERMINATED|SKIPPED|INTERNAL_ERROR) break ;;
  esac
  sleep 6
done

PAGE=$(echo "$GR" | $H run_page)
RES=$(echo "$GR" | $H result)
TASK_RUN_ID=$(echo "$GR" | $H task_run_id)
echo ">> life_cycle=$LIFE result=$RES"
echo ">> run page: $PAGE"

# Notebook exit value (compact summary the notebook returns).
if [[ -n "$TASK_RUN_ID" ]]; then
  echo ">> notebook exit output:"
  databricks jobs get-run-output "$TASK_RUN_ID" --profile "$PROFILE" 2>/dev/null | $H notebook_output || true
fi

# Full HTML render (cells WITH outputs) for committable evidence.
if [[ -n "$EVID" && -n "$TASK_RUN_ID" ]]; then
  echo ">> exporting run HTML -> $EVID"
  databricks api get "/api/2.1/jobs/runs/export?run_id=$TASK_RUN_ID&views_to_export=CODE" \
    --profile "$PROFILE" \
    | python3 -c 'import json,sys; v=json.load(sys.stdin).get("views",[]); sys.stdout.write(v[0]["content"] if v else "")' \
    > "$EVID" || true
  echo ">> wrote $(wc -c < "$EVID" 2>/dev/null || echo 0) bytes"
fi

# Non-zero exit if the run did not succeed, so callers can detect failure.
case "$RES" in
  SUCCESS*) exit 0 ;;
  *) exit 1 ;;
esac
