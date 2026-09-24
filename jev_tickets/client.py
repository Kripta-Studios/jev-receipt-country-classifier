"""Bounded official HTTP client with validated responses and content-addressed caching."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
import urllib.error
import urllib.request
import uuid

ENDPOINT = "https://api.typesafe.ai/v1/systemone"


class ProviderError(RuntimeError):
    """A provider failure, never an UNKNOWN model answer."""


def probability(value):
    return type(value) in (float, int) and math.isfinite(value) and 0 <= value <= 1


def validate_response(data, questions):
    if not isinstance(data, dict) or not isinstance(data.get("model"), str):
        raise ProviderError("Missing provider model identity")
    answers = data.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ProviderError("Response question keys do not match the request")
    for key, question in questions.items():
        answer = answers[key]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise ProviderError("Response answer type does not match the request")
        if question["type"] == "choice":
            probs = answer.get("probabilities")
            if not isinstance(probs, dict) or set(probs) != set(question["criteria"]):
                raise ProviderError("Response country options do not match the request")
            if (
                not all(probability(p) for p in probs.values())
                or abs(sum(probs.values()) - 1) > 0.01
            ):
                raise ProviderError("Invalid probability distribution")
            if answer.get("choice") not in probs or not probability(answer.get("confidence")):
                raise ProviderError("Invalid choice or confidence")
            if probs[answer["choice"]] + 0.001 < max(probs.values()):
                raise ProviderError("Chosen option is not a maximum-probability option")
        elif question["type"] == "noul" and not probability(answer.get("noul")):
            raise ProviderError("Invalid Noul value")
    usage = data.get("usage")
    if not isinstance(usage, dict) or any(
        type(usage.get(k)) is not int or usage[k] < 0 for k in ("input_tokens", "output_tokens")
    ):
        raise ProviderError("Invalid token usage")
    return data


def retry_delay(header, attempt):
    if header:
        try:
            delay = float(header)
        except ValueError:
            try:
                delay = (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError):
                delay = 2**attempt
        if delay > 60:
            raise ProviderError("Provider retry delay exceeds the bounded wait; retry later")
        return max(0, delay)
    return min(30, 2**attempt + random.random())


class JevClient:
    def __init__(self, cache_dir=None, api_key=None, timeout=40, max_attempts=3):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_attempts = max_attempts

    def evaluate(self, payload):
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        identity = hashlib.sha256(ENDPOINT.encode() + encoded).hexdigest()
        path = self.cache_dir / (identity + ".json") if self.cache_dir else None
        if path and path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            validate_response(cached["response"], payload["questions"])
            if cached["response"]["model"] != payload["model"]:
                raise ProviderError("Cached model does not match the pinned request")
            return {**cached, "cache_hit": True, "network_attempts": 0, "elapsed_s": 0}
        if not self.api_key:
            raise ProviderError("Set TYPESAFE_API_KEY in the process environment")
        started = time.perf_counter()
        for attempt in range(self.max_attempts):
            request = urllib.request.Request(
                ENDPOINT,
                data=encoded,
                method="POST",
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 529, 502, 503, 504) and attempt + 1 < self.max_attempts:
                    time.sleep(retry_delay(exc.headers.get("Retry-After"), attempt))
                    continue
                raise ProviderError(f"Jev returned HTTP {exc.code}") from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                # Delivery may have succeeded; do not silently retry and double bill.
                raise ProviderError(
                    "Jev transport or JSON failure; delivery/usage may be unknown"
                ) from None
        validate_response(data, payload["questions"])
        if data["model"] != payload["model"]:
            raise ProviderError("Provider model does not match the pinned request")
        record = {
            "response": data,
            "request_sha256": identity,
            "cache_hit": False,
            "network_attempts": attempt + 1,
            "elapsed_s": time.perf_counter() - started,
        }
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
            temporary.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        return record
