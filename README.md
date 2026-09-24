# Jev receipt country experiment

An experimental Python CLI comparing Jev prompts for receipt country classification.
Jev receives text; the existing **trace-it local OCR** extracts text from images.
Supported experiment labels: ES, FR, DE, IT, GB, US, CA, OTHER and UNKNOWN.

Read [the results](EVALUATION_REPORT.md), [Jev's role and API usage](docs/JEV_USAGE.md),
and [the independent data review](docs/DATA_REVIEW.md).

## Run

Python 3.12 or later. From this project directory:

```powershell
python -m pip install -e .
$env:TYPESAFE_API_KEY = '<your API key>'
python -m jev_tickets --text 'Store, Barcelona, Spain. Total EUR 12.00' --policy evaluation/frozen-policy.json
python -m jev_tickets --file receipt.txt --policy evaluation/frozen-policy.json
python -m jev_tickets --batch receipts.jsonl --output results.jsonl --policy evaluation/frozen-policy.json
```

Batch input contains one JSON object per line, with `id` and either `text` or `file`.
The saved experimental policy returns the model's `candidate` and routes it to review:
automatic acceptance was not calibrated before this experiment closed. Omitting
`--policy` uses exploratory defaults (probability 0.9, margin 0.15); these are not
validated accuracy guarantees. `--variant baseline-v1` selects the original prompt.
`--rules-only` runs the limited regex baseline without an API key or API request.

For images and PDFs, use the trace-it backend environment with its OCR dependencies:

```powershell
$env:TRACE_REPO = 'C:\path\to\trace-pay-main'
& "$env:TRACE_REPO\backend\.venv\Scripts\python.exe" -m jev_tickets --file receipt.jpg --model-dir .cache/models --policy evaluation/frozen-policy.json
```

The inspected source revision is `84c4c0463862640940efb1232344287a2d03bcf5`.
Download the `v5-latin` weights using trace-it's
`app.features.ingestion.tools.download_models` module and `--no-verifier`.
The adapter uses local RapidOCR / ONNX, not trace-it's remotely configured OCR provider.
Image inputs include JPEG, PNG and WebP; PDFs use native text where available.
Limits: 25 MiB per file, 18 megapixels per image, 20 PDF pages.

Only extracted text is sent to TypeSafe. Local `.cache` contains receipt images,
extractions and API responses. Credentials come from the environment; `.env.example`
is a template and is not loaded automatically.

## Evidence and reproduction

- `evaluation/*manifest.jsonl`: selected receipts and reference labels.
- `evaluation/*ocr.jsonl`: actual extraction outputs and explicit failures.
- `evaluation/*predictions.jsonl`: stored Jev answers and usage.
- `evaluation/closure-snapshot.json`: exact subset used when the experiment stopped.
- `evaluation/blind-labels.json`: 70 assistant visual judgments, including ambiguity.
- `evaluation/summary.json`, `TABLES.md`, `predictions.csv`: measured results.
- `research/`: dataset preparation, OCR, evaluation, policy selection and reporting.

The original full benchmark protocol is preserved in `WORK_PLAN.md`. The user
requested an early experimental close; the report identifies incomplete targets.
`research/close_experiment.py` reproduces the available subset using the response cache.
`python research/make_report.py` regenerates its tables without network calls.
Do not mix a resumed full benchmark with this closed experiment: use a new evaluation
directory and a fresh policy selection record.

```powershell
python -m unittest discover -s tests -v
```

## Larger datasets

| Dataset | Available scale and role | Main limitation |
|---|---|---|
| [Open Prices](https://huggingface.co/datasets/openfoodfacts/open-prices) | Inspected snapshot: 9,881 unique receipt proofs, 92 country/territory codes; real images and store metadata | Country is weak metadata, not independently verified visual ground truth; no complete reference transcription |
| [Synthetic receipts OCR](https://huggingface.co/datasets/albertobarnabo/synthetic-receipts-ocr) | 32,000 receipts, clean/degraded images and full text; 2,000 evaluation receipts across US, GB, DE, IT, FR | Synthetic layouts and generated location inconsistencies; no Spanish receipts |

Open Prices data is ODbL and its images CC BY-SA 4.0; the synthetic dataset declares
Apache 2.0. Keep source attribution and inspect the applicable licenses before
redistributing images. Dataset pins and hashes are in `evaluation/preparation.json`
and `research/open-prices-profile.json`. Product origin is never used as store country.

This is a research prototype, not a production certification or a trained OCR model.
