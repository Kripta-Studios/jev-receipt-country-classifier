# Bundled demonstration evidence

`demo-receipt.jpg` is the unmodified `image_photo` for `eval-000001` from
[albertobarnabo/synthetic-receipts-ocr](https://huggingface.co/datasets/albertobarnabo/synthetic-receipts-ocr),
revision `ed46e02b9b1136f6b54847c1d4bce9e94d11e55c`, published under Apache 2.0.
The source is a generated receipt, not a real customer's upload.

`demos.json` includes that image's saved local OCR lines and bounding boxes, synthetic
reference text `eval-000004`, and authored control `control-shared-italian`.
Country responses come from the recorded experiment in
`evaluation/available-predictions.jsonl` and `evaluation/synthetic-dev-predictions.jsonl`.
They are replayed as historical responses and never presented as fresh inference.

Bounding boxes are OCR line regions. They are not verified semantic fields or
explanations of Jev's decision. The saved policy marks all candidates for review.

The Apache 2.0 license text is included in `APACHE-2.0.txt`.
