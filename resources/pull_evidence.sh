#!/usr/bin/env bash
# Pull a step's markdown evidence report from the Volume into the repo evidence/ dir.
# Usage: resources/pull_evidence.sh <step_name>   # e.g. 01_data_generation
set -euo pipefail
PROFILE="${DBNB_PROFILE:-fe-vm-fevm-arjoon-ws}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
STEP="${1:?usage: pull_evidence.sh <step_name>}"
SRC="dbfs:/Volumes/arjoon_ws_catalog/policylens_bronze/raw/_evidence/${STEP}.md"
DEST="$REPO/evidence/${STEP}.md"
databricks fs cp "$SRC" "$DEST" --overwrite --profile "$PROFILE"
echo ">> pulled $SRC -> $DEST ($(wc -l < "$DEST") lines)"