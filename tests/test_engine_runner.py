import os
import unittest
from types import SimpleNamespace
from unittest import mock

from lifescope import engine_runner


class EngineRunnerTests(unittest.TestCase):
    def test_selected_engine_accepts_kimi_aliases(self):
        self.assertEqual(engine_runner.selected_engine("simulate_life"), "simulate_life")
        self.assertEqual(engine_runner.selected_engine("kimi2.5"), "simulate_life")
        self.assertEqual(engine_runner.selected_engine("deterministic"), "deterministic")

    def test_run_reading_falls_back_to_deterministic_on_engine_error(self):
        payload = {
            "name": "Alex",
            "background": "做过 AI 产品，正在比较创业和读研。" * 6,
            "question": "未来两年应该创业还是读研？",
        }
        with mock.patch.object(
            engine_runner,
            "run_simulate_life_reading",
            side_effect=RuntimeError("Moonshot failed with sk-test-secret-1234567890"),
        ):
            reading = engine_runner.run_reading(payload, engine="simulate_life")

        self.assertEqual(reading["engine"]["mode"], "deterministic")
        self.assertEqual(reading["engine"]["fallback_from"], "simulate_life")
        self.assertIn("redacted-secret", reading["engine"]["error"])
        self.assertNotIn("sk-test-secret", reading["engine"]["error"])
        self.assertEqual(reading["source"], "deterministic-web-mvp")

    def test_run_reading_can_disable_fallback(self):
        payload = {"name": "Alex", "background": "做过 AI 产品。"}
        with mock.patch.dict(os.environ, {"LIFESCOPE_FALLBACK_ON_ENGINE_ERROR": "0"}):
            with mock.patch.object(
                engine_runner,
                "run_simulate_life_reading",
                side_effect=RuntimeError("boom"),
            ):
                with self.assertRaises(RuntimeError):
                    engine_runner.run_reading(payload, engine="simulate_life")

    def test_reading_from_simulation_artifacts_maps_engine_result(self):
        branch = SimpleNamespace(
            branch_id="b1",
            title="稳步复利路径",
            probability=0.62,
            confidence=0.74,
            summary="继续积累可信度，并在三年内形成更稳的生活组合。",
            life_events=[
                SimpleNamespace(impact_summary="作品和收入信号更稳定"),
            ],
            uncertainty_notes=["关系和现金流约束仍需补充"],
            extended_outlooks=[],
            yearly_path=[
                SimpleNamespace(year_offset=1, summary="第一年验证工作节奏。"),
                SimpleNamespace(year_offset=3, summary="第三年路径开始显形。"),
                SimpleNamespace(year_offset=10, summary="第十年生活形状落地。"),
            ],
            final_state=SimpleNamespace(career="AI 产品负责人"),
        )
        challenger = SimpleNamespace(
            branch_id="b2",
            title="高上限下注路径",
            probability=0.38,
            confidence=0.7,
            summary="进入高波动机会。",
            life_events=[],
            uncertainty_notes=[],
            extended_outlooks=[],
            yearly_path=[],
            final_state=SimpleNamespace(career="创业团队核心成员"),
        )
        result = SimpleNamespace(
            run_id="run-kimi",
            generated_at="2026-04-15T00:00:00Z",
            provider="moonshot",
            model="kimi-k2.5",
            branches=[branch, challenger],
            baseline_summary="Kimi 生成的结构化基线摘要。",
            global_uncertainty_notes=["预算约束会改变路径排序"],
            evidence_catalog=[
                SimpleNamespace(title="用户背景自述", summary="做过 AI 产品"),
            ],
        )
        artifacts = SimpleNamespace(
            result=result,
            output_dir="/tmp/run-kimi",
            json_path="/tmp/run-kimi/simulation.json",
            report_path="/tmp/run-kimi/report.md",
            visual_summary_path="/tmp/run-kimi/visual_summary.md",
            dossier_path="/tmp/run-kimi/analysis_dossier.json",
        )

        reading = engine_runner.reading_from_simulation_artifacts(
            {
                "name": "Alex",
                "age": 29,
                "location": "上海",
                "career": "AI 产品经理",
                "question": "创业还是读研？",
                "background": "做过 AI 产品。",
                "interests": "AI 产品",
                "constraints": "预算有限",
                "risk": 7,
                "balance": 8,
                "mobility": 7,
                "whatif": ["startup"],
                "includeSensitive": False,
                "localOnly": True,
            },
            artifacts,
        )

        self.assertEqual(reading["source"], "simulate_life")
        self.assertEqual(reading["engine"]["provider"], "moonshot")
        self.assertEqual(reading["engine"]["model"], "kimi-k2.5")
        self.assertEqual(reading["branches"][0]["probability"], 62)
        self.assertEqual(reading["one_screen"]["summary"], "Kimi 生成的结构化基线摘要。")


if __name__ == "__main__":
    unittest.main()
