"""Check web boundaries and reuse of real OCR coordinates without paid requests."""

import base64
from http.server import ThreadingHTTPServer
import json
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from jev_tickets.web import Playground, handler_for


class PlaygroundTests(unittest.TestCase):
    def setUp(self):
        self.app = Playground()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.app))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def post(self, route, body, headers=None):
        request = urllib.request.Request(
            self.base + route,
            json.dumps(body).encode(),
            {"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            with exc:
                return exc.code, json.load(exc)

    def test_recorded_demo_never_calls_provider_and_preserves_boxes(self):
        self.app.client.evaluate = Mock(side_effect=AssertionError("Unexpected provider call"))
        status, data = self.post("/api/demo", {"id": "eval-000001"})
        self.assertEqual(status, 200)
        self.assertEqual(data["mode"], "recorded")
        self.assertEqual(data["lines"][0]["bbox"], [67.0, 31.0, 226.0, 60.0])
        self.assertEqual(len(data["results"]), 2)
        self.app.client.evaluate.assert_not_called()

    def test_demo_rejects_live_requests_even_if_a_key_exists(self):
        self.app.client.api_key = "test-secret"
        self.assertEqual(self.post("/api/compare", {"text": "France"})[0], 400)
        with urllib.request.urlopen(self.base + "/api/config") as response:
            payload = response.read()
        self.assertNotIn(b"test-secret", payload)

    def test_cross_origin_and_live_host_are_rejected(self):
        self.assertEqual(
            self.post("/api/demo", {"id": "eval-000001"}, {"Origin": "https://unrelated.example"})[
                0
            ],
            403,
        )
        self.app.live = True
        self.assertEqual(
            self.post("/api/demo", {"id": "eval-000001"}, {"Host": "unrelated.example"})[0], 403
        )

    def test_static_routes_do_not_expose_local_files(self):
        for route in ("/../.env", "/demos.json", "/web.py"):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(self.base + route)
            self.assertEqual(caught.exception.code, 404)
            caught.exception.close()

    def test_ocr_returns_boxes_and_cleans_temporary_upload(self):
        self.app.live = True
        self.app.trace_repo = "configured"
        lines = [{"text": "France", "bbox": [1, 2, 30, 40], "page": 1, "confidence": 0.9}]
        paths = []

        def read(path):
            paths.append(path)
            self.assertEqual(path.read_bytes(), b"test image content")
            return {"text": "France", "lines": lines, "elapsed_s": 0.1}

        self.app.reader = Mock(read=read)
        status, data = self.post(
            "/api/extract",
            {"name": "../receipt.png", "data": base64.b64encode(b"test image content").decode()},
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["lines"], lines)
        self.assertEqual(paths[0].name, "receipt.png")
        self.assertFalse(paths[0].exists())

    def test_partial_provider_failure_is_not_unknown(self):
        self.app.live = True
        self.app.client.api_key = "test-secret"

        def decision(text, client, variant, policy):
            if variant == "baseline-v1":
                raise RuntimeError("private error detail")
            return {"variant": variant, "candidate": "FR", "status": "review"}

        with patch("jev_tickets.web.classify", side_effect=decision):
            status, data = self.post("/api/compare", {"text": "France"})
        self.assertEqual(status, 200)
        self.assertEqual(data["results"][0]["status"], "error")
        self.assertNotIn("candidate", data["results"][0])
        self.assertNotIn("private error detail", json.dumps(data))
        self.assertEqual(data["results"][1]["candidate"], "FR")


if __name__ == "__main__":
    unittest.main()
