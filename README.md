# Jev receipt country classifier

An experimental Python CLI comparing Jev prompts for receipt country classification.
Jev receives text; the existing **trace-it local OCR** extracts text from images.
Supported experiment labels: ES, FR, DE, IT, GB, US, CA, OTHER and UNKNOWN.

## Results at a glance

| Evaluated input | N | Original prompt | Focused prompt |
|---|---:|---:|---:|
| Real images through local OCR | 361 | 78.9% | 85.6% |
| Synthetic reference text | 421 | 96.7% | 99.0% |
| Synthetic images through local OCR | 170 | 98.8% | 98.8% |

These are matches against dataset labels, including failures in the denominator.
The real-image cohort is an incomplete processing-order subset; the text cohort is
development data. They are exploratory results, not a production accuracy estimate.
The focused prompt also falls from 26/26 to 25/26 on authored ambiguity controls.

**Follow-up using reviewed visible evidence:** on the full 70-image assistant-reviewed
cohort, the original prompt matches the image review in **66/70** cases and the focused
prompt in **62/70**, including two extraction failures. On eight indeterminate images,
they make **2 vs 6 unsupported country assertions**. The focused prompt matches more
store labels but makes more unjustified guesses. See the [case audit, measurements and
reproduction commands](docs/OBSERVABLE_EVALUATION.md). These assistant labels are not
human ground truth; the cohort overlaps the historical benchmark.

Read [the results](EVALUATION_REPORT.md), [Jev's role and API usage](docs/JEV_USAGE.md),
and [the independent data review](docs/DATA_REVIEW.md).
For an introduction, read [architecture, prompt differences and alternatives to
Jev](docs/ARCHITECTURE.md).

## Run

**Starting on another machine?** Follow [the complete installation and deployment
guide](docs/DEPLOYMENT.md). It includes Windows PowerShell and Linux/macOS commands,
OCR/model installation, the bundled browser datasets, live Jev, offline evaluation,
Docker recorded mode, remote live access through SSH, and troubleshooting.

### Browser playground

From a clone of this repository:

```powershell
python -m jev_tickets.web
```

Open **http://127.0.0.1:8000** to inspect a receipt, click its OCR rectangles and
compare the two prompts using saved results. No API key or OCR installation is
needed for the demo. See [browser setup and Docker deployment](docs/WEB.md) for
live text/image processing and a small deployable container.

Live mode also includes **eight difficult real receipts** with folds, blur, shadows
and small print. Run them individually or together using real OCR and fresh Jev
requests, with measured latency, token usage, estimated cost and confidence values.
See [gallery results and selection limits](docs/GALLERY_RESULTS.md).

### Command line

Python 3.12 or later. Clone the repository, then run the commands from its root:

```powershell
git clone --recurse-submodules https://github.com/Kripta-Studios/jev-receipt-country-classifier.git
cd jev-receipt-country-classifier
python -m pip install -e .
$env:TYPESAFE_API_KEY = '<your API key>'
python -m jev_tickets --text 'Store, Barcelona, Spain. Total EUR 12.00' --policy evaluation/frozen-policy.json
```

After creating your own UTF-8 `receipt.txt` or the batch file described below:

```powershell
python -m jev_tickets --file receipt.txt --policy evaluation/frozen-policy.json
python -m jev_tickets --batch receipts.jsonl --output results.jsonl --policy evaluation/frozen-policy.json
```

Batch input contains one JSON object per line, with `id` and either `text` or `file`.
For example, save this as `receipts.jsonl` (file paths are relative to the current
working directory):

```jsonl
{"id":"example-text","text":"Store, Barcelona, Spain. Total EUR 12.00"}
{"id":"example-file","file":"receipt.txt"}
```

The saved experimental policy returns the model's `candidate` and routes it to review:
automatic acceptance was not calibrated before this experiment closed. Omitting
`--policy` uses exploratory defaults (probability 0.9, margin 0.15); these are not
validated accuracy guarantees. `--variant baseline-v1` selects the original prompt.
`--rules-only` runs the limited regex baseline without an API key or API request.

### Images and PDFs

OCR uses the [trace-it](https://github.com/Martinhdeez/trace-it) submodule at
`external/trace-it`, pinned to the source revision used in the experiment. For an
existing clone, initialize it with `git submodule update --init --recursive`.
Text classification and offline report generation do not require the submodule.

The OCR backend requires **Python 3.12**. With `uv` installed, the following Windows
commands create its environment from the tracked lockfile and download the model
weights. Run them from this repository's root:

If `uv` is unavailable, install it with `python -m pip install uv` first.

```powershell
$env:TRACE_REPO = (Resolve-Path 'external/trace-it').Path
$experimentRoot = (Get-Location).Path
$ocrPython = Join-Path $env:TRACE_REPO 'backend\.venv\Scripts\python.exe'
Push-Location (Join-Path $env:TRACE_REPO 'backend')
try {
    uv sync --frozen --no-dev --python 3.12
    & $ocrPython -m app.features.ingestion.tools.download_models --profile v5-latin --no-verifier --output (Join-Path $experimentRoot '.cache\models')
} finally {
    Pop-Location
}
& "$env:TRACE_REPO\backend\.venv\Scripts\python.exe" -m jev_tickets --file receipt.jpg --model-dir .cache/models --policy evaluation/frozen-policy.json
```

The inspected source revision is `84c4c0463862640940efb1232344287a2d03bcf5`.
The submodule contains source and dependency definitions; model weights and virtual
environments are downloaded locally and excluded from Git. See [OCR source and
model provenance](docs/OCR.md) for the model revisions and relevant files.
The adapter uses local RapidOCR / ONNX, not trace-it's remotely configured OCR provider.
Image inputs include JPEG, PNG and WebP; PDFs use native text where available.
OCR/PDF adapter limits: 25 MiB per file, 18 megapixels per image, 20 PDF pages.
Jev input is limited to 80,000 characters. PDF support is implemented but was not
measured in the image benchmark. A known image metadata serialization error is
documented in the results.

Only receipt text is sent to TypeSafe, with the model and question definitions;
images and reference labels are excluded. The ignored `.cache` directory holds
downloaded images, model weights and runtime caches. Published research extractions
and predictions are tracked under `evaluation/`. Credentials come from the environment;
`.env.example` is a template and is not loaded automatically.

## Evidence and reproduction

Use the [step-by-step reproduction guide](docs/REPRODUCIBILITY.md) to regenerate
the published tables offline or rerun the synthetic text comparison against Jev.

- `evaluation/*manifest.jsonl`: selected receipts and reference labels.
- `evaluation/real-ocr.jsonl` and `synthetic-ocr.jsonl`: canonical extractions and failures.
  `real-ocr-reverse.jsonl` is an intermediate worker output already merged into the
  canonical real file; do not count it as another cohort.
- `evaluation/*predictions.jsonl`: stored Jev answers and usage.
- `evaluation/closure-snapshot.json`: exact subset used when the experiment stopped.
- `evaluation/blind-labels.json`: 70 assistant visual judgments, including ambiguity.
- [summary.json](evaluation/summary.json), [TABLES.md](evaluation/TABLES.md) and
  [predictions.csv](evaluation/predictions.csv): measured results.
- `research/`: dataset preparation, OCR, evaluation, policy selection and reporting.

The original protocol is preserved in [WORK_PLAN.md](WORK_PLAN.md). The experiment
closed after a partial run; the report identifies incomplete targets. A fresh clone
includes everything needed to recompute the published tables offline:

```powershell
python research/make_report.py
python -m unittest discover -s tests -v
```

No API key, OCR models, image downloads or research extras are needed for those two
commands. Regeneration writes derived files under `evaluation/`.

Re-running inference is different from recomputing metrics. Images, source parquet
files, weights and the API cache are excluded from Git. `close_experiment.py` skips
stored predictions; if they are missing, it can make new paid API calls. It also
rewrites the closure snapshot, so it is not the offline report-reproduction command.
See [research workflow and snapshot limits](docs/REPRODUCIBILITY.md) before a new run.

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
