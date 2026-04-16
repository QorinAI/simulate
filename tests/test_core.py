import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lifescope.core import build_life_reading, normalize_payload
from lifescope.engine_mapper import to_simulation_request_payload
from lifescope.engine_runner import run_reading, selected_engine
from lifescope.storage import RunStore


class LifeScopeCoreTests(unittest.TestCase):
    def test_build_life_reading_returns_three_ranked_branches(self):
        reading = build_life_reading(
            {
                "name": "Alex",
                "age": 29,
                "location": "上海",
                "career": "AI 产品经理",
                "background": "过去几年做 AI 产品和增长，现在想比较创业、读研和稳定路线。" * 4,
                "interests": "AI 产品 写作 心理学 城市生活 长期主义",
                "question": "未来两年应该加入创业团队还是出国读研？",
                "constraints": "预算有限，不想长期 80 小时工作，希望关系和城市生活更稳定。",
                "risk": 6,
                "balance": 8,
                "mobility": 7,
                "whatif": ["overseas", "startup"],
            }
        )

        self.assertEqual(len(reading["branches"]), 3)
        self.assertEqual(sum(branch["probability"] for branch in reading["branches"]), 100)
        self.assertIn("probability", reading["branches"][0])
        self.assertIn("confidence", reading["branches"][0])
        self.assertEqual(reading["one_screen"]["top_path"], reading["branches"][0]["title"])
        self.assertTrue(reading["trust"]["evidence"])
        self.assertTrue(reading["engine_contract"]["mapping"])

    def test_normalize_payload_bounds_numeric_controls(self):
        profile = normalize_payload({"age": 200, "risk": -3, "balance": 22, "mobility": "bad"})
        self.assertEqual(profile["age"], 100)
        self.assertEqual(profile["risk"], 0)
        self.assertEqual(profile["balance"], 10)
        self.assertEqual(profile["mobility"], 5)

    def test_store_redacts_raw_free_text(self):
        reading = build_life_reading(
            {
                "name": "Alex",
                "background": "private background",
                "interests": "private interests",
                "question": "private question",
                "constraints": "private constraints",
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(Path(directory))
            result = store.save(reading)
            stored = json.loads(Path(result["path"]).read_text(encoding="utf-8"))

        self.assertTrue(result["redacted"])
        self.assertTrue(stored["profile"]["background"]["redacted"])
        self.assertNotIn("private background", json.dumps(stored, ensure_ascii=False))

    def test_engine_mapper_builds_simulation_request_shape(self):
        payload = to_simulation_request_payload(
            {
                "name": "Alex",
                "age": 29,
                "career": "AI 产品经理",
                "location": "上海",
                "background": "做过 AI 产品，希望比较创业和读研。",
                "interests": "AI 产品 写作 长期主义",
                "question": "未来两年应该创业还是读研？",
                "risk": 8,
                "balance": 6,
                "mobility": 7,
                "whatif": ["startup", "overseas"],
            }
        )

        self.assertEqual(payload["person"]["name"], "Alex")
        self.assertEqual(payload["person"]["career"]["current_role"], "AI 产品经理")
        self.assertEqual(payload["person"]["finance"]["risk_tolerance"], "high")
        self.assertEqual(payload["branch_count"], 3)
        self.assertEqual(len(payload["interventions"]), 2)
        self.assertEqual(payload["preferred_language"], "zh")

    def test_engine_mapper_accepts_language_override(self):
        payload = to_simulation_request_payload({"name": "Alex", "preferred_language": "zh"})

        self.assertEqual(payload["preferred_language"], "zh")

    def test_engine_mapper_allows_visible_language_override(self):
        with mock.patch.dict(os.environ, {"LIFESCOPE_SIMULATE_LIFE_LANGUAGE": "zh"}):
            payload = to_simulation_request_payload({"name": "Alex"})

        self.assertEqual(payload["preferred_language"], "zh")

    def test_engine_mapper_payload_matches_simulate_life_schema_when_available(self):
        payload = to_simulation_request_payload({"name": "Alex", "age": 29})
        try:
            import sys

            sys.path.insert(0, "/Users/wangyiqi/Desktop/code/simulate_life")
            from simulated_life.models import SimulationRequest
        except Exception:
            self.skipTest("simulate_life package is not importable")

        parsed = SimulationRequest.parse_obj(payload)
        self.assertEqual(parsed.person.name, "Alex")
        self.assertEqual(parsed.branch_count, 3)

    def test_engine_selection_aliases_kimi_to_simulate_life(self):
        self.assertEqual(selected_engine("kimi"), "simulate_life")
        self.assertEqual(selected_engine("moonshot"), "simulate_life")
        self.assertEqual(selected_engine("deterministic"), "deterministic")

    def test_run_reading_keeps_deterministic_default(self):
        reading = run_reading({"name": "Alex"}, engine="deterministic")
        self.assertEqual(reading["engine"]["mode"], "deterministic")


if __name__ == "__main__":
    unittest.main()
