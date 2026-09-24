# Reproducing the experiment

## Recompute the published results offline

From the repository root, with Python 3.12 or later:

```powershell
python research/make_report.py
python -m unittest discover -s tests -v
```

These commands use only the Python standard library and tracked files. They do not
require an API key, an initialized trace-it submodule, images, model weights or a local cache.
The report script reads the stored predictions, policy, review assignments and labels,
then writes `evaluation/summary.json`, `review-comparison.json`, `predictions.csv`
and `TABLES.md`. It does not make new predictions.

Expected checks: 25 unit tests pass (15 classifier tests and ten browser-server tests);
the report prints 16 metric groups, 19 reviewed
predictions, 1,940 successful uncached requests from the recorded run and an estimated
historical usage cost of USD 0.073908912. Recomputing these values is free of API calls.
See [TABLES.md](../evaluation/TABLES.md) for the full expected table.

### Verification performed for this documentation update

- Copied the publishable project files into a fresh directory without the API key,
  cache or submodule, regenerated the reports and compared them with the saved
  summary, review comparison and Markdown tables: identical results.
- Ran all 15 unit tests successfully in that directory.
- Installed the pinned submodule backend using the documented `uv sync` command
  and read synthetic image `eval-000001` using the existing pinned model weights:
  19 text lines and 406 characters were extracted.
- Executed the transcript-preparation block below: 421 inputs were produced.

The full benchmark and live Jev comparison were not rerun for this documentation
update. The published measurements remain those of the original experiment.

## Repeat the synthetic text comparison with live Jev calls

This reruns the same 421 development transcripts under both prompts without images
or OCR. It requires an API key and may make up to 842 requests on an empty cache.
The saved policy exposes each `candidate` but returns it for review; the comparison
below scores that candidate, rather than the deliberately null accepted `country`.

From the project root in PowerShell, prepare input from the tracked manifest:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
@'
import json
from pathlib import Path
rows = [json.loads(s) for s in Path('evaluation/synthetic-manifest.jsonl').read_text(encoding='utf-8').splitlines()]
rows = [r for r in rows if r['split'] == 'dev']
out = Path('.cache/replay')
out.mkdir(parents=True, exist_ok=True)
(out / 'input.jsonl').write_text(''.join(json.dumps({'id': r['id'], 'text': r['text']}) + '\n' for r in rows), encoding='utf-8')
print(f'Prepared {len(rows)} transcripts.')
'@ | python -

python -m jev_tickets --batch .cache/replay/input.jsonl --variant baseline-v1 --policy evaluation/frozen-policy.json --cache-dir .cache/replay/cache --output .cache/replay/baseline-v1.jsonl
python -m jev_tickets --batch .cache/replay/input.jsonl --variant focused-v2 --policy evaluation/frozen-policy.json --cache-dir .cache/replay/cache --output .cache/replay/focused-v2.jsonl
```

Then count source-label matches, including any failed requests in the denominator:

```powershell
@'
import json
from pathlib import Path
manifest = [json.loads(s) for s in Path('evaluation/synthetic-manifest.jsonl').read_text(encoding='utf-8').splitlines()]
expected = {r['id']: r['expected'] for r in manifest if r['split'] == 'dev'}
for variant in ('baseline-v1', 'focused-v2'):
    rows = [json.loads(s) for s in Path(f'.cache/replay/{variant}.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows) == len(expected) and {r['id'] for r in rows} == set(expected)
    correct = sum(r.get('candidate') == expected[r['id']] for r in rows)
    errors = sum(r['status'] == 'error' for r in rows)
    print(f'{variant}: {correct}/{len(rows)} ({correct/len(rows):.1%}), errors={errors}')
'@ | python -
```

The historical counts are 407/421 for `baseline-v1` and 417/421 for `focused-v2`.
New hosted responses may differ. New outputs stay under `.cache/replay`; they do not
replace the published evidence. The CLI processes a batch sequentially, so this is
slower than the concurrent research runner. Subsequent identical calls can use the
replay cache and do not constitute new independent measurements.

### Canonical evidence

| File in `evaluation/` | Role |
|---|---|
| `available-predictions.jsonl` | 1,114 records: both prompts on 361 real images, 170 synthetic images and 26 authored controls |
| `synthetic-dev-predictions.jsonl` | 842 records: both prompts on 421 reference transcripts |
| `real-ocr.jsonl` | 361 real extraction attempts, including explicit errors and empty text |
| `synthetic-ocr.jsonl` | 170 synthetic image extractions |
| `real-ocr-reverse.jsonl` | Intermediate worker output merged into `real-ocr.jsonl`; not additional examples |
| `closure-snapshot.json` | IDs included at experimental closure |
| `frozen-policy.json` | Recorded focused prompt choice with automatic acceptance disabled |
| `blind-labels.json` | 70 assistant visual judgments; 19 overlap the completed real test predictions |

The reporter reads every `*-predictions.jsonl` file in `evaluation/`. Keep this
directory limited to the closed experiment; mixing additional runs can double-count
requests or replace metric groups. Historical pilot files in `research/` are excluded
from the expanded metrics and cost estimate.

## Run a new experiment

Use a separate checkout and archive its existing evaluation outputs before starting
a new run. Research scripts use fixed paths relative to the repository root; there
is no general `--evaluation-dir` option. They can overwrite manifests and append
predictions, so running them in this published results directory changes the evidence.

The workflow below documents the script dependencies. It is not necessary for offline
report reproduction and was not rerun during the documentation review.

| Stage | Script | Requirements and behavior |
|---|---|---|
| Profile source data | `research/profile_open_prices.py` | DuckDB, network and an existing `.cache` directory; downloads current Open Prices parquet if absent |
| Prepare manifests/images | `research/prepare_benchmark.py` | DuckDB, Open Prices parquet, historical `research/samples.json` and network; writes manifests, downloads images and selects synthetic evaluation data |
| Extract text | `research/ocr_benchmark.py` | trace-it backend environment, weights and downloaded images; resumes by existing IDs, including recorded errors |
| Compare prompts | `research/run_benchmark.py` | `TYPESAFE_API_KEY` for uncached requests; image cohorts require complete OCR for the selected partition |
| Select a policy | `research/select_policy.py` | Complete real development predictions and no existing frozen policy; this stage was not completed in the closed experiment |
| Produce tables | `research/make_report.py` | Stored predictions, policy and review files; no network |

Install the dataset tools with `python -m pip install -e '.[research]'`.
OCR setup is described in the [README](../README.md#images-and-pdfs). For CLI arguments,
use `--help` with `ocr_benchmark.py` and `run_benchmark.py` before launching a run.
Test requests in `run_benchmark.py` require a saved policy file.

`research/close_experiment.py` was used once to finish the available subset after
the long OCR run stopped. It skips existing prediction IDs, consults a local cache
when available, and calls Jev for remaining inputs. It also rewrites the closure
snapshot. It should not be used merely to view or regenerate the published results.

## Snapshot and repeatability limits

The recorded seed is `24092026`. The synthetic revision is
`ed46e02b9b1136f6b54847c1d4bce9e94d11e55c`; the downloaded Open Prices parquet has SHA-256
`fe70ebf08e7a037b24c6e53f5979302b3cfaeac8b9b3754b784c2f1d2fd770f5`.
These are recorded in [preparation.json](../evaluation/preparation.json).

The preparation scripts resolve current upstream data when their local source files
are absent. They do not automatically restore the historical snapshot from those
recorded hashes or enforce the recorded synthetic revision on a fresh download.
Open Prices image URLs are recorded in the manifest but are not immutable snapshots.
Consequently, a fresh data/inference run is not guaranteed to reproduce this cohort
or these predictions exactly. The tracked raw predictions support exact offline
metric reproduction regardless of upstream changes.

Images, source parquet files, model weights and API caches are excluded from Git.
The trace-it source is included as a pinned Git submodule; see
[OCR provenance](OCR.md) for its commit, model revisions and dependency lockfile.
The model identifier is pinned to `jev-1.13.0`, but future hosted availability and
repeatability are not established by this experiment. Latency and cost refer to
the original recorded responses; recomputing the tables incurs no API usage.
