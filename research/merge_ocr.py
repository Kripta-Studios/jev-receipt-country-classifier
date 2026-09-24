"""Merge interrupted forward/reverse OCR jobs without changing reference labels."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "evaluation"
merged = {}
for name in ("real-ocr-reverse.jsonl", "real-ocr.jsonl"):
    path = root / name
    if not path.exists():
        continue
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["id"] not in merged or row["status"] == "ok":
            merged[row["id"]] = row
(root / "real-ocr.jsonl").write_text(
    "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged.values()), encoding="utf-8"
)
print(f"Merged {len(merged)} unique OCR results")
