#!/usr/bin/env bash

set -euo pipefail

WORKER_BASE_URL="${WORKER_BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${WORKER_INTERNAL_TOKEN:-${INGEST_JOB_TOKEN:-}}"
DAYS_PER_WINDOW="${DAYS_PER_WINDOW:-7}"

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "Set WORKER_INTERNAL_TOKEN or INGEST_JOB_TOKEN before running this script." >&2
  exit 1
fi

read -r RANGE_START RANGE_END < <(
  START_DATE="${START_DATE:-}" END_DATE="${END_DATE:-}" python3 - <<'PY'
import os
from datetime import date, timedelta

end = os.environ.get("END_DATE", "").strip()
start = os.environ.get("START_DATE", "").strip()

end = date.fromisoformat(end) if end else date.today()
start = date.fromisoformat(start) if start else end - timedelta(days=182)

print(start.isoformat(), end.isoformat())
PY
)

CATEGORIES_PAYLOAD=""
if [[ -n "${CATEGORIES_JSON:-}" ]]; then
  CATEGORIES_PAYLOAD=", \"categories\": ${CATEGORIES_JSON}"
fi

# Build list of weekly windows on the client side
WINDOWS=$(
  START="${RANGE_START}" END="${RANGE_END}" STEP="${DAYS_PER_WINDOW}" python3 - <<'PY'
import os
from datetime import date, timedelta

start = date.fromisoformat(os.environ["START"])
end = date.fromisoformat(os.environ["END"])
step = int(os.environ["STEP"])

cursor = start
while cursor <= end:
    chunk_end = min(cursor + timedelta(days=step - 1), end)
    print(f"{cursor.isoformat()} {chunk_end.isoformat()}")
    cursor = chunk_end + timedelta(days=1)
PY
)

TOTAL_WINDOWS=$(echo "${WINDOWS}" | wc -l | tr -d ' ')

echo "============================================================"
echo "  History backfill: ${RANGE_START} → ${RANGE_END}"
echo "  ${TOTAL_WINDOWS} windows (${DAYS_PER_WINDOW}-day chunks)"
echo "  Server: ${WORKER_BASE_URL}"
echo "============================================================"
echo ""

WINDOW_NUM=0
TOTAL_FETCHED=0
TOTAL_UPSERTED=0
FAILED=0

INTER_WINDOW_DELAY="${INTER_WINDOW_DELAY:-5}"

while IFS=' ' read -r WIN_START WIN_END; do
  WINDOW_NUM=$((WINDOW_NUM + 1))

  if [[ "${WINDOW_NUM}" -gt 1 ]]; then
    sleep "${INTER_WINDOW_DELAY}"
  fi

  printf "[%d/%d]  %s → %s  " "${WINDOW_NUM}" "${TOTAL_WINDOWS}" "${WIN_START}" "${WIN_END}"

  PAYLOAD="{\"startDate\": \"${WIN_START}\", \"endDate\": \"${WIN_END}\"${CATEGORIES_PAYLOAD}}"

  RESPONSE=$(
    curl -s -w "\n%{http_code}" -X POST "${WORKER_BASE_URL}/internal/jobs/history-backfill" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "${PAYLOAD}" \
      --max-time 600
  ) || true

  HTTP_CODE=$(echo "${RESPONSE}" | tail -n1)
  BODY=$(echo "${RESPONSE}" | sed '$d')

  if [[ "${HTTP_CODE}" == "200" ]]; then
    FETCHED=$(echo "${BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('fetched_count',0))" 2>/dev/null || echo "?")
    UPSERTED=$(echo "${BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('upserted_count',0))" 2>/dev/null || echo "?")
    printf "✓  fetched=%s  upserted=%s\n" "${FETCHED}" "${UPSERTED}"
    if [[ "${FETCHED}" =~ ^[0-9]+$ ]]; then TOTAL_FETCHED=$((TOTAL_FETCHED + FETCHED)); fi
    if [[ "${UPSERTED}" =~ ^[0-9]+$ ]]; then TOTAL_UPSERTED=$((TOTAL_UPSERTED + UPSERTED)); fi
  elif [[ "${HTTP_CODE}" == "" ]]; then
    printf "✗  no response (timeout or connection error)\n"
    FAILED=$((FAILED + 1))
  else
    printf "✗  HTTP %s  %s\n" "${HTTP_CODE}" "${BODY}"
    FAILED=$((FAILED + 1))
  fi

done <<< "${WINDOWS}"

echo ""
echo "============================================================"
echo "  Done!  fetched=${TOTAL_FETCHED}  upserted=${TOTAL_UPSERTED}  failed=${FAILED}"
echo "============================================================"
