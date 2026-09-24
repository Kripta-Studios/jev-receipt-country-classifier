"""Audit split separation and exact duplicates without inspecting predictions."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = {}
for source in ("real", "synthetic"):
    rows = [
        json.loads(line)
        for line in (ROOT / f"evaluation/{source}-manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    groups = {split: {r["group"] for r in rows if r["split"] == split} for split in ("dev", "test")}
    hashes = defaultdict(list)
    for row in rows:
        if "image" in row and (ROOT / row["image"]).exists():
            hashes[hashlib.sha256((ROOT / row["image"]).read_bytes()).hexdigest()].append(row)
    duplicates = [rs for rs in hashes.values() if len(rs) > 1]
    report[source] = {
        "samples": len(rows),
        "unique_ids": len({r["id"] for r in rows}),
        "dev_groups": len(groups["dev"]),
        "test_groups": len(groups["test"]),
        "overlapping_groups": sorted(groups["dev"] & groups["test"]),
        "exact_duplicate_image_groups": [[r["id"] for r in rs] for rs in duplicates],
        "duplicate_images_crossing_split": [
            [r["id"] for r in rs] for rs in duplicates if len({r["split"] for r in rs}) > 1
        ],
    }
    assert not report[source]["overlapping_groups"]
    assert not report[source]["duplicate_images_crossing_split"]
(ROOT / "evaluation/manifest-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
