"""Resume bounded local OCR workers; retain every failure in the manifest denominator."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
READER = None


def initialize(repo):
    global READER
    from jev_tickets.ocr import TraceReader

    READER = TraceReader(repo, ROOT / ".cache/models", ROOT / ".cache/benchmark-ocr", threads=1)


def process(row):
    try:
        return {"id": row["id"], "status": "ok", **READER.read(ROOT / row["image"])}
    except Exception as exc:
        return {"id": row["id"], "status": "error", "error": type(exc).__name__ + ": " + str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-repo", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--manifest", default="real-manifest.jsonl")
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise ValueError("Use 1 to 8 OCR workers")
    rows = [
        json.loads(line)
        for line in (ROOT / "evaluation" / args.manifest).read_text(encoding="utf-8").splitlines()
    ]
    output = ROOT / "evaluation" / (args.output or args.manifest.replace("-manifest", "-ocr"))
    existing = (
        {json.loads(line)["id"] for line in output.read_text(encoding="utf-8").splitlines()}
        if output.exists()
        else set()
    )
    pending = [r for r in rows if "image" in r and r["id"] not in existing]
    pending.sort(key=lambda r: (r["split"] != "dev", r["id"]))
    if args.reverse:
        pending.reverse()
    started = time.perf_counter()
    with (
        output.open("a", encoding="utf-8") as stream,
        ProcessPoolExecutor(
            max_workers=args.workers, initializer=initialize, initargs=(args.trace_repo,)
        ) as pool,
    ):
        futures = [pool.submit(process, row) for row in pending]
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
            if i % 10 == 0 or result["status"] == "error":
                print(
                    json.dumps(
                        {
                            "completed": i,
                            "pending_total": len(pending),
                            "elapsed_s": round(time.perf_counter() - started),
                            "last_status": result["status"],
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    main()
