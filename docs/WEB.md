# Browser playground

A small Python web server and a static HTML/CSS/JavaScript interface. No Node build,
frontend framework, database or extra Python packages are required for the saved demo.
The interface and documentation are in English.

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

## Use your own text or image locally

For text only:

```powershell
$env:TYPESAFE_API_KEY = '<your API key>'
python -m jev_tickets.web --live
```

Choose **Your receipt**, paste text and click **Compare prompts**. Each comparison
can make two Jev requests; matching cached inputs may reuse responses. API keys stay
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

The web upload limit is 10 MiB. The adapter also imposes its existing 18 MP image
and 20-page PDF limits. Images support interactive overlays; PDFs support text
extraction and line inspection but have no page-image overlay in this simple UI.
Native PDF text can lack bounding boxes. OCR errors are reported separately from
country uncertainty. Temporary upload files are removed after processing; the
configured OCR/API cache may retain extraction and response data.

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
published benchmark. The full suite has 21 tests.

The Dockerfile is provided, but a container build was not verified in the development
environment because the Docker engine was not running. The equivalent Python server
was exercised directly.
