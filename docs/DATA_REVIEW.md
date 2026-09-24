# Independent data review

The assistant inspected a prespecified sample of 70 real receipt images, ten from each
named source country. The sample was drawn from the test partition and presented as
18 image sheets with neutral review numbers. Source country metadata and Jev answers
were not consulted while assigning the labels. The prompts were already written and
were not changed using this test review.

Each judgment records a country or `UNKNOWN`, visible evidence, and a certainty level
in `evaluation/blind-labels.json`. The assignment mapping is in
`evaluation/blind-review-assignment.jsonl`. These are assistant judgments, not human
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
Original source labels remain unchanged, and the final report must distinguish those
measurements from observable evidence judgments.

## Independence limits

At experimental closure, only 19 of the 70 blind-reviewed images had completed OCR
and final Jev predictions. The other 51 retain visual labels without a measured
model comparison. Six source images were additionally inspected after prediction;
these error audits are described separately in `EVALUATION_REPORT.md` and are not
independent blind labels.

The source-country sample is balanced by receipt count, not by retailer, contributor,
or image quality. Store locations are disjoint between development and test, but
retail chains can appear in both. Exact duplicate images were checked: one duplicate
pair exists within a real partition and none crosses the split. Near-duplicate photos
and cropped portions of the same transaction have not been exhaustively eliminated.
This prevents claiming 750 fully independent real examples or universal production accuracy.
