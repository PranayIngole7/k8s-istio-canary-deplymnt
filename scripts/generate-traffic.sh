#!/usr/bin/env bash
set -u

REQUESTS="${1:-100}"
URL="${2:-http://127.0.0.1:18080/}"
HOST="${HOST_HEADER:-canary-demo.local}"
TIMEOUT="${CURL_TIMEOUT:-5}"

if ! [[ "$REQUESTS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: $0 [positive_request_count] [url]" >&2
    exit 1
fi

for ((i = 1; i <= REQUESTS; i++)); do
    if response=$(curl -sS --max-time "$TIMEOUT" \
        -H "Host: $HOST" \
        -w $'\n%{http_code}' "$URL"); then

        status="${response##*$'\n'}"
        body="${response%$'\n'*}"

        if [[ "$status" =~ ^2[0-9][0-9]$ ]]; then
            if grep -qF 'Canary Demo - v1.0' <<< "$body"; then
                echo "stable"
            elif grep -qF 'Canary Demo - v2.0' <<< "$body"; then
                echo "canary"
            else
                echo "unknown"
            fi
        else
            echo "error"
        fi
    else
        echo "error"
    fi
done
