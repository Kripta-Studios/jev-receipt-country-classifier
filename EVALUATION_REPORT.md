# Jev receipt country experiment: results

Date: 2026-09-24. Model: `jev-1.13.0`.

## Conclusion

**Jev is useful for this experiment as a fast, inexpensive text country classifier.**
The focused prompt improves agreement with source country labels on real OCR and
synthetic text. It still makes unsupported country guesses, especially on ambiguous
French or Italian text. It should expose a candidate and allow abstention/review.
These results do not establish reliable unattended classification.

Jev does not read the images. The pipeline is image → trace-it local OCR → text →
Jev Choice (country) plus an independent Noul evidence question. OCR, dataset quality,
and country reasoning have separate failure modes. No model was trained or fine-tuned.

## Scope actually completed

The user requested closing this as an exploratory project before the longer benchmark
finished. OCR workers were stopped, and the final API comparison used only the saved
extractions. No further OCR was launched.

| Evidence | Completed | Earlier target |
|---|---:|---:|
| Real receipt image extraction attempts | 361 | 750 |
| Synthetic degraded image extractions | 170 | 200 |
| Synthetic reference transcriptions evaluated | 421 | 2,000 |
| Authored ambiguity/adversarial controls | 26 | 26 |
| Independent assistant visual labels | 70 | 70 |

Both prompt variants were run on each evaluated input. Image and transcription
cohorts can overlap and must not be added as independent receipts. All 750 real
images and 2,000 synthetic reference transcripts were prepared locally.

The available OCR subset reflects processing order and development prioritization.
It is not the completed, balanced benchmark. Original split assignments are retained:
193 real development images and 168 real test images. The saved automation policy
is explicitly disabled; real-data threshold selection was not completed.

## Measured comparison

Match means agreement with the dataset reference, with failures and abstentions kept
in the denominator. Dataset metadata can be wrong or impossible to recover visually.

| Input | N | Original prompt | Focused prompt |
|---|---:|---:|---:|
| Real images, available development + test | 361 | 285 / 361 (78.9%) | 309 / 361 (85.6%) |
| Real images, available test portion only | 168 | 127 / 168 (75.6%) | 138 / 168 (82.1%) |
| Synthetic reference text, development | 421 | 407 / 421 (96.7%) | 417 / 421 (99.0%) |
| Synthetic images, available development + test | 170 | 168 / 170 (98.8%) | 168 / 170 (98.8%) |
| Authored controls | 26 | 26 / 26 (100%) | 25 / 26 (96.2%) |

The focused prompt gains 24 real-image matches and 10 synthetic-text matches.
It loses one control: generic Italian-language text is assigned Italy when the
reference requires UNKNOWN. Thus the improved source-label match has a trade-off
in restraint on ambiguous evidence. The independent Noul output was implemented,
but its value as an acceptance gate has not been established.

The deliberately narrow regex baseline matches 16 / 168 real test references (9.5%).
It abstains on 147 and cannot demonstrate Jev's advantage over a strong geocoding or
address-parsing system; that comparison was not run.

## Reviewing the data and the mistakes

Before seeing real Jev outputs, I visually labeled 70 real images and marked eight
UNKNOWN. These are assistant judgments, not human gold labels. Only 19 of those
images overlap the completed test OCR subset: Jev agrees with 17 / 19, including
15 / 15 high-certainty labels. It assigns France to two of four indeterminate crops.
The subset is too small and selected by processing completion to generalize.

After the final run, I inspected real mismatch OCR and six corresponding source images:

- `op-15137`: a chocolate package, despite receipt-type metadata. Jev predicts Italy
  from packaging text; the selling store's country is not established. This combines
  dataset contamination with an unsupported country inference.
- `op-134354`: a German online-order screenshot with a shipping address and multiple
  sellers, but ES source metadata. Jev's DE answer matches visible context; neither
  that answer nor the metadata establishes the physical selling-store country.
- `op-10038`: the image shows New Westminster, whereas OCR corrupts it as
  `NEII WIESTMTNSTER`. Jev predicts US against CA metadata. The location cue is
  damaged by extraction, and the model makes an unsupported replacement inference.
- `op-64320`: French product lines without a clear location. Jev predicts FR against
  CA metadata. Language alone does not resolve France versus French-speaking Canada.
- `op-24920` and `op-118228`: product-line crops without adequate location evidence.
  Jev predicts FR, matching their metadata but disagreeing with the blind UNKNOWN
  review. A metadata match can therefore conceal unjustified certainty.

Many remaining UNKNOWN answers occur on product-only crops. They are source-label
mismatches, but abstention is reasonable when the location is absent. Four synthetic
text mismatches were also inspected; generated telephone numbers conflict with US
labels or fail to establish them. Details are in [the review notes](docs/DATA_REVIEW.md).

No reference labels were changed to improve scores, and no prompt was retuned after
this final real-image error inspection.

## OCR and API behavior

The existing Latin RapidOCR engine is usable for a prototype. It cannot recover a
missing header and can damage location words. The real snapshot has seven unusable
extractions: three oversized images rejected by the 18 MP limit, one image metadata
serialization error, and three empty extractions. These count as failures, not UNKNOWN.
The metadata serialization edge case remains a documented adapter limitation.

There were no provider failures in the expanded comparison. Fourteen prediction
records are extraction failures: seven inputs evaluated under two variants.
Synthetic image accuracy is not an OCR character-accuracy measurement; no CER/WER
claim is made, and the easy synthetic results do not predict real-world robustness.

The expanded run records 1,940 successful uncached responses, two cache replays,
1,759,736 input tokens and 174,600 output tokens. Median HTTP latency is 0.659 seconds.
At the inspected published input rate, successful uncached usage is approximately
**USD 0.074**, excluding the historical pilot. This is an estimate, not an account bill;
OCR compute and storage are excluded.

## Delivered

- CLI and library for text, images, PDF and JSONL batches.
- Versioned prompts, explicit OTHER/UNKNOWN, typed response validation, bounded
  retries, response caching and distinct extraction/provider errors.
- Larger dataset manifests, stored predictions, blind labels and reproducible metrics.
- English documentation and 15 passing unit tests.

Start with [README.md](README.md). Full split tables and raw measurements are in
[evaluation/TABLES.md](evaluation/TABLES.md) and
[evaluation/summary.json](evaluation/summary.json).

**Decision:** keep Jev for interactive experiments and candidate suggestions. The
main next improvement, if this is revisited, is screening real inputs for usable
store-location evidence and measuring abstention on genuinely ambiguous receipts.
The current experiment is closed; full benchmark completion and production
calibration are outside this delivered result.
