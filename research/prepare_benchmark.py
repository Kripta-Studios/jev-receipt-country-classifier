"""Prepare deterministic, grouped evaluation manifests and attributed image downloads."""

import collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import urllib.request

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
OUT = ROOT / "evaluation"
COUNTRIES = ["ES", "FR", "DE", "IT", "GB", "US", "CA"]
SEED = 24092026


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "JevReceiptEvaluation/0.1"})
        with urllib.request.urlopen(req, timeout=90) as response:
            data = response.read(300_000_000)
        temporary = path.with_suffix(path.suffix + ".partial")
        temporary.write_bytes(data)
        temporary.replace(path)
    return path


def write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )


def main():
    OUT.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    db = duckdb.connect()
    db.read_parquet(str(CACHE / "open-prices.parquet")).create_view("prices")
    real = db.sql("""
       SELECT proof_id, min(proof_file_path) AS path,
              min(location_osm_address_country_code) AS country,
              min(location_id) AS location_id
       FROM prices WHERE proof_type = 'RECEIPT' AND proof_file_path IS NOT NULL
       GROUP BY proof_id HAVING count(DISTINCT location_osm_address_country_code) = 1
    """).fetchall()
    selected = []
    for country in COUNTRIES + ["PT", "CH", "BE", "NL", "MX"]:
        pool = [r for r in real if r[2] == country]
        rng.shuffle(pool)
        pool = pool[: 100 if country in COUNTRIES else 10]
        # Assign all receipts at a location to the same partition.
        groups = sorted(set(str(r[3]) if r[3] is not None else "proof-" + str(r[0]) for r in pool))
        rng.shuffle(groups)
        dev_groups = set(groups[: max(1, round(len(groups) * 0.3))])
        for proof, path, actual_country, location in pool:
            group = str(location) if location is not None else "proof-" + str(proof)
            selected.append(
                {
                    "id": f"op-{proof}",
                    "dataset": "open-prices",
                    "source_country": actual_country,
                    "expected": actual_country if country in COUNTRIES else "OTHER",
                    "split": "dev" if group in dev_groups else "test",
                    "group": group,
                    "image": f".cache/benchmark/real/{proof}.img",
                    "url": "https://prices.openfoodfacts.org/img/" + path,
                    "license": "CC-BY-SA-4.0",
                    "label_source": "store metadata",
                }
            )
    # Frozen before download outcomes or OCR quality are known; failed samples stay in denominator.
    write_jsonl(OUT / "real-manifest.jsonl", selected)
    print(
        json.dumps(
            {"real_manifest": dict(collections.Counter(r["source_country"] for r in selected))}
        ),
        flush=True,
    )
    failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(download, r["url"], ROOT / r["image"]): r for r in selected}
        for i, future in enumerate(as_completed(jobs), 1):
            row = jobs[future]
            try:
                future.result()
            except Exception as exc:
                failures.append({"id": row["id"], "stage": "download", "error": type(exc).__name__})
            if i % 100 == 0:
                print(json.dumps({"downloaded_or_failed": i, "failed": len(failures)}), flush=True)
    write_jsonl(OUT / "download-errors.jsonl", failures)
    dataset = "albertobarnabo/synthetic-receipts-ocr"
    with urllib.request.urlopen("https://huggingface.co/api/datasets/" + dataset) as response:
        revision = json.load(response)["sha"]
    paths = [CACHE / f"synthetic-eval-{i}.parquet" for i in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(
            pool.map(
                lambda i: download(
                    f"https://huggingface.co/datasets/{dataset}/resolve/{revision}/data/eval-0000{i}-of-00002.parquet",
                    paths[i],
                ),
                range(2),
            )
        )
    db.read_parquet([str(p) for p in paths]).create_view("synthetic")
    synth = db.sql("SELECT id, locale, full_text FROM synthetic ORDER BY id").fetchall()
    by_country = collections.defaultdict(list)
    pilot = {
        r["id"]
        for r in json.loads((ROOT / "research/samples.json").read_text(encoding="utf-8"))["samples"]
    }
    for ident, locale, transcript in synth:
        country = "GB" if locale == "UK" else locale
        by_country[country].append(
            {
                "id": ident,
                "dataset": dataset,
                "source_country": country,
                "expected": country,
                "text": transcript,
                "group": ident,
                "license": "Apache-2.0",
                "label_source": "generator locale",
                "revision": revision,
            }
        )
    synthetic = []
    for country, rows in sorted(by_country.items()):
        rng.shuffle(rows)
        dev_ids = {r["id"] for r in rows[: round(len(rows) * 0.2)]} | pilot
        image_ids = {r["id"] for r in rows[:40]}
        # Include image cases in both partitions instead of putting all 40 in development.
        image_ids = {r["id"] for r in rows[:: max(1, len(rows) // 40)][:40]}
        for row in rows:
            row["split"] = "dev" if row["id"] in dev_ids else "test"
            if row["id"] in image_ids:
                photo = db.execute(
                    "SELECT image_photo FROM synthetic WHERE id = ?", [row["id"]]
                ).fetchone()[0]
                path = CACHE / "benchmark" / "synthetic" / (row["id"] + ".jpg")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(photo["bytes"])
                row["image"] = str(path.relative_to(ROOT)).replace("\\", "/")
            synthetic.append(row)
    write_jsonl(OUT / "synthetic-manifest.jsonl", sorted(synthetic, key=lambda r: r["id"]))
    # Blind review assignment is independent of predictions and source-country order.
    reviewed = []
    for country in COUNTRIES:
        pool = [r for r in selected if r["source_country"] == country and r["split"] == "test"]
        reviewed.extend(pool[:10])
    rng.shuffle(reviewed)
    write_jsonl(
        OUT / "blind-review-assignment.jsonl",
        [{"review_id": i + 1, "id": r["id"], "image": r["image"]} for i, r in enumerate(reviewed)],
    )
    summary = {
        "seed": SEED,
        "synthetic_revision": revision,
        "real": len(selected),
        "synthetic": len(synthetic),
        "synthetic_images": sum("image" in r for r in synthetic),
        "download_failures": failures,
        "open_prices_sha256": hashlib.sha256(
            (CACHE / "open-prices.parquet").read_bytes()
        ).hexdigest(),
    }
    (OUT / "preparation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
