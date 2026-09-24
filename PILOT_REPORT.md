# Initial feasibility pilot (superseded by the expanded evaluation)

Date: 2026-09-24. This pilot verified connectivity; it was not sufficient to decide
whether Jev is suitable for production. See [EVALUATION_REPORT.md](EVALUATION_REPORT.md)
for the final experimental results and [WORK_PLAN.md](WORK_PLAN.md) for the archived protocol.

The trace-it repository was updated with `git pull --ff-only origin main` and was
already at commit `84c4c0463862640940efb1232344287a2d03bcf5`. Its source was not modified.
LocalOCR uses RapidOCR/ONNX Runtime with a Latin PP-OCRv5 reader; configured deployment
defaults use remote vision instead, so the experiment explicitly selected local mode.

The pilot used 25 synthetic evaluation transcripts (five per US/GB/DE/IT/FR), five
degraded images (one per country), and three hand-written controls. Jev received text
only, without country labels or source filenames. The API key was not saved to files.

| Input | Cases | Correct country | Abstentions | Wrong country asserted |
|---|---:|---:|---:|---:|
| Original transcript | 25 | 23 | 2 | 0 |
| Local OCR transcript | 5 | 4 | 1 | 0 |
| Hand-written controls | 3 | 2 | 1 expected | 0 |

All three controls matched their expected decision: two country labels and one
UNKNOWN. The table's country count excludes that expected abstention.

The US image produced the same abstention with its reference transcript. All five
image/text decisions agreed, but the OCR had numeric errors (e.g. `46,22` read as
`4622`). Correct country classification does not imply perfect OCR. The first OCR
request took 24.86 seconds including model loading; subsequent images took 3.56–6.56
seconds. The 33 Jev requests reported 22,340 input tokens and 2,640 output tokens,
with a median HTTP latency of 0.64 seconds. No billing statement was inspected.

## Datasets investigated

- [Open Prices](https://huggingface.co/datasets/openfoodfacts/open-prices): the downloaded
  snapshot contains 9,881 distinct receipt proof IDs with image paths, 92 country or
  territory codes, and 101 receipts without a country. Metadata labels require review.
  The snapshot has 163 Spanish, 4,443 French, 1,864 German, 433 US, 359 Italian, 282 UK,
  and 152 Canadian receipts. A price row is not a unique receipt. Image availability
  and legibility were not checked for all 9,881 paths. Data license: ODbL; images:
  CC BY-SA 4.0, according to the publisher.
- [Synthetic Receipts OCR](https://huggingface.co/datasets/albertobarnabo/synthetic-receipts-ocr):
  32,000 receipts, each with a clean and degraded render, reference text, word boxes and
  locale. 30,000 train / 2,000 evaluation. Five countries, no Spain. Apache 2.0.
- [SROIE](https://huggingface.co/datasets/jsdnrs/ICDAR2019-SROIE): inspected mirror has
  987 images with words, boxes and fields; no country column.
- [CORD v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2): Indonesian receipts
  and annotations, per the [original project](https://github.com/clovaai/cord).
- [CORU](https://huggingface.co/datasets/abdoelsayed/CORU): Arabic/English receipt tasks;
  multilingual coverage is not the same as verified country labels.
- [Goodspot EU/NA](https://huggingface.co/datasets/Goodspotai/goodspot-eu-na-receipts):
  labels only; the publisher explicitly excludes images.
- [mychen76 invoices and receipts](https://huggingface.co/datasets/mychen76/invoices-and-receipts_ocr_v1):
  2,238 records; insufficient country/provenance/license documentation in the inspected card.

The scripts and raw pilot results remain under `research/`. They are historical
evidence, not the production classifier or final evaluation.
