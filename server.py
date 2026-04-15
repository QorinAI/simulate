"""LifeScope MVP local server.

Run:

    python3 server.py

Then open http://127.0.0.1:8765/
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlparse

from lifescope.core import build_life_reading, normalize_payload
from lifescope.engine_mapper import to_simulation_request_payload
from lifescope.storage import RunStore


ROOT = Path(__file__).resolve().parent
STORE = RunStore(ROOT / "data")


class LifeScopeHandler(SimpleHTTPRequestHandler):
    server_version = "LifeScopeMVP/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):  # noqa: A002 - inherited signature
        sys.stderr.write("[lifescope] " + format % args + "\n")

    def do_GET(self):  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json(
                {
                    "ok": True,
                    "service": "lifescope-web-mvp",
                    "storage": str(STORE.root),
                }
            )
            return
        if parsed.path == "/api/runs":
            self.write_json({"runs": STORE.list_recent()})
            return
        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.rsplit("/", 1)[-1]
            record = STORE.get(run_id)
            if record is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Run not found")
                return
            self.write_json(record)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_HEAD(self):  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_HEAD()

    def do_POST(self):  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/api/profile":
            payload = self.read_json()
            profile = normalize_payload(payload)
            preview = build_life_reading(profile)
            self.write_json(
                {
                    "profile": preview["profile"],
                    "profile_review": preview["profile_review"],
                    "trust": preview["trust"],
                    "engine_contract": preview["engine_contract"],
                }
            )
            return
        if parsed.path in ("/api/simulate", "/api/intake"):
            payload = self.read_json()
            reading = build_life_reading(payload)
            reading["storage"] = STORE.save(reading)
            self.write_json(reading)
            return
        if parsed.path == "/api/engine-contract":
            payload = self.read_json()
            self.write_json(to_simulation_request_payload(payload))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_DELETE(self):  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.rsplit("/", 1)[-1]
            deleted = STORE.delete(run_id)
            self.write_json({"run_id": run_id, "deleted": deleted})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return {}

    def write_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the LifeScope Web MVP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args(argv)
    STORE.ensure()
    server = ThreadingHTTPServer((args.host, args.port), LifeScopeHandler)
    print(f"LifeScope MVP running at http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping LifeScope MVP server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
