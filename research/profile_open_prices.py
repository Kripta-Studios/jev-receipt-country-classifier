"""Count unique real receipt proofs by store country, never by product origin."""

import json
from pathlib import Path
import urllib.request
import duckdb

root = Path(__file__).resolve().parents[1]
url = "https://huggingface.co/datasets/openfoodfacts/open-prices/resolve/main/prices.parquet"
target = root / ".cache" / "open-prices.parquet"
if not target.exists():
    with urllib.request.urlopen(url, timeout=90) as response:
        target.write_bytes(response.read())
db = duckdb.connect()
db.read_parquet(str(target)).create_view("prices")
countries = db.execute("""
    SELECT location_osm_address_country_code AS country,
           count(DISTINCT proof_id) AS receipts
    FROM prices WHERE proof_type = 'RECEIPT' AND proof_file_path IS NOT NULL
    GROUP BY 1 ORDER BY receipts DESC
""").fetchall()
totals = db.execute("""
    SELECT count(*), count(DISTINCT proof_id) FROM prices
    WHERE proof_type = 'RECEIPT' AND proof_file_path IS NOT NULL
""").fetchone()
conflicts = db.execute("""
    SELECT count(*) FROM (
      SELECT proof_id FROM prices
      WHERE proof_type = 'RECEIPT' AND proof_file_path IS NOT NULL
      GROUP BY proof_id HAVING count(DISTINCT location_osm_address_country_code) > 1
    )
""").fetchone()[0]
result = {
    "source": url,
    "date": "2026-09-24",
    "receipt_price_rows": totals[0],
    "unique_receipts": totals[1],
    "conflicting_country_proofs": conflicts,
    "country_codes": sum(country is not None for country, _ in countries),
    "countries": dict(countries),
}
(root / "research" / "open-prices-profile.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=True))
