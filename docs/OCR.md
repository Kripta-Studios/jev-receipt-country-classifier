# OCR source and model provenance

For step-by-step installation commands on Windows and Linux/macOS, see
[DEPLOYMENT.md](DEPLOYMENT.md#3-install-the-ocr-environment-and-weights).

## Pinned upstream source

The Git submodule at `external/trace-it` points to
[Martinhdeez/trace-it](https://github.com/Martinhdeez/trace-it) at commit
`84c4c0463862640940efb1232344287a2d03bcf5`, the revision inspected and used for the
experiment. The parent repository records this exact commit rather than following
upstream `main` automatically.

```powershell
git submodule update --init --recursive
git submodule status
```

The submodule's detached HEAD is normal. Updating upstream source or weights creates
a different OCR configuration and does not inherit the published measurements.

## What this project reuses

| Source | Role |
|---|---|
| [LocalOCR](https://github.com/Martinhdeez/trace-it/blob/84c4c0463862640940efb1232344287a2d03bcf5/backend/app/features/ingestion/ocr/local.py) | RapidOCR / ONNX Runtime extraction, preprocessing and cache behavior |
| [Settings](https://github.com/Martinhdeez/trace-it/blob/84c4c0463862640940efb1232344287a2d03bcf5/backend/app/features/ingestion/config.py) | Reader configuration, model directories and execution settings |
| [Model downloader](https://github.com/Martinhdeez/trace-it/blob/84c4c0463862640940efb1232344287a2d03bcf5/backend/app/features/ingestion/tools/download_models.py) | Pinned Hugging Face model revisions, hashes and character dictionary generation |
| [Backend dependencies](https://github.com/Martinhdeez/trace-it/blob/84c4c0463862640940efb1232344287a2d03bcf5/backend/pyproject.toml) | Python 3.12 requirement and OCR libraries |
| [Dependency lockfile](https://github.com/Martinhdeez/trace-it/blob/84c4c0463862640940efb1232344287a2d03bcf5/backend/uv.lock) | Backend environment versions |
| [Project adapter](../jev_tickets/ocr.py) | Image/PDF handling and conversion of OCR lines to classifier input |

The adapter imports the backend directly. No trace-it web server, database, frontend
or invoice decision service is needed. Set `TRACE_REPO` or `--trace-repo` to the
submodule path; the CLI does not discover it automatically.

## Models used in this experiment

Downloader profile: `v5-latin`, with `--no-verifier`.

| Component | Hugging Face repository | Pinned revision |
|---|---|---|
| Text detector | `PaddlePaddle/PP-OCRv5_mobile_det_onnx` | `df0bd9dee2bc627e80a2a1798ccab35a332e22d6` |
| Latin text recognizer | `PaddlePaddle/latin_PP-OCRv5_mobile_rec_onnx` | `89d3a50e2c27e2e7cceeab0e944c25c807d5db4f` |

The downloader writes `det/inference.onnx`, `rec/inference.onnx`, model metadata,
`rec/keys.txt` and a hash manifest under `.cache/models`. These files are not stored
in the submodule or parent repository. The pinned downloader is the source of truth
for download filenames and model revision IDs.

The adapter explicitly selects local OCR and disables vision/text provider lists.
The experiment used CPU execution, without the optional server-model verification
pass. Upstream disables the OCR orientation classifier (`use_cls=False`); the adapter
handles EXIF orientation. These are separate mechanisms. The adapter's
`ocr_profile="experimental"` setting is separate from the downloader's `v5-latin`
weight selection.

Images are converted to RGB PNG for extraction. Native PDF text is used when a page
has at least 40 alphanumeric characters; otherwise that page is rendered at 180 DPI
for OCR. PDF support was not measured in this receipt-image experiment.

See the [README setup commands](../README.md#images-and-pdfs) and the
[evaluation report](../EVALUATION_REPORT.md) for observed failures and limitations.
Jev receives the resulting text and performs country classification; it is not one
of the OCR models above.
