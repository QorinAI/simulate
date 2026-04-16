"""LifeScope-owned user-facing report rendering."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _line_items(items: List[str], limit: int = 3) -> str:
    selected = [str(item).strip() for item in items if str(item).strip()][:limit]
    if not selected:
        return "- 暂无足够信息。\n"
    return "".join("- {item}\n".format(item=item) for item in selected)


def render_lifescope_chinese_report(reading: Dict[str, Any]) -> str:
    """Render a shorter Chinese-native report from the LifeScope response shape."""
    profile = reading.get("profile") or {}
    one_screen = reading.get("one_screen") or {}
    branches = list(reading.get("branches") or [])
    timeline = list(reading.get("timeline") or [])
    trust = reading.get("trust") or {}
    name = profile.get("name") or "你"
    question = profile.get("question") or "这次人生选择"

    lines = [
        "# LifeScope 中文阅读报告",
        "",
        "生成时间：{time}".format(time=datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        "",
        "## 先看结论",
        "",
        "{name}，这次报告不是在给你下判断，而是在比较几种未来的代价和可能性。".format(name=name),
        "",
        one_screen.get("summary") or "当前信息足够生成第一版推演，但还需要补充关键约束。",
        "",
        "- 最可能路径：{path}".format(path=one_screen.get("top_path") or "待确认"),
        "- 最强替代：{path}".format(path=one_screen.get("main_challenger") or "待确认"),
        "- 最大风险：{risk}".format(path=one_screen.get("main_challenger") or "待确认", risk=one_screen.get("biggest_risk") or "待确认"),
        "- 最大不确定性：{uncertainty}".format(uncertainty=one_screen.get("biggest_uncertainty") or "待确认"),
        "- 下一步：{action}".format(action=one_screen.get("next_action") or "补充一个关键变量后重跑。"),
        "",
        "## 这次真正要回答的问题",
        "",
        question,
        "",
        "## 三条路径怎么读",
        "",
    ]

    for branch in branches[:3]:
        lines.extend(
            [
                "### {title}".format(title=branch.get("title") or "未命名路径"),
                "",
                "这条路当前权重约为 {probability}%，置信度约为 {confidence}%。".format(
                    probability=branch.get("probability", 0),
                    confidence=branch.get("confidence", 0),
                ),
                "",
                branch.get("landing") or "这条路径还需要更多信息来描述。",
                "",
                "**它可能给你：**",
                "",
                _line_items(branch.get("upside") or []),
                "**它会要求你承担：**",
                "",
                _line_items(branch.get("watch") or []),
            ]
        )

    lines.extend(["## 未来几年先看什么", ""])
    for item in timeline[:4]:
        lines.extend(
            [
                "### {year}：{title}".format(
                    year=item.get("year") or "某一年",
                    title=item.get("title") or "关键节点",
                ),
                "",
                item.get("body") or "这个节点还需要更多输入。",
                "",
            ]
        )

    lines.extend(
        [
            "## 为什么这份报告还不能说满",
            "",
            "这份报告的价值不在于给出唯一答案，而在于让你看到哪些信息会改变判断。",
            "",
            "**这次主要用了：**",
            "",
            _line_items(trust.get("evidence") or [], limit=5),
            "**还缺这些信息：**",
            "",
            _line_items(trust.get("missing") or [], limit=5),
            "## 下一次怎么重跑",
            "",
            _line_items(trust.get("rerun") or [], limit=5),
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_lifescope_chinese_report(reading: Dict[str, Any], output_root: Path) -> str:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(reading.get("run_id") or "run")
    path = output_dir / "{run_id}.md".format(run_id=run_id)
    path.write_text(render_lifescope_chinese_report(reading), encoding="utf-8")
    return str(path)
