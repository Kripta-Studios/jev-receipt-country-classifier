# Measured evaluation tables

Generated from stored predictions. Country references are dataset metadata unless explicitly described as assistant review.

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
