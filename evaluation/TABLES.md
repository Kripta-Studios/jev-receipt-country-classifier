# Measured evaluation tables

Generated from stored predictions. Country references are dataset metadata unless explicitly described as assistant review.

See the [evaluation report](../EVALUATION_REPORT.md) for scope and interpretation, and [reproduction notes](../docs/REPRODUCIBILITY.md) for offline commands.

The image cohorts are incomplete processing-order subsets. The synthetic text cohort is development data. Controls use authored expected answers.

N includes failures and abstentions. Raw match is agreement with the reference label, including an expected UNKNOWN or OTHER. It is not verified real-world accuracy.

All Jev rows use the saved disabled automation policy, so Accepted and Coverage are zero by configuration. The literal-rules row uses its own permissive routing rule. These columns are not a calibrated coverage comparison.

Assistant review rows use focused-v2 and overlap the real test cohort; they are not additional receipts. Image and reference-text cohorts can also overlap.

| Dataset / variant | N | Raw match | UNKNOWN | OTHER | Accepted | Accepted errors | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| controls/test/baseline-v1 | 26 | 100.0% | 8 | 5 | 0 | 0 | 0.0% |
| controls/test/focused-v2 | 26 | 96.2% | 7 | 5 | 0 | 0 | 0.0% |
| real/dev/baseline-v1 | 193 | 81.9% | 30 | 9 | 0 | 0 | 0.0% |
| real/dev/focused-v2 | 193 | 88.6% | 16 | 11 | 0 | 0 | 0.0% |
| real/test/baseline-v1 | 168 | 75.6% | 35 | 24 | 0 | 0 | 0.0% |
| real/test/focused-v2 | 168 | 82.1% | 24 | 26 | 0 | 0 | 0.0% |
| synthetic-image/dev/baseline-v1 | 47 | 95.7% | 0 | 1 | 0 | 0 | 0.0% |
| synthetic-image/dev/focused-v2 | 47 | 95.7% | 0 | 1 | 0 | 0 | 0.0% |
| synthetic-image/test/baseline-v1 | 123 | 100.0% | 0 | 0 | 0 | 0 | 0.0% |
| synthetic-image/test/focused-v2 | 123 | 100.0% | 0 | 0 | 0 | 0 | 0.0% |
| synthetic/dev/baseline-v1 | 421 | 96.7% | 6 | 6 | 0 | 0 | 0.0% |
| synthetic/dev/focused-v2 | 421 | 99.0% | 0 | 3 | 0 | 0 | 0.0% |
| assistant_visual_review | 19 | 89.5% | 2 | 0 | 0 | 0 | 0.0% |
| assistant_high_certainty_review | 15 | 100.0% | 0 | 0 | 0 | 0 | 0.0% |
| assistant_indeterminate_review | 4 | 50.0% | 2 | 0 | 0 | 0 | 0.0% |
| real_test_literal_rules | 168 | 9.5% | 147 | 0 | 18 | 2 | 10.7% |

## Usage

Expanded experiment only; historical pilot excluded. There are 1,956 prediction records: 1,940 successful uncached responses, 2 cache replays and 14 failed records. Extraction failures: 14; provider failures: 0. Counts include both prompt variants. The estimated price uses the rate inspected on 2026-09-24; HTTP latency excludes OCR.

```json
{
  "successful_uncached_requests": 1940,
  "input_tokens": 1759736,
  "output_tokens": 174600,
  "estimated_usd_at_published_rate": 0.07390891200000001,
  "median_http_s": 0.6588535000000775,
  "cached_records": 2,
  "failed_records": 14,
  "note": "Successful responses only. Failed delivered requests may have unknown usage. Not an invoice."
}
```

Wilson intervals and calibration values in summary.json treat samples as independent. Repeated stores and weak labels limit that interpretation. Assistant reviews are not human gold labels.
