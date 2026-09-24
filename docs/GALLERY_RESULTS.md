# Difficult real gallery validation

This is a separate browser-gallery verification, not an extension of the published benchmark.
The eight photos were chosen after inspecting existing successful predictions and then visually
reviewing 28 candidates for wrinkles, blur, lighting and small print. This selection intentionally
favors challenging examples the system can resolve; it is not a random or held-out accuracy test.

Original images are unmodified. Source country metadata remains a weak reference, with assistant
visual evidence notes in the gallery manifest. The faded Spanish image has weaker location evidence.
No human transcription or character error rate is available. OCR scores do not measure text accuracy.

## Fresh computation

All images were read again with trace-it Latin PP-OCRv5 on CPU with result-cache reuse disabled.
Both Jev prompts were called again with `jev-1.13.0`, without response-cache lookup.
The first image includes model loading; later images reuse the loaded model, not saved OCR text.

| Receipt | Country reference | Difficulty | OCR seconds | Jev wall seconds | Original / focused | Mean OCR score | Est. API USD |
|---|---|---|---:|---:|---|---:|---:|
| op-65346 | US | Deep wrinkles, uneven illumination and faint small print. | 18.41 | 0.872 | US / US | 93.6% | 0.000093 |
| op-114865 | ES | Strong blue lighting, folds through the text and a curved receipt. | 9.88 | 0.658 | ES / ES | 86.0% | 0.000072 |
| op-20873 | FR | Heavy crumpling, shadow bands and distorted text baselines. | 7.64 | 0.654 | FR / FR | 92.7% | 0.000084 |
| op-33833 | DE | Small type, low contrast, distant capture and a horizontal fold. | 7.78 | 0.661 | DE / DE | 85.4% | 0.000101 |
| op-41050 | IT | Perspective distortion, dense tiny type, a hand and a curved edge. | 9.63 | 0.649 | IT / IT | 92.8% | 0.000102 |
| op-121503 | GB | Soft-focus header, folds, dense product lines and a long narrow image. | 15.12 | 0.651 | GB / GB | 91.2% | 0.000103 |
| op-12106 | CA | Creases across the store address, shadow, skew and pale print. | 9.23 | 0.656 | CA / CA | 74.8% | 0.000079 |
| op-116267 | ES | Blur and very low contrast obscure thin characters throughout. | 16.94 | 0.648 | ES / ES | 83.7% | 0.000073 |

Both prompts matched all eight source labels in this run (16 fresh responses). This says nothing
about the accuracy on arbitrary difficult receipts. The total estimated API cost was
USD 0.000707112, excluding local compute and subsequent browser smoke tests.
The first browser smoke test on the US image later took about 35.7 seconds end-to-end, including
about 34.9 seconds of OCR/model loading: latency varies with machine load and startup state.

Raw measurements: [gallery-validation.json](../research/gallery-validation.json).
Pricing: [TypeSafe models](https://docs.typesafe.ai/models), USD 0.042 per million input tokens,
output free, checked 2026-09-24. This is a token-based estimate, not an account invoice.

The web UI performs new runs when requested. It does not load these validation results as live output.

## Browser batch verification

The **Run all 8** action was also exercised end-to-end in the browser with a further
16 fresh Jev requests. Both prompts again matched all eight references. OCR times
in that batch ranged from 11.29 to 21.12 seconds; parallel Jev wall times ranged
from 0.66 to 0.83 seconds. These later requests are not included in the first-run
cost total above. Layout checks at widths 320, 390, 800, 1024 and 1440 pixels found
no page overflow, clipped result cards or hidden lines in the full text area.
