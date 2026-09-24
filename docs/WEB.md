# Browser playground

A small Python web server and a static HTML/CSS/JavaScript interface. No Node build,
frontend framework, database or extra Python packages are required for the saved demo.
The interface and documentation are in English.

For a new machine, start with [DEPLOYMENT.md](DEPLOYMENT.md): it includes the complete
Windows/Linux/macOS setup, dataset availability, Docker and remote live access.
This page describes the UI and its behavior in more detail.

## Start the saved demo

From the repository root, with Python 3.12 or later:

```powershell
python -m jev_tickets.web
```

Open **http://127.0.0.1:8000**. Select an example and click **Compare prompts**.
If that port is occupied or reserved, add `--port 8765` and open
**http://127.0.0.1:8765** instead. Stop the server with Ctrl+C.
The demo uses historical responses and makes no Jev calls, even if an API key is
present in the environment. It bundles three examples:

- A synthetic French image with saved OCR and agreement between prompts.
- A synthetic transcription where the focused prompt resolves an abstention.
- An Italian-language ambiguity control where the focused prompt is wrong.

On the image example, green rectangles show the actual saved OCR line coordinates.
Click a rectangle or expand **Inspect extracted lines** and select a line: the
matching region turns orange. These are text regions, not semantic merchant/total
fields. Source attribution is in [ATTRIBUTION.md](../jev_tickets/static/ATTRIBUTION.md).

## Difficult real receipt gallery

With the OCR environment, downloaded weights and API key configured, start:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
& '.\external\trace-it\backend\.venv\Scripts\python.exe' -m jev_tickets.web --live --port 8765 --trace-repo external/trace-it --model-dir .cache/models
```

Open **http://127.0.0.1:8765**. The live server starts on **Real challenge gallery**.
Choose among eight real photographs, then click **Run real OCR + Jev**, or **Run all 8**
to process the gallery sequentially. Selecting a photo alone does not make API calls.

The photos include heavy wrinkles, uneven illumination, a blue color cast, folds
through the address, small dense type and an out-of-focus faded print. Images are
unaltered Open Prices contributions and include per-image source URLs, reference
evidence, licensing and hashes in `jev_tickets/static/real-examples.json`.

Each run forces a new OCR computation and two fresh Jev requests. The loaded local
model session can be reused, but neither OCR text nor Jev responses are replayed
from a result cache. Only extracted text reaches Jev; source labels and example
descriptions do not. The results panel shows:

- Total server processing time, OCR time and the wall time of the two parallel Jev calls.
- Whether the first OCR model load was included.
- Input/output tokens, per-request latency and estimated API cost.
- Candidate probability, API confidence, top-two margin, Noul evidence judgment
  and the complete country distribution.
- Mean OCR score and individual line scores via selectable bounding boxes.
- A session table with both predictions and their source-reference matches.

Costs use the [published input rate](https://docs.typesafe.ai/models) checked on
2026-09-24: USD 0.042 per million input tokens; output is free. They exclude local
CPU/storage costs and are not an account invoice. If a request fails, displayed
costs cover successful responses only. Total server time excludes browser upload
and rendering; parallel request times should not be added to obtain wall time.

Use **Fit image**, zoom controls or **Open full image** to inspect a receipt. The
page and result cards wrap at narrow widths, and the text area expands to show the
whole extraction. Tables respond to their own container width: below 60 rem,
each row becomes a card with labelled values. No column requires sideways scrolling.
The workspace columns also fit the available container width. In an embedded or
automated browser reporting a viewport wider than its visible host window, a small
layout safeguard bounds the page to that window and tracks host resizing.
The introductory copy wraps naturally, without forced line breaks.

The page also shows the complete 70-image reviewed-evidence comparison, generated
from the same artifacts as [the follow-up report](OBSERVABLE_EVALUATION.md). Store
metadata agreement, reviewed image agreement, abstentions, unsupported guesses and
extraction failures are separate measurements. The original 85.6% is explicitly
labelled dataset agreement. See [browser verification](WEB_VALIDATION.md).

The gallery was deliberately selected from previously successful cases with visible
image difficulties. A new verification run matched all eight source labels under
both prompts. This is a curated demonstration, not independent accuracy evidence;
no character-level OCR accuracy was measured. See [gallery validation](GALLERY_RESULTS.md).

## Use your own text or image locally

For text only:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
python -m jev_tickets.web --live
```

Choose **Your receipt**, paste text and click **Compare prompts**. Each comparison
makes two new Jev requests. The web interface bypasses the response cache; the CLI's
existing cache behavior is unchanged. API keys stay
on the server. The browser shows candidates and probabilities, with review routing.

For images, first follow the [OCR setup](../README.md#images-and-pdfs), then use the
submodule's Python environment:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
& '.\external\trace-it\backend\.venv\Scripts\python.exe' -m jev_tickets.web --live --trace-repo external/trace-it --model-dir .cache/models
```

Choose a file, click **Extract text locally**, inspect its boxes and text, then
click **Compare prompts**. The image stays local; only text is sent to Jev. The
extraction step does not call Jev. Edited text affects classification; boxes and
line labels continue to represent the original OCR extraction.
After editing the transcription, timing cards no longer attribute the changed text
to the earlier OCR run.

The web upload limit is 10 MiB. The adapter also imposes its existing 18 MP image
and 20-page PDF limits. Images support interactive overlays; PDFs support text
extraction and line inspection but have no page-image overlay in this simple UI.
Native PDF text can lack bounding boxes. OCR errors are reported separately from
country uncertainty. Temporary upload files are removed after processing; the
local OCR cache may retain extraction data even when its reuse is disabled.

**Download comparison JSON** exports the displayed comparison and text. It does not
modify the published evaluation files.

## Deploy the saved demo quickly

The default mode can be exposed publicly without an API key or OCR setup:

```powershell
python -m jev_tickets.web --host 0.0.0.0 --port 8000
```

Or use the included Dockerfile:

```powershell
docker build -t jev-receipt-demo .
docker run --rm -p 8000:8000 jev-receipt-demo
```

On a container hosting service, build this repository's Dockerfile. It starts the
saved demo, listens on `0.0.0.0`, and honors the `PORT` environment variable (default
8000). No secrets, submodule initialization or model downloads are needed for that
container. The container runs as an unprivileged user and copies only the application.

Live mode is deliberately bound to localhost. This experimental server does not
provide accounts, public upload authentication or a public paid-inference service.
Deploying the saved demo and enabling local live processing are separate options.

## Verify

```powershell
python -m unittest discover -s tests -v
```

Web tests cover recorded-mode isolation, credential exclusion, request boundaries,
temporary upload handling, bounding-box preservation and partial provider failure.
The historical evaluation scores remain unchanged by this interface.

Browser verification covered desktop and 390-pixel mobile layouts, switching saved
examples, clicking image boxes and text lines, uploading the bundled image, local OCR
and one live comparison. That image produced 19 OCR lines and 406 characters; both
live prompts proposed France. These two smoke-test calls are separate from the
published benchmark. The full suite now has 28 tests, including observable-reference scoring, fresh-inference,
cost calculation and source-label isolation checks for the real gallery.

The real-gallery update also passed the complete **Run all 8** browser flow using
fresh OCR and Jev responses. Layout was checked from 320 to 1440 pixels, with full
transcriptions and result cards visible without clipping. Both prompt variants
matched the eight source references in that curated batch.

The Dockerfile is provided, but a container build was not verified in the development
environment because the Docker engine was not running. The equivalent Python server
was exercised directly.
