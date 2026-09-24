# What Jev does in this application

Jev is a hosted, text-only decision model. It evaluates a state against typed
questions. It is suitable for a bounded country label decision. It is not our OCR
engine, image reader, free-text explanation generator, address database, calculator,
or a source of ground-truth labels.

The application calls `POST https://api.typesafe.ai/v1/systemone` with the pinned
model `jev-1.13.0`. Authentication is read from `TYPESAFE_API_KEY`. The API key never
enters prompts, cache identities, reports or source files. Country reference labels,
image paths and Open Prices location metadata are excluded from state.

## Decision contract

- `Choice`: one selected option and a probability distribution over configured
  countries, `OTHER` and `UNKNOWN`. `OTHER` means evidence supports a country outside the
  configured set. `UNKNOWN` is insufficient or conflicting observable evidence.
- `Noul`: in the improved prompt, one independent probability that the text has
  discriminating location evidence. It does not see the answer to the Choice in the
  same request. It is a diagnostic whose use as a gate must be selected on development data.
- `Score`: not needed. Country labels are categorical, not positions on an ordered scale.
- `confidence`: a summary of distribution concentration, not a verified probability
  that the selected country is correct. Acceptance uses separately evaluated criteria.

The provider permits up to 255 Choice options. The application supports up to 253
configured country keys plus OTHER and UNKNOWN. Keys are checked for two uppercase
letters; the application does not validate them against an ISO registry. The measured evaluation
uses seven named countries, so an unmeasured larger option set must not inherit its
performance claims or thresholds.

The question ID is an application lookup key; the model does not see it. Essential
instructions therefore appear inside the question. One receipt is one request state.
Questions about that receipt may share a request, but unrelated receipts are not
packed together. All arithmetic, metrics, thresholds and split assignments run in code.

## Prompt comparison

`baseline-v1` reproduces the initial pilot question. `focused-v2` explicitly targets
the selling store and explains distinguishing evidence for each country. It permits
multiple weak signals to support a decision without requiring a printed country name.
It distinguishes purchase location from headquarters, product origins and customer
addresses. Receipts longer than 80 lines preserve their first/last 25 lines plus
lines matching the evidence regex; this is a heuristic and can omit useful text.
The original extraction is retained for audit; no translation or invented evidence is added.

Jev is not asked to generate evidence quotations. `literal_evidence` contains regex
matches from actual input lines and is a separate, limited baseline. Such matches are
not a model explanation and may refer to the wrong entity; they do not override Jev.

## Boundaries and failure handling

Local OCR errors may remove the location before Jev sees it. An empty extraction,
ambiguous image, out-of-scope country, low certainty and provider failure are different
states. A network error never becomes an `UNKNOWN` prediction. Cached responses
preserve model identity and original usage, with zero new network calls on replay.

The client validates answer keys, options, finite probabilities, their sum, selected
maximum, Noul range, confidence and token counts. Retries are bounded for explicit
rate-limit/overload/server statuses and honor bounded Retry-After values. Ambiguous
transport failures are reported instead of silently repeated. Raw receipt instructions
are declared untrusted, but wording alone does not prove prompt-injection resistance.

The provider documents weaker multilingual performance than English, sensitivity to
irrelevant context and literal/ambiguous instructions, and adversarial-input failures.
Those limitations make a real multilingual test and an explicit review route necessary.

## Policy used for the published results

The saved [policy](../evaluation/frozen-policy.json) selects `focused-v2` and sets
`automatic_enabled` to false. Real-data acceptance calibration was not completed.
With `--policy evaluation/frozen-policy.json`, successful nonempty inputs expose
Jev's candidate while returning `status: review` and `country: null`. The Noul
answer is retained for inspection and is not a validated acceptance gate.

Without `--policy`, the CLI uses exploratory probability and margin thresholds of
0.9 and 0.15. Neither those defaults nor Jev's probability/confidence values promise
a corresponding real-world error rate. The `confidence` field is reported for
inspection; it is not the field used by the routing threshold.

## Official references inspected on 2026-09-24

- [HTTP API](https://docs.typesafe.ai/api): schema, answer types and errors.
- [Choice](https://docs.typesafe.ai/primitives/choice): criteria, option limit and parallel questions.
- [Noul](https://docs.typesafe.ai/primitives/noul): independent yes/no judgments.
- [State](https://docs.typesafe.ai/concepts/state): text-only input and data separation.
- [Confidence](https://docs.typesafe.ai/confidence): distribution summary and domain thresholds.
- [Models](https://docs.typesafe.ai/models): pinned ID, language support, no customer fine-tuning,
  and published input price of USD 0.042 per million tokens; output tokens free.
- [Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13): literal reading,
  irrelevant context, numerical/indirection weaknesses, adversarial inputs, and generation limits.

Prices are estimates from the published rate, not an inspected account invoice.
