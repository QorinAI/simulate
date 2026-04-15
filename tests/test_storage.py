import json
import tempfile
import unittest
from pathlib import Path

from lifescope.core import build_life_reading
from lifescope.storage import RunStore


class RunStoreTests(unittest.TestCase):
    def test_save_get_delete_removes_index_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(Path(directory))
            reading = build_life_reading(
                {
                    "name": "Alex",
                    "background": "private background",
                    "interests": "private interests",
                    "question": "private question",
                    "constraints": "private constraints",
                }
            )

            saved = store.save(reading)
            self.assertIsNotNone(store.get(saved["run_id"]))
            self.assertEqual(len(store.list_recent()), 1)

            self.assertTrue(store.delete(saved["run_id"]))
            self.assertIsNone(store.get(saved["run_id"]))
            self.assertEqual(store.list_recent(), [])

    def test_redaction_replaces_nested_raw_text(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(Path(directory))
            reading = build_life_reading(
                {
                    "name": "Alex",
                    "background": "private background",
                    "interests": "private interests",
                    "question": "private question",
                    "constraints": "private constraints",
                }
            )
            reading["nested"] = {"copy": "private background should not be stored"}

            saved = store.save(reading)
            stored_text = Path(saved["path"]).read_text(encoding="utf-8")
            stored = json.loads(stored_text)

            self.assertNotIn("private background", stored_text)
            self.assertIn("[redacted:background:", stored["nested"]["copy"])


if __name__ == "__main__":
    unittest.main()
