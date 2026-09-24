import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jev_tickets.classifier import classify, route, rule_baseline
from jev_tickets.client import JevClient, ProviderError, retry_delay, validate_response
from jev_tickets.metrics import summarize, wilson
from jev_tickets.prompts import focused_text, make_payload


def response(payload, country="FR"):
    countries = payload["questions"]["country"]["criteria"]
    result = {
        "model": "jev-1.13.0",
        "answers": {
            "country": {
                "type": "choice",
                "choice": country,
                "confidence": 1.0,
                "probabilities": {k: float(k == country) for k in countries},
            }
        },
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }
    if "location_evidence" in payload["questions"]:
        result["answers"]["location_evidence"] = {"type": "noul", "noul": 0.99}
    return result


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.payload = make_payload("Merchant in Lyon, France")
        self.valid = response(self.payload)

    def test_payload_contains_text_only(self):
        self.assertEqual(set(self.payload["state"]), {"receipt_text"})
        self.assertEqual(self.payload["model"], "jev-1.13.0")
        self.assertNotIn("image", self.payload)
        self.assertIn("UNKNOWN", self.payload["questions"]["country"]["criteria"])

    def test_reject_invalid_inputs(self):
        for text in ("", "  ", None, "x" * 80_001):
            with self.assertRaises(ValueError):
                make_payload(text)
        for countries in ({}, {"UKK": "UK"}, {"GB": ""}, ["GB"]):
            with self.assertRaises(ValueError):
                make_payload("test", countries=countries)

    def test_focused_text_preserves_middle_evidence(self):
        lines = [f"ordinary item {i}" for i in range(100)]
        lines[50] = "SIRET 12345678900011"
        focused = focused_text("\n".join(lines))
        self.assertIn(lines[0], focused)
        self.assertIn(lines[99], focused)
        self.assertIn(lines[50], focused)
        self.assertNotIn(lines[49], focused)

    def test_valid_response(self):
        self.assertIs(validate_response(self.valid, self.payload["questions"]), self.valid)

    def test_reject_nonfinite_and_boolean_probabilities(self):
        for value in (float("nan"), float("inf"), True, -0.1, 1.1):
            bad = copy.deepcopy(self.valid)
            bad["answers"]["country"]["probabilities"]["FR"] = value
            with self.assertRaises(ProviderError):
                validate_response(bad, self.payload["questions"])

    def test_reject_missing_options_and_wrong_max(self):
        bad = copy.deepcopy(self.valid)
        del bad["answers"]["country"]["probabilities"]["US"]
        with self.assertRaises(ProviderError):
            validate_response(bad, self.payload["questions"])
        bad = copy.deepcopy(self.valid)
        bad["answers"]["country"]["choice"] = "US"
        with self.assertRaises(ProviderError):
            validate_response(bad, self.payload["questions"])

    def test_reject_missing_question_and_usage(self):
        for field in ("usage", "answers"):
            bad = copy.deepcopy(self.valid)
            del bad[field]
            with self.assertRaises(ProviderError):
                validate_response(bad, self.payload["questions"])

    def test_noul_is_independent(self):
        bad = copy.deepcopy(self.valid)
        bad["answers"]["location_evidence"]["noul"] = 0.1
        self.assertEqual(
            route(
                bad["answers"]["country"],
                0.1,
                {"min_probability": 0.9, "min_margin": 0.15, "min_evidence": 0.8},
            )["review_reason"],
            "weak_location_evidence",
        )

    def test_other_unknown_and_disabled_are_review(self):
        for label in ("OTHER", "UNKNOWN"):
            answer = response(self.payload, label)["answers"]["country"]
            self.assertIsNone(route(answer)["country"])
        self.assertEqual(
            route(self.valid["answers"]["country"], policy={"automatic_enabled": False})["status"],
            "review",
        )

    def test_empty_input_does_not_call_provider(self):
        class NoCall:
            def evaluate(self, payload):
                raise AssertionError("Must not call API")

        self.assertEqual(classify(" ", NoCall())["review_reason"], "empty_extraction")

    def test_cache_replay_does_not_call_provider_or_save_key(self):
        with tempfile.TemporaryDirectory() as directory:
            client = JevClient(directory, api_key="private-test-key")
            with patch(
                "urllib.request.urlopen", return_value=io.BytesIO(json.dumps(self.valid).encode())
            ) as call:
                first = client.evaluate(self.payload)
                second = client.evaluate(self.payload)
                self.assertEqual(call.call_count, 1)
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertEqual(second["network_attempts"], 0)
            self.assertNotIn("private-test-key", next(Path(directory).glob("*.json")).read_text())

    def test_timeout_is_error_not_unknown(self):
        client = JevClient(api_key="test")
        with patch("urllib.request.urlopen", side_effect=TimeoutError) as call:
            with self.assertRaises(ProviderError):
                client.evaluate(self.payload)
            self.assertEqual(call.call_count, 1)

    def test_retry_delay_is_bounded(self):
        self.assertEqual(retry_delay("2", 0), 2)
        with self.assertRaises(ProviderError):
            retry_delay("120", 0)

    def test_rules_abstain_for_shared_currency_and_conflicts(self):
        self.assertEqual(rule_baseline("TOTAL 10 EUR")["country"], "UNKNOWN")
        self.assertEqual(rule_baseline("France\nGermany")["country"], "UNKNOWN")
        self.assertEqual(rule_baseline("SIRET 12345678900011")["country"], "FR")

    def test_metrics_keep_failures_and_abstentions_in_denominator(self):
        rows = [
            {"status": "ok", "expected": "FR", "response": self.valid},
            {"status": "ok", "expected": "US", "response": response(self.payload, "UNKNOWN")},
            {"status": "provider_error", "expected": "IT"},
        ]
        metrics = summarize(rows)
        self.assertEqual(metrics["n"], 3)
        self.assertEqual(metrics["raw_accuracy"], 1 / 3)
        self.assertEqual(metrics["coverage"], 1 / 3)
        self.assertEqual(metrics["accepted_accuracy"], 1)
        self.assertEqual(metrics["unknown"], 1)
        self.assertGreater(wilson(0, 100)[1], 0)


if __name__ == "__main__":
    unittest.main()
