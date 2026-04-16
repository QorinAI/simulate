import unittest

from lifescope.report_quality import (
    inspect_chinese_report,
    summarize_chinese_artifact_quality,
)


class ReportQualityTests(unittest.TestCase):
    def test_fluent_chinese_report_passes_lightweight_gate(self):
        report = (
            "## 一眼答案\n"
            "这条路径的重点不是立刻做出终局选择，而是先用三个月验证创业节奏是否真的适合你。"
            "如果现金流压力继续上升，稳定路线会变得更有吸引力。\n"
        )

        result = inspect_chinese_report(report)

        self.assertTrue(result["passed"])
        self.assertEqual(result["awkward_markers"], [])

    def test_awkward_translation_markers_fail_gate(self):
        report = "## 一眼答案\n诚实答案仍是拒绝。报告能看到这版推演看到的路径，树故意保持开放。\n"

        result = inspect_chinese_report(report)

        self.assertFalse(result["passed"])
        self.assertIn("critical_semantic_break_markers_present", result["findings"])

    def test_artifact_summary_blocks_beta_when_any_artifact_fails(self):
        summary = summarize_chinese_artifact_quality(
            [
                {
                    "artifact": "report.md",
                    "passed": True,
                    "findings": [],
                },
                {
                    "artifact": "visual_summary.md",
                    "passed": False,
                    "findings": ["awkward_translation_markers_present"],
                },
            ]
        )

        self.assertFalse(summary["passed"])
        self.assertEqual(summary["release_gate"], "blocks_beta_when_failed")
        self.assertEqual(summary["failed_artifacts"], ["visual_summary.md"])


if __name__ == "__main__":
    unittest.main()
