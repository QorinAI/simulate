"""Lightweight report quality checks for user-facing artifacts."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{3,}")

AWKWARD_CHINESE_MARKERS = (
    "这版推演看到的",
    "被居住",
    "更低戏剧性",
    "诚实答案仍是拒绝",
    "报告能看到",
    "尚欠指定",
    "中年岁月",
    "树故意保持",
    "普通版本，而非关于它的论证",
    "先买到什么",
)

CRITICAL_MARKERS = (
    "诚实答案仍是拒绝",
    "报告能看到",
    "树故意保持",
)


def cjk_count(text: str) -> int:
    return len(CJK_RE.findall(text or ""))


def english_word_count(text: str) -> int:
    return len(ENGLISH_WORD_RE.findall(text or ""))


def inspect_chinese_report(markdown: str) -> Dict[str, object]:
    """Return a conservative Chinese fluency assessment.

    This is intentionally heuristic. It catches obvious translation-smell and
    mixed-language failures so the product does not mistake "Kimi run completed"
    for "the report is readable enough for beta".
    """
    text = str(markdown or "")
    cjk = cjk_count(text)
    english_words = english_word_count(text)
    awkward_hits = [marker for marker in AWKWARD_CHINESE_MARKERS if marker in text]
    critical_hits = [marker for marker in CRITICAL_MARKERS if marker in text]
    english_per_1000_cjk = 0.0
    if cjk:
        english_per_1000_cjk = round((english_words / float(cjk)) * 1000.0, 2)

    findings: List[str] = []
    if not cjk:
        findings.append("artifact_has_no_chinese_text")
    if english_per_1000_cjk > 12.0:
        findings.append("mixed_language_density_high")
    if awkward_hits:
        findings.append("awkward_translation_markers_present")
    if critical_hits:
        findings.append("critical_semantic_break_markers_present")

    passed = (
        bool(cjk)
        and not critical_hits
        and len(awkward_hits) <= 2
        and english_per_1000_cjk <= 12.0
    )
    return {
        "language": "zh" if cjk else "unknown",
        "passed": passed,
        "cjk_characters": cjk,
        "english_words": english_words,
        "english_words_per_1000_cjk": english_per_1000_cjk,
        "awkward_markers": awkward_hits,
        "critical_markers": critical_hits,
        "findings": findings,
        "summary": (
            "Chinese report passes the lightweight fluency gate."
            if passed
            else "Chinese report is not fluent enough for beta review."
        ),
    }


def inspect_markdown_artifact(path: object, label: str) -> Dict[str, object]:
    artifact_path = Path(str(path))
    if not artifact_path.exists():
        return {
            "artifact": label,
            "path": str(artifact_path),
            "passed": False,
            "summary": "{label} was not found for Chinese fluency inspection.".format(
                label=label
            ),
            "findings": ["artifact_missing"],
        }
    try:
        result = inspect_chinese_report(artifact_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return {
            "artifact": label,
            "path": str(artifact_path),
            "passed": False,
            "summary": "{label} could not be decoded as UTF-8.".format(label=label),
            "findings": ["artifact_decode_failed"],
        }
    result["artifact"] = label
    result["path"] = str(artifact_path)
    return result


def summarize_chinese_artifact_quality(checks: List[Dict[str, object]]) -> Dict[str, object]:
    failed = [check for check in checks if not check.get("passed")]
    passed = not failed and bool(checks)
    return {
        "passed": passed,
        "checks": checks,
        "failed_artifacts": [check.get("artifact") for check in failed],
        "release_gate": "blocks_beta_when_failed",
        "summary": (
            "Chinese user-facing artifacts pass the lightweight fluency gate."
            if passed
            else "Chinese user-facing artifacts are not fluent enough for beta."
        ),
    }
