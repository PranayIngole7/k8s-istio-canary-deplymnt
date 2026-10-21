import contextlib
import importlib.util
import io
import math
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "evaluate-canary.py"
)

SPEC = importlib.util.spec_from_file_location(
    "evaluate_canary", SCRIPT
)
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def request_row(workload, code, value):
    return {
        "metric": {
            "destination_workload": workload,
            "response_code": code,
        },
        "value": [0, str(value)],
    }


def latency_row(workload, value):
    return {
        "metric": {"destination_workload": workload},
        "value": [0, str(value)],
    }


class CanaryEvaluatorTests(unittest.TestCase):

    def run_evaluator(self, weights, requests, latencies):
        EVALUATOR.get_route_weights = lambda: weights.copy()

        responses = iter([requests, latencies])
        EVALUATOR.query_prometheus = lambda query: next(responses)

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = EVALUATOR.main()

        return exit_code, output.getvalue()

    def healthy_metrics(self):
        requests = [
            request_row("stable-app", "200", 1000),
            request_row("canary-app", "200", 100),
        ]
        latencies = [
            latency_row("stable-app", 5.0),
            latency_row("canary-app", 6.0),
        ]
        return requests, latencies

    def test_disabled_canary_is_not_evaluated(self):
        code, output = self.run_evaluator(
            {"stable": 100, "canary": 0}, [], []
        )
        self.assertEqual(code, 2)
        self.assertIn("NOT EVALUATED", output)

    def test_healthy_metrics_are_promotion_candidate(self):
        requests, latencies = self.healthy_metrics()
        code, output = self.run_evaluator(
            {"stable": 80, "canary": 20}, requests, latencies
        )
        self.assertEqual(code, 0)
        self.assertIn("PROMOTION CANDIDATE", output)

    def test_high_error_rate_recommends_rollback(self):
        requests = [
            request_row("stable-app", "200", 1000),
            request_row("canary-app", "200", 98),
            request_row("canary-app", "500", 2),
        ]
        latencies = [
            latency_row("stable-app", 5.0),
            latency_row("canary-app", 6.0),
        ]
        code, output = self.run_evaluator(
            {"stable": 80, "canary": 20}, requests, latencies
        )
        self.assertEqual(code, 1)
        self.assertIn("RECOMMENDATION: ROLLBACK", output)

    def test_excessive_relative_latency_recommends_rollback(self):
        requests, _ = self.healthy_metrics()
        latencies = [
            latency_row("stable-app", 5.0),
            latency_row("canary-app", 10.0),
        ]
        code, output = self.run_evaluator(
            {"stable": 80, "canary": 20}, requests, latencies
        )
        self.assertEqual(code, 1)
        self.assertIn("latency", output.lower())

    def test_insufficient_canary_requests(self):
        requests = [
            request_row("stable-app", "200", 1000),
            request_row("canary-app", "200", 49),
        ]
        latencies = [
            latency_row("stable-app", 5.0),
            latency_row("canary-app", 5.0),
        ]
        code, output = self.run_evaluator(
            {"stable": 80, "canary": 20}, requests, latencies
        )
        self.assertEqual(code, 2)
        self.assertIn("INSUFFICIENT DATA", output)

    def test_invalid_canary_latency_is_insufficient_data(self):
        requests, _ = self.healthy_metrics()

        invalid_values = [
            None,
            math.nan,
            math.inf,
            -1.0,
        ]

        for invalid in invalid_values:
            with self.subTest(latency=invalid):
                latencies = [latency_row("stable-app", 5.0)]

                if invalid is not None:
                    latencies.append(
                        latency_row("canary-app", invalid)
                    )

                code, output = self.run_evaluator(
                    {"stable": 80, "canary": 20},
                    requests,
                    latencies,
                )

                self.assertEqual(code, 2)
                self.assertIn("INSUFFICIENT DATA", output)

    def test_missing_stable_latency_is_insufficient_data(self):
        requests, _ = self.healthy_metrics()
        latencies = [latency_row("canary-app", 6.0)]

        code, output = self.run_evaluator(
            {"stable": 80, "canary": 20}, requests, latencies
        )

        self.assertEqual(code, 2)
        self.assertIn("INSUFFICIENT DATA", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
