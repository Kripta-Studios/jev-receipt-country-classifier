# Archived receipt country evaluation protocol

Status: closed exploratory experiment. This document preserves the original plan;
completed work and conclusions are in [EVALUATION_REPORT.md](EVALUATION_REPORT.md).

## Closure amendment

The experiment closed after a partial run on 2026-09-24.
Long OCR jobs were stopped. The available snapshot contains 361 real and 170
synthetic image extractions; the completed text development comparison contains
421 receipts. Remaining planned OCR and text test requests were not run.
The final comparison uses the available OCR subset and separately reports its
original development/test membership. Processing order affects inclusion, so this
does not complete the original benchmark protocol below. No real-data acceptance
policy was calibrated; the saved policy disables automatic acceptance.

## Research objective

Follow-up completed: all 70 pre-labelled real images now have recorded extraction
attempts and two prompt outcomes, with failures retained. The [observable-evidence
report](docs/OBSERVABLE_EVALUATION.md) separates metadata agreement from justified
decisions. The historical partial benchmark and frozen review-only policy remain intact.
The browser layout and real model workflow were also checked; see
[WEB_VALIDATION.md](docs/WEB_VALIDATION.md).

Implement receipt classification using Jev and trace-it OCR, evaluate it on substantially
more data, independently inspect and label receipt evidence, and determine whether Jev
is useful. Code, documentation and reports are written in English.

## Evaluation protocol (declared before expanded results)

- Real data: deterministic sample of up to 100 distinct proofs per country for ES, FR,
  DE, IT, GB, US, CA (target 700), plus out-of-scope country controls.
- Synthetic data: all 2,000 evaluation transcriptions, and 200 stratified degraded images.
- Separate development and test by store location for real receipts. Group clean/photo
  versions by receipt for synthetic data. Initial pilot receipts belong to development.
- Compare the original prompt, a documented improved prompt, and a deterministic
  evidence baseline. Select prompt and acceptance thresholds on development only.
- Freeze configuration before test results are inspected. Keep source-country accuracy
  distinct from independently adjudicated observable-country accuracy.
- Policy selection criterion: maximize real development coverage with at least 50
  accepted cases, observed accepted error <=2%, and Wilson 95% upper error <=5%.
  Search probability thresholds 0.5/0.7/0.8/0.9/0.95/0.98/0.99/1.0, fixed margin 0.15,
  and evidence gates 0/0.5/0.8 for the improved prompt. Disable automatic decisions
  if no policy qualifies. This empirical criterion is not a production guarantee.
- Independently review a prespecified stratified real sample before seeing Jev predictions.
  Review errors afterward in a separate audit. Record unavailable/ambiguous evidence.
- Record all denominators, download/OCR/provider failures, abstentions, accepted errors,
  per-country metrics, calibration, latency, usage and estimated API cost.
- No claim of human ground truth: independent reviews are by the assistant and explicitly
  identified as such. Dataset metadata is a weak reference until verified against evidence.

## Deliverables

- Reusable Python classifier, CLI for text/images/PDF and batch processing.
- Strict API validation, bounded retries, cache, separate errors and abstention.
- Reproducible dataset, OCR, benchmark and metric scripts; tests.
- English reports, reviewed labels, raw predictions, and a qualified go/no-go conclusion.

## Source baseline

Inspected trace-it main: `84c4c0463862640940efb1232344287a2d03bcf5`.
The same source revision is now recorded as the `external/trace-it` Git submodule.
Its source was not modified. Local OCR weights were stored in `.cache/models` and
are excluded from Git. The original 33-call pilot is retained in `research/` as
historical evidence; see [PILOT_REPORT.md](PILOT_REPORT.md).
