import os
import tempfile
import unittest
from pathlib import Path
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
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.md"
            visual_summary_path = Path(directory) / "visual_summary.md"
            report_path.write_text(
                "## 先看结论\n这是一份通顺的中文报告，说明三条路径、关键风险和下一步。",
                encoding="utf-8",
            )
            visual_summary_path.write_text(
                "## 路径对比\n这份摘要帮助用户比较机会、代价、生活节奏和下一步行动。",
                encoding="utf-8",
            )
            artifacts = SimpleNamespace(
                result=result,
                output_dir="/tmp/run-kimi",
                json_path="/tmp/run-kimi/simulation.json",
                report_path=str(report_path),
                visual_summary_path=str(visual_summary_path),
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
        self.assertTrue(reading["quality"]["chinese_artifacts"]["passed"])
        self.assertEqual(reading["quality"]["beta_blockers"], [])
        self.assertIn("lifescope_report_path", reading["engine"])

    def test_reading_marks_unfluent_chinese_report_as_beta_blocker(self):
        branch = SimpleNamespace(
            branch_id="b1",
            title="稳步复利路径",
            probability=1.0,
            confidence=0.74,
            summary="继续积累可信度。",
            life_events=[],
            uncertainty_notes=[],
            extended_outlooks=[],
            yearly_path=[],
            final_state=SimpleNamespace(career="AI 产品负责人"),
        )
        result = SimpleNamespace(
            run_id="run-kimi",
            generated_at="2026-04-15T00:00:00Z",
            provider="moonshot",
            model="kimi-k2.5",
            branches=[branch],
            baseline_summary="Kimi 生成的结构化基线摘要。",
            global_uncertainty_notes=[],
            evidence_catalog=[],
        )
        with tempfile.TemporaryDirectory() as directory:
            report_path = os.path.join(directory, "report.md")
            visual_summary_path = os.path.join(directory, "visual_summary.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write("## 一眼答案\n诚实答案仍是拒绝。报告能看到这版推演看到的路径。\n")
            with open(visual_summary_path, "w", encoding="utf-8") as handle:
                handle.write("## 路径对比\n这份摘要把几条路径放在一起比较机会、代价和下一步。\n")
            artifacts = SimpleNamespace(
                result=result,
                output_dir=directory,
                json_path=os.path.join(directory, "simulation.json"),
                report_path=report_path,
                visual_summary_path=visual_summary_path,
                dossier_path=os.path.join(directory, "analysis_dossier.json"),
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

        self.assertFalse(reading["quality"]["chinese_artifacts"]["passed"])
        self.assertEqual(reading["quality"]["chinese_artifacts"]["failed_artifacts"], ["report.md"])
        self.assertIn("chinese_report_fluency_not_beta_ready", reading["quality"]["beta_blockers"])
        self.assertIn("lifescope_report_path", reading["engine"])


if __name__ == "__main__":
    unittest.main()
