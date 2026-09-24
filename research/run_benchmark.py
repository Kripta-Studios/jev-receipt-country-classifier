"""Evaluate only text against versioned prompts; reference labels never enter requests."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_tickets.client import JevClient
from jev_tickets.prompts import make_payload
from jev_tickets.classifier import rule_baseline


def load(path):
    return (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", choices=["real", "synthetic", "synthetic-image", "controls"], required=True
    )
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    parser.add_argument("--variants", nargs="+", default=["baseline-v1", "focused-v2"])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.split == "test" and not (ROOT / "evaluation/frozen-policy.json").exists():
        raise ValueError("Freeze the development-selected policy before running test requests")
    manifest = args.source if args.source in ("real", "controls") else "synthetic"
    rows = [
        r for r in load(ROOT / f"evaluation/{manifest}-manifest.jsonl") if r["split"] == args.split
    ]
    if args.source not in ("synthetic", "controls"):
        readings = {r["id"]: r for r in load(ROOT / f"evaluation/{manifest}-ocr.jsonl")}
        if args.source == "synthetic-image":
            rows = [r for r in rows if "image" in r]
        for row in rows:
            reading = readings.get(row["id"], {})
            if not reading:
                raise ValueError("OCR is incomplete; do not silently evaluate a partial sample")
            row["text"] = reading.get("text", "")
            row["extraction_status"] = reading.get("status", "missing")
    output = ROOT / f"evaluation/{args.source}-{args.split}-predictions.jsonl"
    previous = {(r["id"], r["variant"]) for r in load(output)}
    client = JevClient(ROOT / ".cache/jev")

    def process(row, variant):
        base = {k: row[k] for k in ("id", "expected", "source_country", "split", "group")}
        base.update(
            variant=variant, source=args.source, rules=rule_baseline(row.get("text", ""))["country"]
        )
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

    work = [(r, v) for r in rows for v in args.variants if (r["id"], v) not in previous]
    started = time.perf_counter()
    with (
        output.open("a", encoding="utf-8") as stream,
        ThreadPoolExecutor(max_workers=args.workers) as pool,
    ):
        futures = [pool.submit(process, r, v) for r, v in work]
        for i, future in enumerate(as_completed(futures), 1):
            record = future.result()
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            if i % 50 == 0 or record["status"] != "ok":
                print(
                    json.dumps(
                        {
                            "completed": i,
                            "total": len(work),
                            "elapsed_s": round(time.perf_counter() - started),
                            "last_status": record["status"],
                        }
                    ),
                    flush=True,
                )
    print(
        json.dumps({"finished": True, "new_predictions": len(work), "previous": len(previous)}),
        flush=True,
    )


if __name__ == "__main__":
    main()
