#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

REQUESTS="${1:-100}"
URL="${2:-http://127.0.0.1:18080/}"
REPORT_DIR="${REPORT_DIR:-$PROJECT_DIR/reports}"

if ! [[ "$REQUESTS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: $0 [positive_request_count] [url]" >&2
    exit 1
fi

mkdir -p "$REPORT_DIR"
RESULTS_FILE="$(mktemp)"
trap 'rm -f "$RESULTS_FILE"' EXIT

"$SCRIPT_DIR/generate-traffic.sh" "$REQUESTS" "$URL" > "$RESULTS_FILE"

STABLE="$(grep -cx 'stable' "$RESULTS_FILE" || true)"
CANARY="$(grep -cx 'canary' "$RESULTS_FILE" || true)"
UNKNOWN="$(grep -cx 'unknown' "$RESULTS_FILE" || true)"
ERRORS="$(grep -cx 'error' "$RESULTS_FILE" || true)"

STABLE_PCT="$(awk -v n="$STABLE" -v t="$REQUESTS" 'BEGIN { printf "%.1f", n*100/t }')"
CANARY_PCT="$(awk -v n="$CANARY" -v t="$REQUESTS" 'BEGIN { printf "%.1f", n*100/t }')"

REPORT_FILE="$REPORT_DIR/traffic-test-$(date +%Y%m%d-%H%M%S).log"

{
    echo "=== Istio Canary Traffic Distribution Test ==="
    echo "Timestamp: $(date --iso-8601=seconds)"
    echo "URL: $URL"
    echo "Host: ${HOST_HEADER:-canary-demo.local}"
    echo
    echo "Total requests: $REQUESTS"
    echo "Stable v1.0 responses: $STABLE"
    echo "Canary v2.0 responses: $CANARY"
    echo "Unknown responses: $UNKNOWN"
    echo "Errors: $ERRORS"
    echo "Observed stable traffic: ${STABLE_PCT}%"
    echo "Observed canary traffic: ${CANARY_PCT}%"
    echo
    echo "Report: $REPORT_FILE"
} | tee "$REPORT_FILE"

if (( UNKNOWN > 0 || ERRORS > 0 )); then
    exit 1
fi
