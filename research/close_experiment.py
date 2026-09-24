"""Close the exploratory experiment on the available OCR snapshot, without new OCR."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_tickets.client import JevClient
from jev_tickets.classifier import rule_baseline
from jev_tickets.prompts import make_payload


def load(name):
    path = ROOT / "evaluation" / name
    return (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def main():
    policy_path = ROOT / "evaluation/frozen-policy.json"
    if not policy_path.exists():
        policy_path.write_text(
            json.dumps(
                {
                    "variant": "focused-v2",
                    "policy": {
                        "min_probability": 0.9,
                        "min_margin": 0.15,
                        "min_evidence": 0,
                        "automatic_enabled": False,
                    },
                    "selected_on": "Exploratory synthetic development comparison; no completed real-data policy calibration",
                    "selected_at": datetime.now(timezone.utc).isoformat(),
                    "criterion_met": False,
                    "note": "User requested early experimental closure. This is a disabled automation policy, not a calibrated policy.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    rows = []
    snapshot = {}
    for source, manifest in [("real", "real"), ("synthetic-image", "synthetic")]:
        readings = {r["id"]: r for r in load(f"{manifest}-ocr.jsonl")}
        available = [r for r in load(f"{manifest}-manifest.jsonl") if r["id"] in readings]
        snapshot[source] = [r["id"] for r in available]
        for row in available:
            reading = readings[row["id"]]
            rows.append(
                {
                    **row,
                    "source": source,
                    "text": reading.get("text", ""),
                    "extraction_status": reading["status"],
                }
            )
    rows.extend({**r, "source": "controls"} for r in load("controls-manifest.jsonl"))
    (ROOT / "evaluation/closure-snapshot.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reason": "User requested closing the exploratory project without finishing the long benchmark.",
                "sampling_warning": "Available OCR is a processing-order subset, not a fresh random sample or the completed preregistered test.",
                "ids": snapshot,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output = ROOT / "evaluation/available-predictions.jsonl"
    done = {(r["source"], r["id"], r["variant"]) for r in load(output.name)}
    client = JevClient(ROOT / ".cache/jev")

    def process(row, variant):
        base = {k: row[k] for k in ("id", "expected", "source_country", "split", "group", "source")}
        base.update(variant=variant, rules=rule_baseline(row.get("text", ""))["country"])
        if row.get("extraction_status", "ok") != "ok" or not row.get("text", "").strip():
            return {**base, "status": "extraction_error"}
        try:
            return {**base, "status": "ok", **client.evaluate(make_payload(row["text"], variant))}
        except Exception as exc:
            return {
                **base,
                "status": "provider_error",
                "error": type(exc).__name__ + ": " + str(exc),
            }

    work = [
        (r, v)
        for r in rows
        for v in ("baseline-v1", "focused-v2")
        if (r["source"], r["id"], v) not in done
    ]
    with output.open("a", encoding="utf-8") as stream, ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(process, r, v) for r, v in work]
        for i, future in enumerate(as_completed(futures), 1):
            stream.write(json.dumps(future.result(), ensure_ascii=False) + "\n")
            stream.flush()
            if i % 100 == 0:
                print(json.dumps({"completed": i, "total": len(work)}), flush=True)
    print("Exploratory snapshot complete.", flush=True)


if __name__ == "__main__":
    main()
