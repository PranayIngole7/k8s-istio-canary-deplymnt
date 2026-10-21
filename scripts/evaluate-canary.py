#!/usr/bin/env python3

import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request

PROMETHEUS_URL = "http://127.0.0.1:19090"
NAMESPACE = "canary-demo"
VIRTUAL_SERVICE = "canary-routing"

# Initial demonstration thresholds; tune for a real service.
WINDOW = "5m"
MIN_CANARY_REQUESTS = 50
MAX_CANARY_ERROR_RATE = 0.01       # 1%
MAX_CANARY_P95_MS = 500.0          # 500 milliseconds
MAX_LATENCY_RATIO = 1.5             # Canary p95 <= 1.5x stable p95


def query_prometheus(query):
    url = PROMETHEUS_URL + "/api/v1/query?" + urllib.parse.urlencode(
        {"query": query}
    )

    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.load(response)

    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus query failed: {payload}")

    return payload.get("data", {}).get("result", [])


def get_route_weights():
    command = [
        "kubectl", "get", "virtualservice", VIRTUAL_SERVICE,
        "-n", NAMESPACE, "-o", "json"
    ]
    result = subprocess.run(
        command, check=True, capture_output=True, text=True
    )
    virtual_service = json.loads(result.stdout)

    weights = {}
    routes = virtual_service.get("spec", {}).get("http", [])

    for http_route in routes:
        for route in http_route.get("route", []):
            subset = route.get("destination", {}).get("subset")
            if subset:
                weights[subset] = route.get("weight", 0)

    return weights


def main():
    print("=== Canary Performance Evaluator ===")
    print(f"Prometheus window: {WINDOW}")
    print(
        f"Thresholds: minimum {MIN_CANARY_REQUESTS} canary requests, "
        f"maximum {MAX_CANARY_ERROR_RATE:.1%} errors, "
        f"maximum p95 {MAX_CANARY_P95_MS:.0f} ms, "
        f"maximum latency ratio {MAX_LATENCY_RATIO:.2f}x"
    )

    try:
        weights = get_route_weights()
        print(
            f"Current routing: stable={weights.get('stable', 0)}%, "
            f"canary={weights.get('canary', 0)}%"
        )

        if weights.get("canary", 0) <= 0:
            print(
                "RECOMMENDATION: NOT EVALUATED — canary traffic is disabled. "
                "Enable a controlled canary split before evaluating."
            )
            return 2

        request_query = (
            "sum by (destination_workload, response_code) "
            f"(increase(istio_requests_total"
            f'{{destination_workload_namespace="{NAMESPACE}"}}[{WINDOW}]))'
        )

        request_rows = query_prometheus(request_query)

        counts = {"stable-app": 0.0, "canary-app": 0.0}
        errors = {"stable-app": 0.0, "canary-app": 0.0}

        for row in request_rows:
            labels = row.get("metric", {})
            workload = labels.get("destination_workload")
            code = labels.get("response_code")

            if workload not in counts:
                continue

            value = float(row["value"][1])
            counts[workload] += value

            if code and code.startswith("5"):
                errors[workload] += value

        latency_query = (
            "histogram_quantile(0.95, "
            "sum by (le, destination_workload) "
            f"(rate(istio_request_duration_milliseconds_bucket"
            f'{{destination_workload_namespace="{NAMESPACE}"}}[{WINDOW}])))'
        )

        latency_rows = query_prometheus(latency_query)
        p95 = {}

        for row in latency_rows:
            workload = row.get("metric", {}).get("destination_workload")
            if workload:
                p95[workload] = float(row["value"][1])

        print("\n=== Observed metrics ===")

        for workload in ("stable-app", "canary-app"):
            total = counts[workload]
            error_count = errors[workload]
            error_rate = error_count / total if total > 0 else None
            latency = p95.get(workload)

            error_text = (
                f"{error_rate:.2%}" if error_rate is not None else "N/A"
            )
            latency_text = (
                f"{latency:.2f} ms" if latency is not None else "N/A"
            )

            print(
                f"{workload}: requests={total:.1f}, "
                f"5xx={error_count:.1f}, "
                f"error_rate={error_text}, p95={latency_text}"
            )

        canary_count = counts["canary-app"]
        stable_p95 = p95.get("stable-app")
        canary_p95 = p95.get("canary-app")

        for workload, latency in (
            ("stable-app", stable_p95),
            ("canary-app", canary_p95),
        ):
            if (
                latency is None
                or not math.isfinite(latency)
                or latency < 0
            ):
                print(
                    "\\nRECOMMENDATION: INSUFFICIENT DATA — "
                    f"invalid or missing p95 latency for {workload}."
                )
                return 2

        if canary_count < MIN_CANARY_REQUESTS:
            print(
                "\nRECOMMENDATION: INSUFFICIENT DATA — "
                f"only {canary_count:.1f} canary requests; "
                f"at least {MIN_CANARY_REQUESTS} are required."
            )
            return 2

        if counts["stable-app"] <= 0 or stable_p95 is None or canary_p95 is None:
            print(
                "\nRECOMMENDATION: INSUFFICIENT DATA — "
                "stable baseline or latency histogram is missing."
            )
            return 2

        canary_error_rate = errors["canary-app"] / canary_count
        latency_ratio = (
            canary_p95 / stable_p95 if stable_p95 > 0 else float("inf")
        )

        print(f"\nCanary/stable p95 ratio: {latency_ratio:.2f}x")

        reasons = []

        if canary_error_rate > MAX_CANARY_ERROR_RATE:
            reasons.append(
                f"canary error rate {canary_error_rate:.2%} exceeds "
                f"{MAX_CANARY_ERROR_RATE:.2%}"
            )

        if canary_p95 > MAX_CANARY_P95_MS:
            reasons.append(
                f"canary p95 {canary_p95:.2f} ms exceeds "
                f"{MAX_CANARY_P95_MS:.2f} ms"
            )

        if latency_ratio > MAX_LATENCY_RATIO:
            reasons.append(
                f"canary p95 is {latency_ratio:.2f}x stable p95, "
                f"above {MAX_LATENCY_RATIO:.2f}x"
            )

        if reasons:
            print("\nRECOMMENDATION: ROLLBACK")
            for reason in reasons:
                print(f"- {reason}")
            print("No routing changes were made.")
            return 1

        print(
            "\nRECOMMENDATION: PROMOTION CANDIDATE — "
            "the configured checks passed. "
            "This is not an automatic promotion."
        )
        print("No routing changes were made.")
        return 0

    except Exception as exc:
        print(f"\nERROR: Evaluation could not be completed: {exc}")
        print("RECOMMENDATION: INSUFFICIENT DATA; do not promote canary.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
