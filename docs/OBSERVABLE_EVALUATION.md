# Country visible in the document: follow-up evaluation

Date: 2026-09-24. Model: `jev-1.13.0`. Prompts: unchanged `baseline-v1` and
`focused-v2`. No training, prompt tuning or threshold selection used these results.

## What changed

The historical **309/361 (85.6%)** measures agreement with store metadata. It is
not verified accuracy at identifying a country visible in a receipt. A correct
store-country label may describe a photo that shows only products and prices.
A model can therefore disagree with metadata by reasonably answering UNKNOWN,
or match metadata by making an unsupported guess.

We completed evaluation of the entire existing **70-image visual-review cohort**,
ten images per named source country from the test partition. Its image labels
were assigned by the assistant before consulting metadata or Jev predictions.
The labels were preserved. They contain 62 country judgments and eight UNKNOWNs.
These are assistant judgments, including medium-certainty judgments, not human
ground truth. This small cohort is not a representative production sample.

All 70 images were submitted to the existing OCR adapter, with its cache enabled.
68 yielded text; two exceeded its 18-megapixel limit. The saved OCR records contain
text, coordinates, source hashes and errors. Both fixed prompts received the same
extraction, without reference labels: **136 fresh, uncached API requests**, plus
four extraction-error records. All 140 case/prompt records remain in the report.
The 70-image cohort overlaps the historical benchmark; do not add their totals.

## Results

| Measurement | Original | Focused |
|---|---:|---:|
| Matches store metadata, failures included | 62/70 (88.6%) | 66/70 (94.3%) |
| Matches reviewed image country or justified UNKNOWN | 66/70 (94.3%) | 62/70 (88.6%) |
| Correct country on images judged observable | 60/62 (96.8%) | 60/62 (96.8%) |
| Reasonable abstentions on indeterminate images | 6/8 | 2/8 |
| Unsupported country assertions on indeterminate images | 2/8 | 6/8 |
| Unsupported assertions that happen to match metadata | 2 | 6 |
| Unsupported assertions with candidate probability ≥0.9 | 0 | 5 |
| Extraction failures, included in denominators | 2 | 2 |
| Provider failures | 0 | 0 |

Both prompts identified the reviewed country on all **60 successfully extracted,
observable** images. The 62 denominator also includes `op-28963` and `op-48271`,
whose visible German addresses could not be processed under the size limit.
Conditional success on those 60 images is not overall pipeline accuracy.

The focused prompt gains four metadata matches and loses four justified decisions.
This reverses the ranking when the reference changes from metadata to reviewed
image evidence. Calling it universally “better” would misrepresent the experiment.

## Inspecting all eight indeterminate cases

The assistant additionally read the extracted text for all eight after this run.
The OCR text contains no recovered merchant address that resolves the visual
review's uncertainty. This is a subsequent error audit, not a second blind review.
Full text and predictions are available in the linked artifacts below.

| Image | Visible / extracted evidence | Original | Focused | Focused probability / Noul |
|---|---|---|---|---:|
| `op-7604` | Cropped English product lines and dollars | UNKNOWN | UNKNOWN | 0.89 / 0.14 |
| `op-118228` | Rotated French product list; no location | FR | FR | 0.98 / 0.53 |
| `op-24920` | French product names and amounts only | UNKNOWN | FR | 0.52 / 0.22 |
| `op-107951` | M&S, English and sterling amounts; no store location | UNKNOWN | GB | 0.96 / 0.21 |
| `op-22911` | Two product lines, British product names and sterling | UNKNOWN | GB | 0.93 / 0.27 |
| `op-59498` | Obscured Italian receipt fragment, IVA and total | IT | IT | 0.98 / 0.47 |
| `op-111937` | Four Italian product lines | UNKNOWN | IT | 0.91 / 0.39 |
| `op-7607` | Cropped English product lines and dollars | UNKNOWN | UNKNOWN | 0.88 / 0.14 |

A brand, product origin, shared language or currency can make a country plausible
without uniquely establishing the issuing merchant's location. In particular,
sterling does not by itself distinguish the UK from other sterling jurisdictions.
This review uses the experiment's conservative evidence requirement.

The separate Noul judgment is much lower than the country probability on these
overreaches. That makes it worth investigating on development data; choosing a
threshold on these already inspected test examples would not validate a filter.
Automatic acceptance remains disabled. No new evidence gate is claimed here.

## Different data problems need different labels

| Problem | Example | Treatment |
|---|---|---|
| Valid metadata, insufficient visible location | The eight indeterminate cases above | Preserve metadata; reviewed image target is UNKNOWN |
| Wrong document type | `op-15137`, chocolate packaging among receipt records | Record contamination; packaging country is not purchase country |
| Unclear issuing merchant | `op-134354`, order screenshot with shipping address and multiple sellers | Do not treat shipping address as merchant-country truth |
| Location damaged by OCR | `op-10038`, New Westminster corrupted in extraction | Review image and text separately; do not attribute the entire failure to Jev |
| Inconsistent generated cues | `eval-001627`, US generator label with a Canadian area code | Preserve generator label and flag inconsistency; do not silently relabel |

The last four examples belong to the earlier diagnostic audit, not the 70-image
score. Their details and original provenance are in [DATA_REVIEW.md](DATA_REVIEW.md)
and [EVALUATION_REPORT.md](../EVALUATION_REPORT.md).

Image-based reference labels evaluate **OCR plus Jev together**. They do not establish
which country is recoverable from every OCR transcription. Only the eight ambiguous
transcriptions received the additional text audit here. A separate, independently
reviewed text reference is needed to isolate Jev from OCR across the whole cohort.

## Does Jev help?

Yes, as an inexpensive experimental text classifier that returns reviewable
candidates. This run used 130,474 input and 12,240 output tokens, an estimated
**USD 0.005479908** at the recorded input rate of USD 0.042/M and free output.
This excludes OCR hardware costs and the separate browser validation calls.

The original prompt was more conservative on this reviewed cohort. The focused
prompt is useful for demonstrating the trade-off between metadata agreement and
unsupported inference. Neither is validated for automatic decisions. These results
do not establish superiority over a strong rules/geocoding system or another model.

## Reproduce locally

From the repository root, Python 3.12 or later. Exact offline reproduction needs
only committed files, without images, OCR models, an API key or network access:

```powershell
python research/evaluate_observable.py
python -m unittest discover -s tests -v
```

Expected: the table above, 28 passing tests. The script regenerates the summary,
case CSV/JSONL and identical browser summary. Historical 361-image results remain
in their original files and are not rewritten by this script.

To make new Jev requests on the recorded OCR text, keeping published results intact:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
python research/evaluate_observable.py --predict --output-dir .cache/observable-replay
```

This resumes existing case/prompt records in the chosen directory. Choose a new
directory name for another fully fresh API run. Requests bypass the response cache.
Saved request hashes are checked against the supplied OCR text and current prompts;
changed inputs cannot silently reuse earlier predictions from the same directory.
Service/model changes and inference variability can change the new answers.

To also repeat OCR, complete the [OCR installation](../README.md#images-and-pdfs),
then fetch the exact cohort and verify available recorded image hashes:

```powershell
python research/evaluate_observable.py --download
& '.\external\trace-it\backend\.venv\Scripts\python.exe' research/ocr_benchmark.py --trace-repo external/trace-it --workers 3 --manifest observable/manifest.jsonl --output observable/replay-ocr.jsonl
python research/evaluate_observable.py --predict --ocr evaluation/observable/replay-ocr.jsonl --output-dir .cache/observable-new-ocr
```

The OCR command resumes recorded attempts, including errors, and can reuse the
local OCR cache. To force model inference, add `--force-recompute` to that command
and choose a new OCR output filename; completed output records are never overwritten.
Source images can disappear or change; a hash mismatch stops the download check.
The two failed historical extractions have no saved image hash. No claim of exact
future network or inference reproducibility is made.

## Artifacts

- [Unchanged visual labels](../evaluation/blind-labels.json) and [review assignments](../evaluation/blind-review-assignment.jsonl).
- [Fixed cohort and source URLs](../evaluation/observable/manifest.jsonl).
- [OCR text, boxes and failures](../evaluation/observable/ocr.jsonl).
- [Fresh model decisions and usage](../evaluation/observable/predictions.jsonl).
- [Per-case comparison CSV](../evaluation/observable/cases.csv) and [JSONL](../evaluation/observable/cases.jsonl).
- [Generated measurements](../evaluation/observable/summary.json).
- [Metric implementation](../jev_tickets/evaluation.py) and [reproduction script](../research/evaluate_observable.py).
