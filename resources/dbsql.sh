#!/usr/bin/env bash
# PolicyLens SQL helper — run a SQL statement on the workspace via the
# Databricks SQL Statement Execution API (no Python deps required).
#
# Usage:
#   resources/dbsql.sh "SELECT current_catalog()"
#   echo "CREATE CATALOG IF NOT EXISTS policylens_demo" | resources/dbsql.sh -
#
# Env:
#   DBSQL_PROFILE   Databricks CLI profile (default: fe-vm-fevm-arjoon-ws)
#   DBSQL_WAREHOUSE SQL warehouse id      (default: 8085db376d889a9a)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="${DBSQL_PROFILE:-fe-vm-fevm-arjoon-ws}"
WAREHOUSE="${DBSQL_WAREHOUSE:-8085db376d889a9a}"
FMT="python3 $HERE/_dbsql.py"

if [[ "${1:-}" == "-" ]]; then
  STMT="$(cat)"
else
  STMT="${1:?usage: dbsql.sh \"<SQL>\" | dbsql.sh -}"
fi

REQ=$($FMT req "$WAREHOUSE" "$STMT")
RESP=$(databricks api post /api/2.0/sql/statements --json "$REQ" --profile "$PROFILE")
SID=$(echo "$RESP" | $FMT sid)
STATE=$(echo "$RESP" | $FMT state)

for _ in $(seq 1 80); do
  case "$STATE" in
    SUCCEEDED|FAILED|CANCELED|CLOSED) break ;;
  esac
  sleep 3
  RESP=$(databricks api get "/api/2.0/sql/statements/$SID" --profile "$PROFILE")
  STATE=$(echo "$RESP" | $FMT state)
done

echo "$RESP" | $FMT print
