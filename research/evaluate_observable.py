"""Re-evaluate the entire pre-labelled 70-image cohort, without changing prompts.

Default: reproduce the report offline from committed OCR/predictions/reviews.
--predict: issue missing, uncached Jev requests (requires TYPESAFE_API_KEY).
--download: fetch only the cohort images from their recorded public source URLs.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_tickets.classifier import classify
from jev_tickets.client import ENDPOINT, JevClient
from jev_tickets.evaluation import summarize_observable
from jev_tickets.prompts import make_payload

DIRECTORY = ROOT / "evaluation/observable"
VARIANTS = ("baseline-v1", "focused-v2")


def load(path):
    return (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predict", action="store_true")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DIRECTORY,
        help="Separate results directory for a new run",
    )
    parser.add_argument(
        "--ocr",
        type=Path,
        default=DIRECTORY / "ocr.jsonl",
        help="OCR records for all 70 cohort images",
    )
    args = parser.parse_args()
    manifest = load(DIRECTORY / "manifest.jsonl")
    labels = {
        r["review_id"]: r
        for r in json.loads((ROOT / "evaluation/blind-labels.json").read_text(encoding="utf-8"))
    }
    ocr = {r["id"]: r for r in load(args.ocr)}
    if len(manifest) != 70 or len({r["id"] for r in manifest}) != 70:
        raise ValueError("Expected the fixed 70-image cohort")
    if args.download:
        for row in manifest:
            path = ROOT / row["image"]
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                request = urllib.request.Request(
                    row["url"], headers={"User-Agent": "receipt-country-research/1.0"}
                )
                with urllib.request.urlopen(request, timeout=60) as response:
                    path.write_bytes(response.read())
            expected = ocr.get(row["id"], {}).get("sha256")
            if expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Image hash changed: {row['id']}")
        print("Verified/downloaded 70 source images.")
        return
    if set(ocr) != {r["id"] for r in manifest}:
        raise ValueError("Complete all 70 OCR attempts before evaluating")
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "predictions.jsonl"
    previous = load(output)
    keys = {(r["id"], r["variant"]) for r in previous}
    requests = {}
    for row in manifest:
        reading = ocr[row["id"]]
        for variant in VARIANTS:
            if reading["status"] == "ok" and reading.get("text", "").strip():
                payload = make_payload(reading["text"], variant)
                encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                requests[row["id"], variant] = hashlib.sha256(
                    ENDPOINT.encode() + encoded
                ).hexdigest()
            else:
                requests[row["id"], variant] = None
    for record in previous:
        key = record["id"], record["variant"]
        if key not in requests or record.get("request_sha256") != requests[key]:
            raise ValueError(
                "Saved predictions do not match this OCR/prompt input; choose a new --output-dir"
            )
    if args.predict:
        client = JevClient()  # No response cache; stored output provides explicit resumption.

        def process(row, variant):
            reading = ocr[row["id"]]
            base = {
                "id": row["id"],
                "variant": variant,
                "request_sha256": requests[row["id"], variant],
            }
            if reading["status"] != "ok" or not reading.get("text", "").strip():
                return {**base, "status": "extraction_error", "candidate": None}
            try:
                decision = classify(
                    reading["text"], client, variant, policy={"automatic_enabled": False}
                )
                return {**base, **decision, "route_status": decision["status"], "status": "ok"}
            except Exception as exc:
                return {
                    **base,
                    "status": "provider_error",
                    "candidate": None,
                    "error_type": type(exc).__name__,
                }

        work = [(r, v) for r in manifest for v in VARIANTS if (r["id"], v) not in keys]
        if work and not client.api_key:
            raise ValueError("Set TYPESAFE_API_KEY before requesting new predictions")
        with (
            output.open("a", encoding="utf-8") as stream,
            ThreadPoolExecutor(max_workers=args.workers) as pool,
        ):
            futures = [pool.submit(process, r, v) for r, v in work]
            for i, future in enumerate(as_completed(futures), 1):
                stream.write(json.dumps(future.result(), ensure_ascii=False) + "\n")
                stream.flush()
                if i % 20 == 0:
                    print(f"Completed {i}/{len(work)} new Jev decisions", flush=True)
    predictions = load(output)
    if len(predictions) != 140 or {(r["id"], r["variant"]) for r in predictions} != {
        (r["id"], v) for r in manifest for v in VARIANTS
    }:
        raise ValueError("Need exactly two predictions per case; run with --predict")
    by_id = {r["id"]: r for r in manifest}
    cases = []
    for prediction in predictions:
        row = by_id[prediction["id"]]
        review = labels[row["review_id"]]
        cases.append(
            {
                **prediction,
                "metadata_country": row["expected"],
                "reviewed_image_country": review["country"],
                "review_certainty": review["certainty"],
                "review_evidence": review["evidence"],
                "review_id": row["review_id"],
            }
        )
    cases.sort(key=lambda r: (r["review_id"], r["variant"]))
    summary = {
        "cohort": "70 pre-labelled images; 10 per source country; test partition",
        "reference": "Assistant image review, not human ground truth or OCR-text-only labels",
        "variants": summarize_observable(cases),
    }
    usage = [r for r in predictions if r["status"] == "ok"]
    summary["input_tokens"] = sum(r["usage"]["input_tokens"] for r in usage)
    summary["output_tokens"] = sum(r["usage"]["output_tokens"] for r in usage)
    summary["estimated_api_cost_usd"] = summary["input_tokens"] * 0.042 / 1_000_000
    (destination / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    # Bundle the same generated measurements in the installable browser demo.
    if destination == DIRECTORY.resolve():
        (ROOT / "jev_tickets/static/observable-summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
    (destination / "cases.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in cases), encoding="utf-8"
    )
    columns = [
        "id",
        "review_id",
        "variant",
        "status",
        "metadata_country",
        "reviewed_image_country",
        "candidate",
        "probability",
        "location_evidence_probability",
        "review_certainty",
        "review_evidence",
    ]
    with (destination / "cases.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cases)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
