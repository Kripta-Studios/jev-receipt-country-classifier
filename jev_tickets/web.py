"""Small browser playground. Saved demo by default; live processing is local-only."""

import argparse
import base64
import binascii
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
from urllib.parse import urlsplit

from .classifier import classify, rule_baseline
from .client import JevClient

STATIC = Path(__file__).parent / "static"
POLICY = {"min_probability": 0.9, "min_margin": 0.15, "min_evidence": 0, "automatic_enabled": False}
MAX_FILE = 10 * 1024 * 1024
MAX_BODY = 14 * 1024 * 1024
VARIANTS = ("baseline-v1", "focused-v2")


class Playground:
    def __init__(
        self, live=False, trace_repo=None, model_dir=".cache/models", cache_dir=".cache/web"
    ):
        self.live = live
        self.trace_repo = trace_repo
        self.model_dir = model_dir
        self.cache_dir = Path(cache_dir)
        self.client = JevClient(self.cache_dir / "jev")
        self.reader = None
        self.busy = threading.Lock()
        self.demos = json.loads((STATIC / "demos.json").read_text(encoding="utf-8"))

    def config(self):
        return {
            "live": self.live,
            "jev_available": self.live and bool(self.client.api_key),
            "ocr_available": self.live and bool(self.trace_repo),
            "examples": [{k: row[k] for k in ("id", "title", "description")} for row in self.demos],
        }

    def demo(self, ident):
        row = next((r for r in self.demos if r["id"] == ident), None)
        if row is None:
            raise ValueError("Unknown saved example")
        return {**row, "mode": "recorded", "rules": rule_baseline(row["text"])}

    def compare(self, text):
        if not self.live or not self.client.api_key:
            raise ValueError(
                "Live Jev is unavailable. Start locally with --live and TYPESAFE_API_KEY."
            )
        if not isinstance(text, str) or not text.strip() or len(text) > 80_000:
            raise ValueError("Enter between 1 and 80,000 characters of receipt text.")

        def run(variant):
            try:
                return classify(text, self.client, variant, POLICY)
            except Exception:
                # Provider messages may contain internal request details; keep them off the browser.
                return {
                    "variant": variant,
                    "status": "error",
                    "error": "Jev could not complete this request. Check server connectivity and API configuration, then try again.",
                }

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, VARIANTS))
        return {"mode": "live", "results": results, "rules": rule_baseline(text)}

    def extract(self, body):
        if not self.live or not self.trace_repo:
            raise ValueError("Local OCR is unavailable. Configure --live and --trace-repo first.")
        name, encoded = body.get("name"), body.get("data")
        if not isinstance(name, str) or not isinstance(encoded, str):
            raise ValueError("Choose an image or PDF to extract.")
        suffix = Path(name).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
            raise ValueError("Supported files: JPEG, PNG, WebP and PDF.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Invalid file encoding.") from exc
        if not data or len(data) > MAX_FILE:
            raise ValueError("Choose a file between 1 byte and 10 MiB.")
        if self.reader is None:
            try:
                from .ocr import TraceReader

                self.reader = TraceReader(self.trace_repo, self.model_dir, self.cache_dir / "ocr")
            except Exception as exc:
                raise ValueError(
                    "OCR could not start. Use the trace-it backend Python environment and download the v5-latin weights."
                ) from exc
        with tempfile.TemporaryDirectory(prefix="jev-upload-") as directory:
            path = Path(directory) / ("receipt" + suffix)
            path.write_bytes(data)
            try:
                extraction = self.reader.read(path)
            except Exception as exc:
                raise ValueError(
                    "This file could not be read. Check its format, resolution and orientation; try a smaller image."
                ) from exc
        return {
            "text": extraction["text"],
            "lines": extraction["lines"],
            "line_count": len(extraction["lines"]),
            "elapsed_s": extraction["elapsed_s"],
            "mode": "local_ocr",
        }


def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, data, content_type="application/json; charset=utf-8"):
            payload = (
                json.dumps(data, ensure_ascii=False).encode() if isinstance(data, dict) else data
            )
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if app.live and urlsplit("http://" + self.headers.get("Host", "")).hostname not in {
                "127.0.0.1",
                "localhost",
            }:
                return self.send(403, {"error": "Live mode requires a localhost Host header."})
            path = urlsplit(self.path).path
            if path == "/api/config":
                return self.send(200, app.config())
            assets = {
                "/favicon.svg": ("favicon.svg", "image/svg+xml"),
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
                "/demo-receipt.jpg": ("demo-receipt.jpg", "image/jpeg"),
            }
            if path not in assets:
                return self.send(404, {"error": "Not found"})
            filename, mime = assets[path]
            self.send(200, (STATIC / filename).read_bytes(), mime)

        def do_POST(self):
            self.connection.settimeout(30)
            if app.live and urlsplit("http://" + self.headers.get("Host", "")).hostname not in {
                "127.0.0.1",
                "localhost",
            }:
                return self.send(403, {"error": "Live mode requires a localhost Host header."})
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                return self.send(403, {"error": "Cross-origin requests are not allowed."})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send(415, {"error": "Expected application/json"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    return self.send(413, {"error": "Request is empty or too large."})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
            except (ValueError, UnicodeError):
                return self.send(400, {"error": "Invalid JSON request"})
            path = urlsplit(self.path).path
            if path not in {"/api/demo", "/api/compare", "/api/extract"}:
                return self.send(404, {"error": "Not found"})
            if not app.busy.acquire(blocking=False):
                return self.send(
                    429, {"error": "Another receipt is being processed. Try again shortly."}
                )
            try:
                if path == "/api/demo":
                    result = app.demo(body.get("id"))
                elif path == "/api/compare":
                    result = app.compare(body.get("text"))
                else:
                    result = app.extract(body)
                self.send(200, result)
            except ValueError as exc:
                self.send(400, {"error": str(exc)})
            except Exception:
                self.send(500, {"error": "The request could not be completed."})
            finally:
                app.busy.release()

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Receipt country browser playground")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--live", action="store_true", help="Enable local OCR and live Jev calls")
    bundled = Path(__file__).resolve().parents[1] / "external/trace-it"
    parser.add_argument(
        "--trace-repo",
        default=os.environ.get("TRACE_REPO") or (str(bundled) if bundled.exists() else None),
    )
    parser.add_argument("--model-dir", default=".cache/models")
    parser.add_argument("--cache-dir", default=".cache/web")
    args = parser.parse_args()
    if args.live and args.host not in {"127.0.0.1", "localhost"}:
        parser.error(
            "Live mode binds to localhost only. Public deployment supports the saved demo."
        )
    app = Playground(args.live, args.trace_repo, args.model_dir, args.cache_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler_for(app))
    print(
        f"Receipt country playground: http://{args.host}:{args.port} ({'live enabled' if args.live else 'saved demo; no API calls'})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
