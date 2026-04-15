import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib import error, request

import server
from lifescope.core import build_life_reading
from lifescope.storage import RunStore


class ServerApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_store = server.STORE
        server.STORE = RunStore(Path(self.temp_dir.name))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.LifeScopeHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.base_url = "http://127.0.0.1:{port}".format(port=self.httpd.server_port)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        server.STORE = self.previous_store
        self.temp_dir.cleanup()

    def post_json(self, path, payload):
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        return json.loads(request.urlopen(req, timeout=5).read().decode("utf-8"))

    def test_health_reports_default_engine(self):
        response = json.loads(
            request.urlopen(self.base_url + "/api/health", timeout=5).read().decode("utf-8")
        )

        self.assertTrue(response["ok"])
        self.assertIn(response["default_engine"], ("deterministic", "simulate_life"))

    def test_simulate_route_honors_engine_query_and_saves_redacted_run(self):
        reading = build_life_reading(
            {
                "name": "Alex",
                "background": "private background",
                "question": "创业还是读研？",
            }
        )
        with mock.patch.object(server, "run_reading", return_value=reading) as run_reading:
            response = self.post_json(
                "/api/simulate?engine=simulate_life",
                {"name": "Alex", "background": "private background"},
            )

        run_reading.assert_called_once()
        self.assertEqual(run_reading.call_args[1]["engine"], "simulate_life")
        self.assertEqual(response["storage"]["redacted"], True)
        stored = server.STORE.get(response["run_id"])
        self.assertIsNotNone(stored)
        self.assertTrue(stored["profile"]["background"]["redacted"])

    def test_delete_run_removes_it_from_recent_runs(self):
        response = self.post_json(
            "/api/simulate?engine=deterministic",
            {"name": "Alex", "background": "private background"},
        )
        req = request.Request(self.base_url + "/api/runs/" + response["run_id"], method="DELETE")
        delete_response = json.loads(request.urlopen(req, timeout=5).read().decode("utf-8"))
        runs = json.loads(request.urlopen(self.base_url + "/api/runs", timeout=5).read().decode("utf-8"))

        self.assertTrue(delete_response["deleted"])
        self.assertEqual(runs["runs"], [])

    def test_bad_json_returns_400_once(self):
        req = request.Request(
            self.base_url + "/api/profile",
            data=b"{bad json",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(error.HTTPError) as raised:
            request.urlopen(req, timeout=5)
        self.assertEqual(raised.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
