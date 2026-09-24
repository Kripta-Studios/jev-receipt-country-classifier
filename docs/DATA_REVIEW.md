# Independent data review

The assistant inspected a prespecified sample of 70 real receipt images, ten from each
named source country. The sample was drawn from the test partition and presented as
18 image sheets with neutral review numbers. Source country metadata and Jev answers
were not consulted while assigning the labels. The prompts were already written and
were not changed using this test review.

Each judgment records a country or `UNKNOWN`, visible evidence, and a certainty level
in [blind-labels.json](../evaluation/blind-labels.json). The assignment mapping is in
[blind-review-assignment.jsonl](../evaluation/blind-review-assignment.jsonl). These are assistant judgments, not human
ground truth. Eight images were judged indeterminate. Medium-certainty inferences
are retained separately from high-certainty explicit location readings.

Several indeterminate images contain only product lines and prices. A correct store
metadata label can therefore be impossible to recover from the image. This distinction
matters when judging abstention: source-label mismatch is not always a model error.
Conversely, correctly guessing a source country from a familiar product layout is not
proof that the image contains a reliable location.

## Synthetic development anomalies

The assistant also inspected all four mismatches from `focused-v2` on the 421-sample
synthetic development partition. They all have generator label US:

- `eval-001627` prints `+1 (780) ...`, an Alberta, Canada area code, despite its US
  generator label. Jev gave Canada 0.52 and US 0.43. The rest of the receipt contains
  a generic street and dollar prices; the label is not an unambiguous observed country.
- `eval-000401` prints `+1 (869) ...`, which belongs to Saint Kitts and Nevis. Jev chose OTHER.
- `eval-000084` and `eval-001977` print unusual generated `+1 (595)` and `+1 (598)`
  telephone numbers with incomplete street addresses. Jev chose OTHER, which is not
  established by the visible evidence. UNKNOWN would be defensible; their US labels
  are not independently verified by a real address.

The area-code facts were checked against the [Canadian Numbering Administrator](https://www.cnac.ca/data/COCodeStatus_NPA780.htm)
and [NANPA territory table](https://www.nanpa.com/resources/area-code-map/territories).
No phone-number-based relabeling was used to inflate accuracy or tune to generator quirks.
Original source labels remain unchanged. The final report distinguishes source-label
measurements from observable evidence judgments.

## Independence limits

At the original experimental closure, only 19 of the 70 blind-reviewed images had
completed OCR and final Jev predictions. The [follow-up evaluation](OBSERVABLE_EVALUATION.md)
now covers all 70 attempts: 68 OCR successes and two extraction failures. Original
labels and both prompts were preserved. Against image review, the original prompt
matches 66/70 and the focused prompt 62/70; their unsupported country assertions on
the eight indeterminate images are 2/8 and 6/8. All eight ambiguous OCR texts were
also inspected after prediction; this additional audit is not blind annotation.
Six other source images were additionally inspected after the original prediction run;
these error audits are described separately in [EVALUATION_REPORT.md](../EVALUATION_REPORT.md)
and do not constitute additional independent blind labels.

The prepared sample contains 100 receipts per named country and 10 per out-of-scope
country. The 361-image evaluated subset is incomplete and is not country-balanced.
Neither selection balances retailer, contributor or image quality.
Store locations are disjoint between development and test, but
retail chains can appear in both. Exact duplicate images were checked: one duplicate
pair exists within a real partition and none crosses the split. Near-duplicate photos
and cropped portions of the same transaction have not been exhaustively eliminated.
This prevents claiming 750 fully independent real examples or universal production accuracy.
