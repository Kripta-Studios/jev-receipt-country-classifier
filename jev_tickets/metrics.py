"""Transparent metrics: abstention and failures stay in the total denominator."""

from collections import Counter
import math

from .classifier import route
from .prompts import COUNTRIES


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - half), min(1, center + half)]


def summarize(records, policy=None):
    n = len(records)
    correct = accepted = accepted_correct = unknown = other = wrong_country = 0
    confusion = Counter()
    failures = Counter()
    calibration = [[] for _ in range(10)]
    brier = []
    for row in records:
        expected = row["expected"]
        if row["status"] != "ok":
            failures[row["status"]] += 1
            confusion[(expected, "ERROR")] += 1
            continue
        answer = row["response"]["answers"]["country"]
        predicted = answer["choice"]
        match = predicted == expected
        correct += match
        unknown += predicted == "UNKNOWN"
        other += predicted == "OTHER"
        wrong_country += predicted not in ("UNKNOWN", "OTHER") and not match
        confusion[(expected, predicted)] += 1
        diagnostic = row["response"]["answers"].get("location_evidence", {}).get("noul")
        decision = route(answer, diagnostic, policy)
        if decision["status"] == "classified":
            accepted += 1
            accepted_correct += match
        p = answer["probabilities"][predicted]
        calibration[min(9, int(p * 10))].append((p, int(match)))
        brier.append(
            sum(
                (value - int(label == expected)) ** 2
                for label, value in answer["probabilities"].items()
            )
        )
    per_country = {}
    for label in sorted({r["expected"] for r in records}):
        support = sum(count for (gold, _), count in confusion.items() if gold == label)
        tp = confusion[(label, label)]
        fp = sum(
            count for (gold, pred), count in confusion.items() if pred == label and gold != label
        )
        fn = support - tp
        per_country[label] = {
            "support": support,
            "correct": tp,
            "recall": tp / support if support else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0,
        }
    bins = [
        {
            "count": len(bucket),
            "mean_probability": sum(x[0] for x in bucket) / len(bucket),
            "observed_accuracy": sum(x[1] for x in bucket) / len(bucket),
        }
        for bucket in calibration
        if bucket
    ]
    evaluated = sum(b["count"] for b in bins)
    return {
        "n": n,
        "raw_correct": correct,
        "raw_accuracy": correct / n if n else None,
        "raw_accuracy_wilson95": wilson(correct, n),
        "unknown": unknown,
        "other": other,
        "wrong_country_assertions": wrong_country,
        "failures": dict(failures),
        "accepted": accepted,
        "accepted_correct": accepted_correct,
        "accepted_errors": accepted - accepted_correct,
        "coverage": accepted / n if n else 0,
        "accepted_accuracy": accepted_correct / accepted if accepted else None,
        "accepted_error_wilson95": wilson(accepted - accepted_correct, accepted),
        "macro_f1": sum(v["f1"] for k, v in per_country.items() if k in COUNTRIES)
        / max(1, sum(k in COUNTRIES for k in per_country)),
        "per_country": per_country,
        "confusion": {f"{a}->{b}": v for (a, b), v in sorted(confusion.items())},
        "multiclass_brier": sum(brier) / len(brier) if brier else None,
        "top_label_ece": sum(
            b["count"] * abs(b["mean_probability"] - b["observed_accuracy"]) for b in bins
        )
        / evaluated
        if evaluated
        else None,
        "calibration_bins": bins,
    }
