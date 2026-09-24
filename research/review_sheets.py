"""Render blinded receipt contact sheets for independent visual review."""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

root = Path(__file__).resolve().parents[1]
rows = [
    json.loads(line)
    for line in (root / "evaluation/blind-review-assignment.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
out = root / ".cache/review-sheets"
out.mkdir(parents=True, exist_ok=True)
for offset in range(0, len(rows), 4):
    sheet = Image.new("RGB", (2000, 1400), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    for column, row in enumerate(rows[offset : offset + 4]):
        draw.text(
            (column * 500 + 10, 10), f"REVIEW {row['review_id']:02d}", fill="black", font_size=24
        )
        with Image.open(root / row["image"]) as original:
            receipt = ImageOps.exif_transpose(original).convert("RGB")
            receipt.thumbnail((480, 1330))
            sheet.paste(receipt, (column * 500 + 10, 55))
    sheet.save(out / f"sheet-{offset // 4 + 1:02d}.jpg", quality=92)
print(f"Created {(len(rows) + 3) // 4} blinded sheets")
