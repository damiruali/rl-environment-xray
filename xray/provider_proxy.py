"""Local bounded 429 backoff for V1 evaluations; no request/response bodies persisted.

Groq free-tier TPM can be lower than one multi-turn episode. V1's short client retry
window otherwise aborts a valid episode. This relay honors explicit Retry-After / the
provider's retry message, at most four retries, at most 60 seconds each.
"""

import hmac
import json
import math
import os
import re
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx


@contextmanager
def groq_proxy():
    stats = {
        "requests": 0,
        "retries_429": 0,
        "backoff_seconds": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "reasoning_tokens": 0,
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            if not hmac.compare_digest(
                self.headers.get("Authorization", ""), "Bearer " + os.environ["GROQ_API_KEY"]
            ):
                self.send_error(401)
                return
            if self.path not in ("/v1/chat/completions", "/chat/completions"):
                self.send_error(404)
                return
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            payload = json.loads(body)
            if payload.get("stream"):
                self.send_error(400, "This small eval relay only supports non-streaming")
                return
            with httpx.Client(timeout=90) as client:
                for attempt in range(5):
                    if stats["requests"] >= 300 or stats["prompt_tokens"] > 300_000:
                        self.send_error(429, "Local demo request/token budget exhausted")
                        return
                    stats["requests"] += 1
                    response = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        content=body,
                        headers={
                            "Authorization": "Bearer " + os.environ["GROQ_API_KEY"],
                            "Content-Type": "application/json",
                        },
                    )
                    if response.status_code != 429 or attempt == 4:
                        break
                    match = re.search(r"try again in ([\d.]+)s", response.text)
                    delay = min(60, math.ceil(float(match.group(1))) + 1 if match else 30)
                    stats["retries_429"] += 1
                    stats["backoff_seconds"] += delay
                    print(f"Provider TPM backoff: {delay}s (no rollout restart)", flush=True)
                    time.sleep(delay)
            if response.status_code == 200:
                usage = response.json().get("usage", {})
                for key in ("prompt_tokens", "completion_tokens"):
                    stats[key] += usage.get(key, 0)
                stats["reasoning_tokens"] += usage.get("completion_tokens_details", {}).get(
                    "reasoning_tokens", 0
                )
            self.send_response(response.status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response.content)))
            self.end_headers()
            self.wfile.write(response.content)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", stats
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
