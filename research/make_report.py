"""Generate auditable evaluation tables without changing a frozen selection policy."""

import copy
import csv
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_tickets.metrics import summarize
from jev_tickets.classifier import route


def load(name):
    path = ROOT / "evaluation" / name
    return (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def main():
    frozen = json.loads((ROOT / "evaluation/frozen-policy.json").read_text(encoding="utf-8"))
    all_rows = []
    metrics = {}
    for path in sorted((ROOT / "evaluation").glob("*-predictions.jsonl")):
        rows = load(path.name)
        all_rows.extend(rows)
        for source, split, variant in sorted(
            {(r["source"], r["split"], r["variant"]) for r in rows}
        ):
            records = [
                r
                for r in rows
                if (r["source"], r["split"], r["variant"]) == (source, split, variant)
            ]
            metrics[source + "/" + split + "/" + variant] = summarize(records, frozen["policy"])
    real_test = [
        r
        for r in all_rows
        if r["source"] == "real" and r["split"] == "test" and r["variant"] == frozen["variant"]
    ]
    assignment = {r["review_id"]: r for r in load("blind-review-assignment.jsonl")}
    labels = json.loads((ROOT / "evaluation/blind-labels.json").read_text(encoding="utf-8"))
    indexed = {assignment[r["review_id"]]["id"]: r for r in labels}
    reviewed = []
    for row in real_test:
        if row["id"] in indexed:
            review = indexed[row["id"]]
            record = copy.deepcopy(row)
            record["metadata_expected"] = row["expected"]
            record["expected"] = review["country"]
            record["review"] = review
            reviewed.append(record)
    metrics["assistant_visual_review"] = summarize(reviewed, frozen["policy"])
    metrics["assistant_high_certainty_review"] = summarize(
        [r for r in reviewed if r["review"]["certainty"] == "high"], frozen["policy"]
    )
    metrics["assistant_indeterminate_review"] = summarize(
        [r for r in reviewed if r["expected"] == "UNKNOWN"], frozen["policy"]
    )
    rules = []
    for row in real_test:
        record = copy.deepcopy(row)
        label = row["rules"]
        if row["status"] == "ok":
            options = row["response"]["answers"]["country"]["probabilities"]
            record["response"]["answers"] = {
                "country": {
                    "type": "choice",
                    "choice": label,
                    "confidence": 1.0,
                    "probabilities": {c: float(c == label) for c in options},
                }
            }
        rules.append(record)
    metrics["real_test_literal_rules"] = summarize(
        rules, {"min_probability": 0, "min_margin": 0, "min_evidence": 0}
    )
    live = [r for r in all_rows if r["status"] == "ok" and not r["cache_hit"]]
    inputs = sum(r["response"]["usage"]["input_tokens"] for r in live)
    outputs = sum(r["response"]["usage"]["output_tokens"] for r in live)
    usage = {
        "successful_uncached_requests": len(live),
        "input_tokens": inputs,
        "output_tokens": outputs,
        "estimated_usd_at_published_rate": inputs * 0.042 / 1_000_000,
        "median_http_s": statistics.median(r["elapsed_s"] for r in live) if live else None,
        "cached_records": sum(r.get("cache_hit", False) for r in all_rows),
        "failed_records": sum(r["status"] != "ok" for r in all_rows),
        "note": "Successful responses only. Failed delivered requests may have unknown usage. Not an invoice.",
    }
    summary = {"frozen_policy": frozen, "metrics": metrics, "usage": usage}
    (ROOT / "evaluation/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "evaluation/review-comparison.json").write_text(
        json.dumps(reviewed, indent=2), encoding="utf-8"
    )
    with (ROOT / "evaluation/predictions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "id",
                "source",
                "split",
                "variant",
                "expected",
                "candidate",
                "status",
                "accepted",
                "probability",
                "confidence",
            ],
        )
        writer.writeheader()
        for row in all_rows:
            result = {k: row[k] for k in ("id", "source", "split", "variant", "expected", "status")}
            if row["status"] == "ok":
                answer = row["response"]["answers"]["country"]
                decision = route(
                    answer,
                    row["response"]["answers"].get("location_evidence", {}).get("noul"),
                    frozen["policy"],
                )
                result.update(
                    candidate=answer["choice"],
                    accepted=decision["status"] == "classified",
                    probability=decision["probability"],
                    confidence=answer["confidence"],
                )
            writer.writerow(result)
    lines = [
        "# Measured evaluation tables",
        "",
        "Generated from stored predictions. Country references are dataset metadata unless explicitly described as assistant review.",
        "",
        "| Dataset / variant | N | Raw match | UNKNOWN | OTHER | Accepted | Accepted errors | Coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in metrics.items():
        accuracy = f"{result['raw_accuracy']:.1%}" if result["raw_accuracy"] is not None else "n/a"
        lines.append(
            f"| {name} | {result['n']} | {accuracy} | {result['unknown']} | {result['other']} | {result['accepted']} | {result['accepted_errors']} | {result['coverage']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## Usage",
            "",
            "```json",
            json.dumps(usage, indent=2),
            "```",
            "",
            "Wilson intervals and calibration values in summary.json treat samples as independent. Repeated stores and weak labels limit that interpretation. Assistant reviews are not human gold labels.",
        ]
    )
    (ROOT / "evaluation/TABLES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"datasets": len(metrics), "reviewed_predictions": len(reviewed), "usage": usage},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
