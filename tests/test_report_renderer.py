import tempfile
import unittest
from pathlib import Path

from lifescope.report_quality import inspect_chinese_report
from lifescope.report_renderer import (
    render_lifescope_chinese_report,
    write_lifescope_chinese_report,
)


class ReportRendererTests(unittest.TestCase):
    def sample_reading(self):
        return {
            "run_id": "run-demo",
            "profile": {
                "name": "Alex",
                "question": "未来两年应该创业还是读研？",
            },
            "one_screen": {
                "summary": "当前最值得比较的是高上限机会和生活稳定之间的代价。",
                "top_path": "稳步复利路径",
                "main_challenger": "高上限下注路径",
                "biggest_risk": "工作强度挤压健康和关系。",
                "biggest_uncertainty": "现金流与关系约束还不够清楚。",
                "next_action": "补充预算和关系时间线后重跑。",
            },
            "branches": [
                {
                    "title": "稳步复利路径",
                    "probability": 42,
                    "confidence": 70,
                    "landing": "这条路保留职业成长，同时让生活节奏仍然可恢复。",
                    "upside": ["现金流更稳", "关系维护更容易"],
                    "watch": ["上限可能来得更慢", "需要持续做作品"],
                }
            ],
            "timeline": [
                {
                    "year": "1 年",
                    "title": "第一次选择",
                    "body": "先看工作节奏是否还能留出恢复时间。",
                }
            ],
            "trust": {
                "evidence": ["当前身份：AI 产品经理"],
                "missing": ["预算细节不足"],
                "rerun": ["只改一个 what-if 后重跑"],
            },
        }

    def test_rendered_lifescope_report_is_fluent_enough_for_gate(self):
        report = render_lifescope_chinese_report(self.sample_reading())
        quality = inspect_chinese_report(report)

        self.assertIn("LifeScope 中文阅读报告", report)
        self.assertIn("这次真正要回答的问题", report)
        self.assertTrue(quality["passed"])

    def test_write_lifescope_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_lifescope_chinese_report(self.sample_reading(), Path(directory))

        self.assertTrue(path.endswith("run-demo.md"))


if __name__ == "__main__":
    unittest.main()
