# Install and run on another machine

This is the complete setup guide. Run commands from the repository root unless a
block explicitly changes directory. All examples use port **8765**; change it if
occupied. Stop a foreground server with **Ctrl+C**.

## 1. Choose what to run

| Goal | Requirements | Downloads / paid calls |
|---|---|---|
| Browser with three recorded comparisons, OCR boxes and published results | Git, Python 3.12+ and a modern browser | Everything needed is in Git; no API calls |
| Recompute published evaluation tables | Git and Python 3.12+ | Offline; no API calls |
| Browser or CLI with live text classification | Above plus your own TypeSafe API key | Two Jev calls per browser comparison |
| Browser with eight real receipt photographs, fresh OCR and live Jev | Git submodule, `uv`, Python **3.12**, OCR dependencies/models and API key | Initial model download; two Jev calls per image |
| Publicly hosted demonstration | Python host or Docker | Recorded mode; no credentials or models |
| Live OCR on a remote machine | Full live setup on that machine and SSH access | Open locally through an SSH tunnel |

The application is Python plus static HTML/CSS/JavaScript. No Node build, database,
trace-it server, GPU, Hugging Face hosted inference or general-purpose LLM is needed.
Jev is a hosted **text** classifier. OCR runs on the machine hosting this application.

### Platform requirements and verification scope

- Git must be available as `git`. Use a current Chromium, Firefox or Safari browser
  supporting CSS container queries; allow JavaScript.
- The lightweight app accepts Python 3.12 or newer. The pinned trace-it backend
  requires **Python 3.12.x**, not 3.13/3.14. `uv` can install that interpreter.
- Prefer a 64-bit machine supported by the locked ONNX Runtime/OpenCV wheels.
  CPU execution was used. Memory/storage minimums have not been benchmarked; keep
  enough space for the backend environment, model files and optional image datasets.
- Windows live operation has been exercised. Linux/macOS commands below use the same
  pinned source and lockfile, but were not executed on those platforms in this session.
  Package availability can differ by OS/CPU. A Docker engine was not available for
  container validation. These limits also apply to the deployment examples below.
- You need access to this GitHub repository and its trace-it submodule. If either
  clone reports a permissions error, authenticate with an account that has access.

## 2. Clone and open the recorded browser demo

### Windows PowerShell

Install Git and Python if needed. These commands assume `python` is on PATH:

```powershell
git clone https://github.com/Kripta-Studios/jev-receipt-country-classifier.git
cd jev-receipt-country-classifier
python --version
python -m jev_tickets.web --port 8765
```

### Linux / macOS, bash or zsh

```bash
git clone https://github.com/Kripta-Studios/jev-receipt-country-classifier.git
cd jev-receipt-country-classifier
python3 --version
python3 -m jev_tickets.web --port 8765
```

Open **http://127.0.0.1:8765/**. This starts in **Saved demo** mode. Choose one of
three examples and click **Compare prompts**. The synthetic image has selectable
OCR boxes; the other two examples use text. The evaluation section shows the
historical dataset agreement and the separate 70-image reviewed-evidence results.

The **Real challenge gallery** photographs are also bundled, but running them needs
the live setup below. Selecting a photograph alone never runs inference. The web
gallery contains eight curated examples, not every benchmark image.

Running from the repository root requires no `pip install` for recorded mode.
The app does not automatically read `.env`; `.env.example` is documentation only.

## 3. Install the OCR environment and weights

Skip this section for recorded mode, offline reports or live text-only processing.

### Windows PowerShell

From the repository root, initialize the pinned source and install `uv`:

```powershell
git submodule update --init --recursive
git submodule status
python -m pip install --user uv
```

The expected trace-it revision is `84c4c0463862640940efb1232344287a2d03bcf5`.
The following block uses `python -m uv` so a missing scripts directory on PATH does
not prevent it from running. It creates the environment at the submodule's backend:

```powershell
$projectRoot = (Get-Location).Path
$ocrPython = Join-Path $projectRoot 'external\trace-it\backend\.venv\Scripts\python.exe'
$modelPath = Join-Path $projectRoot '.cache\models'
Push-Location (Join-Path $projectRoot 'external\trace-it\backend')
try {
    python -m uv sync --frozen --no-dev --python 3.12
    if ($LASTEXITCODE -ne 0) { throw 'OCR dependency installation failed.' }
    & $ocrPython -m app.features.ingestion.tools.download_models --profile v5-latin --no-verifier --output $modelPath
    if ($LASTEXITCODE -ne 0) { throw 'OCR model download failed.' }
} finally {
    Pop-Location
}
```

### Linux / macOS, bash or zsh

Install `uv` using the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).
For example, its standalone installer for Linux/macOS is:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal or follow the installer's PATH instructions before running `uv`.
On Ubuntu/Debian, the pinned backend's OpenCV dependency needs these system libraries
(also listed in the upstream Dockerfile):

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0
```

That package-manager block is for Ubuntu/Debian, not macOS. Then, from the repository root:

```bash
git submodule update --init --recursive
git submodule status
uv --version
project_root="$PWD"
(
  set -e
  cd "$project_root/external/trace-it/backend"
  uv sync --frozen --no-dev --python 3.12
  .venv/bin/python -m app.features.ingestion.tools.download_models \
    --profile v5-latin --no-verifier --output "$project_root/.cache/models"
)
```

The subshell returns you to the repository root. On all platforms the downloader
fetches the pinned detector and Latin recognizer, creates the character dictionary,
and writes `.cache/models/manifest.json`. It can reuse the Hugging Face download
cache. The model repositories used here are public; normally no HF token is needed.
If the Hub requires authentication in your environment, use `hf auth login` from
the installed backend environment, or supply `HF_TOKEN` through that process's
environment. This is separate from `TYPESAFE_API_KEY`.

Expected model files include:

```text
.cache/models/
  det/inference.onnx
  det/inference.yml
  rec/inference.onnx
  rec/inference.yml
  rec/keys.txt
  manifest.json
```

See [OCR.md](OCR.md) for exact model repositories, revisions and settings. Do not
copy somebody else's `.venv` between machines; rebuild it from the lockfile.

## 4. Start the full live browser playground

Set your own API key in the same terminal that starts the server. The placeholders
below are not working keys; do not commit a real key or put it in browser JavaScript.

### Windows PowerShell

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
& '.\external\trace-it\backend\.venv\Scripts\python.exe' -m jev_tickets.web --live --port 8765 --trace-repo external/trace-it --model-dir .cache/models
```

### Linux / macOS

```bash
export TYPESAFE_API_KEY='<your API key>'
./external/trace-it/backend/.venv/bin/python -m jev_tickets.web \
  --live --port 8765 --trace-repo external/trace-it --model-dir .cache/models
```

Open **http://127.0.0.1:8765/** and follow this sequence:

1. Select **Real challenge gallery**, then a country/example.
2. Click **Run real OCR + Jev**, or **Run all 8**. The first OCR initialization can
   take longer. Wait for the completion message; the server processes one UI operation
   at a time. A second browser tab can receive a busy response during a run.
3. Read OCR/Jev/total latency, tokens, estimated API cost and OCR score above the workspace.
4. Inspect the photo. Click a box or open **Inspect extracted lines** and select a line.
   **Show OCR text regions**, zoom, **Fit image** and **Open full image** help inspect it.
5. Compare the original and focused country candidates. Expand **All country
   probabilities**. These are suggestions for review, not automatically accepted decisions.
6. Read the session results below, then use **Download comparison JSON** to export
   the current comparison. Session history is in browser memory and resets on reload.
7. Use **Your receipt** to upload another image/PDF or paste text. Click **Extract
   text locally**, inspect/edit the text, then **Compare prompts**.

Both live prompts receive OCR text only. Each gallery run recomputes OCR and makes
two new Jev requests, without replaying saved decisions. Eight images therefore
produce 16 successful API requests when everything completes. The three saved
demos remain recorded examples even while the server is in live mode.

The gallery photographs and their licences are already under `jev_tickets/static/real/`.
**Do not download the full datasets just to run the web gallery.** Its source labels
are metadata, not guaranteed visible country truth. Live session results never
overwrite the published benchmark files.

### Live text only

Without OCR installed, set the key as above and run:

```bash
python3 -m jev_tickets.web --live --port 8765
```

On Windows use `python` instead of `python3`. Choose **Your receipt** and paste text.
Do not attempt the image buttons until the OCR environment and weights are installed;
the configured submodule path alone does not prove its dependencies are available.

## 5. Datasets and repeatable evaluation

| Data | Included in Git? | How to use it |
|---|---|---|
| Three browser demos, including one synthetic image | Yes | Saved demo; no API key |
| Eight real challenge images and provenance | Yes | Full live gallery after OCR setup |
| Historical OCR text, predictions, labels and metrics | Yes | Recompute tables offline |
| Full 70-image reviewed cohort: manifest, OCR, predictions and reviews | Records yes; original image files no | Download with the command below; run OCR/evaluation separately |
| Prepared 750 real / 2,000 synthetic references | Manifests yes; downloaded source files/images no | Advanced research workflow in REPRODUCIBILITY.md |
| OCR weights, dependency environments and API caches | No | Install/download locally |

### Exact offline reports, without API usage

```bash
python3 research/make_report.py
python3 research/evaluate_observable.py
python3 -m unittest discover -s tests -v
```

On Windows replace `python3` with `python`. Expected: **28 passing tests**, the
historical focused metadata match **309/361**, and the separate reviewed-image
agreement **66/70 original vs 62/70 focused**, including two extraction failures.
The reference is an assistant review, not human ground truth. These overlapping
cohorts must not be added together as independent examples.

### Fetch the 70 reviewed images

```bash
python3 research/evaluate_observable.py --download
```

This uses URLs from the fixed manifest, writes `.cache/benchmark/real/*.img` and
checks available historical image hashes. The `.img` suffix contains a normal image;
the OCR adapter detects its format from the bytes. To inspect one in the browser,
copy it to a `.jpg`, `.png` or `.webp` filename matching its actual format, then use
**Your receipt**. The web gallery does not automatically import the 70-case manifest.
Two cohort images exceed the adapter's 18 MP limit; those failures are retained in
the published evaluation. Source URLs may later disappear or change.

### Repeat Jev on the recorded OCR text

After setting the API key:

```bash
python3 research/evaluate_observable.py --predict --output-dir .cache/observable-replay
```

This makes up to 136 new Jev requests for the 68 valid extractions. Existing records
in that output directory are resumed; use a new directory name for a completely new
run. The script rejects saved predictions if their request hashes no longer match
the OCR text/current prompts. Published results are preserved.

### Repeat OCR and Jev together

After the image download and full OCR setup, use a new output filename/directory:

Windows PowerShell:

```powershell
& '.\external\trace-it\backend\.venv\Scripts\python.exe' research/ocr_benchmark.py --trace-repo external/trace-it --workers 3 --manifest observable/manifest.jsonl --output observable/replay-ocr.jsonl --force-recompute
python research/evaluate_observable.py --predict --ocr evaluation/observable/replay-ocr.jsonl --output-dir .cache/observable-new-ocr
```

Linux/macOS:

```bash
./external/trace-it/backend/.venv/bin/python research/ocr_benchmark.py \
  --trace-repo external/trace-it --workers 3 --manifest observable/manifest.jsonl \
  --output observable/replay-ocr.jsonl --force-recompute
python3 research/evaluate_observable.py --predict \
  --ocr evaluation/observable/replay-ocr.jsonl --output-dir .cache/observable-new-ocr
```

Use `--workers 1` on a smaller CPU/memory machine. `--force-recompute` bypasses the
OCR cache for pending images but does not redo IDs already recorded in the output
file. A new filename is needed to redo every attempt. These commands create a new
local OCR output under `evaluation/observable/`; do not commit it as historical evidence.

For the 421 synthetic text comparison, the full research workflow and original
snapshot limitations, follow [REPRODUCIBILITY.md](REPRODUCIBILITY.md). The dataset
preparation scripts can rewrite manifests and select current upstream data: use a
separate checkout for a new experiment. They are not a prerequisite for the web UI.

## 6. CLI on the same installation

From the repository root, text classification works with plain Python:

```bash
python3 -m jev_tickets --text 'Store, Barcelona, Spain. Total EUR 12.00' --policy evaluation/frozen-policy.json
python3 -m jev_tickets --text 'Store, Barcelona, Spain. Total EUR 12.00' --rules-only
```

Use `python` on Windows. The second command needs no API key. Image/PDF classification
uses the backend interpreter and an explicit trace-it path:

```powershell
& '.\external\trace-it\backend\.venv\Scripts\python.exe' -m jev_tickets --file jev_tickets/static/real/op-65346.webp --trace-repo external/trace-it --model-dir .cache/models --policy evaluation/frozen-policy.json
```

```bash
./external/trace-it/backend/.venv/bin/python -m jev_tickets \
  --file jev_tickets/static/real/op-65346.webp --trace-repo external/trace-it \
  --model-dir .cache/models --policy evaluation/frozen-policy.json
```

See the [README batch example](../README.md#command-line) for JSONL input/output.

## 7. Deploy the recorded web demo

### Python host

```bash
python3 -m jev_tickets.web --host 0.0.0.0 --port 8765
```

Use `python` on Windows. On another computer on the same network, open
`http://<server-address>:8765/`; `127.0.0.1` always means the computer running your
browser. Configure the host's firewall/network routing for the chosen port when
remote access is intended. For a hosting platform, use its assigned `PORT`:

```bash
python3 -m jev_tickets.web --host 0.0.0.0
```

That command honors `PORT` and defaults to 8000 if it is absent. A public hostname,
HTTPS and process supervision are supplied by the hosting platform/reverse proxy.
The built-in server is intended for this experimental demonstration.

### Docker, recorded mode

Run from the repository root with a working Docker engine:

```bash
docker build -t jev-receipt-demo .
docker run --rm --name jev-receipt-demo -p 8765:8000 jev-receipt-demo
```

Open **http://127.0.0.1:8765/**. The same commands work in PowerShell. No submodule,
OCR weights or API key is needed. The image contains the app, three saved demos,
eight gallery photos and published browser metrics. Gallery inference is disabled.
The Dockerfile runs as an unprivileged user and respects `PORT` inside the container.
If you change the container port, also change the right-hand side of `-p`.

For a detached, restartable demo:

```bash
docker run -d --name jev-receipt-demo -p 8765:8000 --restart unless-stopped jev-receipt-demo
docker logs -f jev-receipt-demo
```

Use this instead of the preceding `--rm` command. If that foreground container is
still running, stop it first. Later, `docker stop jev-receipt-demo` stops the named
demo. Docker commands are provided but a container build was not verified here.

## 8. Full live processing on a remote machine

Install sections 2–4 **on the remote machine**, including its own Python environment,
model files and API-key environment variable. Start the live server on that host's
loopback interface, using the same command as section 4. Keep that process running.

In a separate terminal on your laptop/desktop, open a tunnel:

```bash
ssh -N -L 8765:127.0.0.1:8765 username@server-address
```

Then open **http://127.0.0.1:8765/** on your laptop. The browser connects through SSH;
OCR runs remotely and only the extracted text goes from the remote server to Jev.
Stop the tunnel with Ctrl+C. If 8765 is already used locally, change only the first
port to 8766 and browse to `http://127.0.0.1:8766/`.

Live mode deliberately rejects `--host 0.0.0.0` and non-localhost Host headers. The
included Dockerfile is recorded-mode only. It does not become a working OCR container
by adding an API key: it has neither the backend dependencies nor the model weights.
An SSH tunnel is the documented way to use full live functionality from another
machine without changing the application's current local-only design.

## 9. Troubleshooting and updates

| Symptom | Check / action |
|---|---|
| `No module named jev_tickets` | Run from the cloned repository root, or install that project into the interpreter you are using |
| Missing `app`, `rapidocr`, `cv2` or `onnxruntime` | Initialize the submodule, run the frozen install and start live OCR with its `.venv` interpreter |
| Python version rejected | Use `uv sync --frozen --no-dev --python 3.12` for the backend |
| `libGL.so.1` / GLib error on Linux | Install `libgl1` and `libglib2.0-0` for the pinned OpenCV wheel |
| Missing model / dictionary | Run the pinned `v5-latin --no-verifier` downloader and pass the correct `--model-dir` |
| Live controls disabled or Jev unavailable | Set `TYPESAFE_API_KEY` in the terminal starting the server and include `--live`; `.env` is not auto-loaded |
| First OCR request slow | Model loading is included; subsequent runs reuse the loaded session but recompute the image |
| Busy response | Wait for the current image/batch to finish; close duplicate submissions |
| Upload rejected | Web limit 10 MiB; OCR image limit 18 MP; PDF limit 20 pages; image formats JPEG/PNG/WebP |
| No PDF boxes | This simple UI extracts PDF text but does not render PDF page-image overlays |
| Different answers or timings | Hosted inference, hardware and OCR can vary; offline reports reproduce the recorded results |
| Port unavailable | Add `--port 8766` and browse to that port; do not stop unrelated services |
| Stale layout | Reload the page after an update; avoid leaving device emulation enabled when checking the actual browser window |
| Session rows disappear | History is per-page memory; export the current JSON before reloading |
| Can't access remote live server directly | Use the SSH tunnel in section 8 |
| Dataset download hash mismatch | Upstream bytes changed; retain the published evidence and investigate rather than silently accepting new bytes |

To update an existing clone, first stop its server and save any work you need:

```bash
git pull --ff-only
git submodule update --init --recursive
```

If the backend lockfile/submodule changed, rerun section 3. Restart the server and
reload the browser. Credentials, `.cache`, model weights and `.venv` are not pushed
to GitHub. Published code, documentation, dataset manifests, reviewed labels, raw
evaluation outputs and the small attributed browser gallery are tracked.

## 10. Installation verification performed

On 2026-09-24, the documented runtime was checked in a separate clean Git clone
of code revision `f5038e2`, without copying the original project's `.venv`, model
directory, API key or receipt-processing caches:

- Both offline report commands reproduced their tracked outputs without changes.
- All 28 tests passed without a Jev API key.
- The recorded web server served HTML/CSS/JavaScript and all eight gallery images;
  their SHA-256 hashes matched the bundled provenance manifest.
- Recursive submodule initialization fetched the pinned trace-it revision.
- The frozen Python 3.12 environment installed 106 packages in a new `.venv`.
- The pinned model downloader populated a new model directory and character dictionary.
- Real local OCR of bundled `op-65346.webp` returned 36 regions, 781 text characters
  and nonempty bounding boxes, with OCR cache reuse disabled. The first read including
  initialization took about 49 seconds on this machine; this is not a latency guarantee.

Package-manager/Hugging Face global download caches could still be reused; this
was not a freshly installed operating system. The new OCR check did not make paid
Jev requests. Earlier live browser and API checks are recorded in
[WEB_VALIDATION.md](WEB_VALIDATION.md). Linux/macOS execution, Docker building and
an actual remote SSH deployment were not verified in this Windows environment.
