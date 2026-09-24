"""Command line application for text, image, PDF and JSONL batches."""

import argparse
import json
import os
from pathlib import Path
import sys

from .classifier import classify, rule_baseline
from .client import JevClient


def read_policy(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    policy = data.get("policy", data)
    for field in ("min_probability", "min_margin", "min_evidence"):
        if (
            field not in policy
            or type(policy[field]) not in (int, float)
            or not 0 <= policy[field] <= 1
        ):
            raise ValueError(f"Policy {field} must be a number from zero to one")
    return data.get("variant", "focused-v2"), policy


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Classify the issuing store's country from receipts"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--text", help="Receipt text (avoid shell interpolation for untrusted text)"
    )
    source.add_argument("--file", type=Path, help="UTF-8 text, image or PDF")
    source.add_argument("--batch", type=Path, help="JSONL records with id and text or file")
    parser.add_argument("--output", type=Path, help="JSONL output; defaults to standard output")
    parser.add_argument("--trace-repo", default=os.environ.get("TRACE_REPO"))
    parser.add_argument("--model-dir", type=Path, default=Path(".cache/models"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    parser.add_argument("--policy", type=Path, help="A frozen evaluation policy JSON")
    parser.add_argument("--variant", choices=["baseline-v1", "focused-v2"], default=None)
    parser.add_argument(
        "--countries", type=Path, help="JSON object mapping ISO country codes to English names"
    )
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Run the limited deterministic baseline without API calls",
    )
    args = parser.parse_args(argv)
    try:
        variant, policy = read_policy(args.policy) if args.policy else ("focused-v2", None)
        variant = args.variant or variant
        countries = (
            json.loads(args.countries.read_text(encoding="utf-8")) if args.countries else None
        )
        if args.batch:
            inputs = [
                json.loads(line)
                for line in args.batch.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            inputs = (
                [{"id": str(args.file) if args.file else "text", "file": str(args.file)}]
                if args.file
                else [{"id": "text", "text": args.text}]
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    client = JevClient(args.cache_dir / "jev")
    reader = None
    failures = 0
    stream = args.output.open("w", encoding="utf-8") if args.output else sys.stdout
    try:
        for index, item in enumerate(inputs):
            record = (
                {"id": item.get("id", str(index))} if isinstance(item, dict) else {"id": str(index)}
            )
            try:
                if not isinstance(item, dict) or ("text" in item) == ("file" in item):
                    raise ValueError("Each input must contain exactly one of text or file")
                extraction = None
                if "text" in item:
                    text = item["text"]
                else:
                    path = Path(item["file"])
                    if path.suffix.lower() == ".txt":
                        text = path.read_text(encoding="utf-8-sig")
                    else:
                        if not args.trace_repo:
                            raise ValueError("Set TRACE_REPO or --trace-repo for OCR/PDF input")
                        if reader is None:
                            from .ocr import TraceReader

                            reader = TraceReader(
                                args.trace_repo, args.model_dir, args.cache_dir / "app-ocr"
                            )
                        extraction = reader.read(path)
                        text = extraction["text"]
                if not isinstance(text, str):
                    raise ValueError("Receipt text must be a string")
                if args.rules_only:
                    decision = {**rule_baseline(text), "method": "literal_rules"}
                else:
                    decision = classify(text, client, variant, policy, countries)
                record.update(decision)
                if extraction:
                    record["extraction"] = extraction
            except Exception as exc:
                failures += 1
                record.update(
                    status="error", country=None, error=type(exc).__name__ + ": " + str(exc)
                )
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
    finally:
        if args.output:
            stream.close()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
