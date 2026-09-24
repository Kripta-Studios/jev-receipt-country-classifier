"""Protect the distinction between correct labels and justified decisions."""

import unittest

from jev_tickets.evaluation import summarize_observable


class ObservableEvaluationTests(unittest.TestCase):
    def case(self, identifier, metadata, reviewed, candidate, status="ok"):
        return {
            "id": identifier,
            "variant": "v",
            "metadata_country": metadata,
            "reviewed_image_country": reviewed,
            "candidate": candidate,
            "probability": 0.99,
            "status": status,
        }

    def test_lucky_match_and_reasonable_abstention_are_different(self):
        rows = [
            self.case("lucky", "FR", "UNKNOWN", "FR"),
            self.case("abstain", "CA", "UNKNOWN", "UNKNOWN"),
            self.case("visible", "ES", "ES", "ES"),
        ]
        result = summarize_observable(rows)["v"]
        self.assertEqual(result["metadata_matches"], 2)
        self.assertEqual(result["reviewed_image_matches"], 2)
        self.assertEqual(result["unsupported_metadata_matches"], 1)
        self.assertEqual(result["reasonable_abstentions"], 1)
        self.assertEqual(result["unsupported_probability_at_least_0_9"], 1)

    def test_failure_remains_in_denominator_and_other_is_not_abstention(self):
        rows = [
            self.case("failure", "US", "US", None, "extraction_error"),
            self.case("other", "CA", "UNKNOWN", "OTHER"),
        ]
        result = summarize_observable(rows)["v"]
        self.assertEqual(result["n"], 2)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["image_country_observable"], 1)
        self.assertEqual(result["unsupported_country_assertions"], 1)
        self.assertEqual(result["reasonable_abstentions"], 0)

    def test_duplicate_case_is_rejected(self):
        case = self.case("duplicate", "US", "US", "US")
        with self.assertRaises(ValueError):
            summarize_observable([case, case])
