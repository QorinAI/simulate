"""Deterministic life-reading scaffolding for the Web MVP.

This module intentionally does not call an LLM. It produces the same product
shape that the first backend integration should expect from the real engine:
profile review, three branches, timeline, trust surface, and rerun guidance.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Any, Dict, Iterable, List


WHAT_IF_LABELS = {
    "overseas": "出国读研",
    "startup": "加入创业团队",
    "stable": "稳定现金流",
    "family": "优先亲密关系",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def text_words(value: str) -> List[str]:
    return [item for item in re.split(r"[\s,，;；、\n]+", str(value or "")) if item]


def normalized_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = default
    return int(clamp(parsed, minimum, maximum))


def clean_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or default).replace("\r", "\n").split())
    return text.strip()


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    whatif = payload.get("whatif") or payload.get("what_if") or []
    if isinstance(whatif, str):
        whatif = [whatif]
    return {
        "name": clean_text(payload.get("name"), "你") or "你",
        "age": normalized_int(payload.get("age"), 29, 15, 100),
        "location": clean_text(payload.get("location"), "未填写") or "未填写",
        "career": clean_text(payload.get("career"), "未填写") or "未填写",
        "background": clean_text(payload.get("background")),
        "interests": clean_text(payload.get("interests")),
        "question": clean_text(payload.get("question")),
        "constraints": clean_text(payload.get("constraints")),
        "focus": clean_text(payload.get("focus"), "whole"),
        "risk": normalized_int(payload.get("risk"), 5, 0, 10),
        "balance": normalized_int(payload.get("balance"), 5, 0, 10),
        "mobility": normalized_int(payload.get("mobility"), 5, 0, 10),
        "whatif": [str(item) for item in whatif if str(item).strip()],
        "includeSensitive": bool(payload.get("includeSensitive")),
        "localOnly": bool(payload.get("localOnly", True)),
    }


def profile_richness(profile: Dict[str, Any]) -> float:
    fields = [
        len(profile["background"]) > 120,
        len(profile["interests"]) > 40,
        len(profile["question"]) > 20,
        len(profile["constraints"]) > 20,
        profile["location"] != "未填写",
        profile["career"] != "未填写",
        bool(profile["whatif"]),
    ]
    return sum(1 for item in fields if item) / float(len(fields))


def missing_signals(profile: Dict[str, Any]) -> List[str]:
    missing = []
    if len(profile["background"]) < 120:
        missing.append("缺少连续经历和关键转折")
    if len(profile["interests"]) < 30:
        missing.append("兴趣与价值观还太薄")
    if len(profile["constraints"]) < 20:
        missing.append("现实约束没有说清")
    if len(profile["question"]) < 20:
        missing.append("本次推演问题不够具体")
    if not profile["includeSensitive"]:
        missing.append("关系、家庭、健康等高敏信息未纳入")
    return missing[:5]


def has_what_if(profile: Dict[str, Any], value: str) -> bool:
    return value in set(profile["whatif"])


def weighted_probabilities(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [dict(item) for item in items]
    total = sum(max(float(row["raw"]), 0.01) for row in rows)
    assigned = 0
    for index, row in enumerate(rows):
        if index == len(rows) - 1:
            row["probability"] = max(1, 100 - assigned)
        else:
            row["probability"] = max(1, int(round(max(float(row["raw"]), 0.01) / total * 100)))
            assigned += row["probability"]
    return rows


def build_branches(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    risk = profile["risk"] / 10.0
    balance = profile["balance"] / 10.0
    mobility = profile["mobility"] / 10.0
    text = " ".join(
        [
            profile["background"],
            profile["interests"],
            profile["constraints"],
        ]
    ).lower()
    relationship_signal = 0.08 if re.search(r"关系|家庭|伴侣|结婚|孩子|亲密", text) else 0.0
    creator_signal = 0.06 if re.search(r"写作|创作|内容|产品|创业|独立", text) else 0.0

    branches = weighted_probabilities(
        [
            {
                "id": "steady",
                "raw": 0.34 + balance * 0.11 - risk * 0.04 + (0.08 if has_what_if(profile, "stable") else 0),
                "title": "稳步复利路径",
                "tone": "green",
                "landing": "在熟悉行业继续积累可信度，把职业上升、现金流和生活节奏放在同一张表里。",
                "upside": ["稳定现金流让选择权变多", "人际和城市生活更容易沉淀"],
                "watch": ["避免舒适区吞掉增长速度", "每 6 个月检查一次技能杠杆"],
            },
            {
                "id": "bet",
                "raw": 0.31
                + risk * 0.14
                + mobility * 0.07
                + creator_signal
                + (0.1 if has_what_if(profile, "startup") else 0),
                "title": "高上限下注路径",
                "tone": "red",
                "landing": "把未来两年压到高密度 AI 机会里，换取更快的能力复利和更大的波动。",
                "upside": ["可能更早进入核心决策层", "作品、网络和商业判断会快速压缩成长周期"],
                "watch": ["工作强度会挤压关系和健康", "需要预设退出窗口而不是无限硬扛"],
            },
            {
                "id": "reset",
                "raw": 0.28
                + mobility * 0.11
                + balance * 0.03
                + relationship_signal
                + (0.1 if has_what_if(profile, "overseas") else 0),
                "title": "迁移重塑路径",
                "tone": "gold",
                "landing": "用城市、学校或跨国环境重组身份和网络，但短期要承受现金流与归属感波动。",
                "upside": ["新网络会改变中长期机会密度", "有机会重新定义生活方式"],
                "watch": ["前 18 个月最容易怀疑选择", "关系和预算需要更早做压力测试"],
            },
        ]
    )
    richness = profile_richness(profile)
    missing = missing_signals(profile)
    confidence = clamp(0.54 + richness * 0.24 - len(missing) * 0.025, 0.46, 0.86)
    sorted_branches = sorted(branches, key=lambda branch: branch["probability"], reverse=True)
    for index, branch in enumerate(sorted_branches):
        branch["confidence"] = int(round((confidence - index * 0.03) * 100))
    return sorted_branches


def build_timeline(profile: Dict[str, Any], branches: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    lead = branches[0]
    question = profile["question"] or "核心选择"
    return [
        {
            "year": "现在",
            "title": "确认问题边界",
            "body": f"{profile['name']} 当前最重要的不是马上选“最佳人生”，而是把 {question} 拆成可验证的 2 到 3 个假设。",
        },
        {
            "year": "1 年",
            "title": "第一次硬分叉",
            "body": f"{lead['title']} 会先考验节奏管理。若投入方向没有带来可见作品、收入信号或关系稳定感，需要降低承诺成本。",
        },
        {
            "year": "3 年",
            "title": "路径开始显形",
            "body": "职业、城市和关系会开始互相牵制。这个阶段最该看的是精力是否还能支持长期复利，而不是只看头衔变化。",
        },
        {
            "year": "10 年",
            "title": "生活形状落地",
            "body": "最好的结果不是单点成功，而是职业杠杆、现金流、亲密关系和身体节奏之间形成可持续组合。",
        },
    ]


def build_evidence(profile: Dict[str, Any]) -> List[str]:
    items = [
        f"当前身份：{profile['career']}",
        f"城市与迁移：{profile['location']}，迁移意愿 {profile['mobility']}/10",
        "兴趣价值观："
        + ("、".join(text_words(profile["interests"])[:6]) if profile["interests"] else "未充分填写"),
        f"约束：{profile['constraints'] or '未充分填写'}",
    ]
    if profile["whatif"]:
        labels = [WHAT_IF_LABELS.get(item, item) for item in profile["whatif"]]
        items.append("What-if：" + "、".join(labels))
    return items


def build_rerun_guidance(profile: Dict[str, Any], missing: List[str]) -> List[str]:
    items = [
        "补一段最近两年真实选择经历，而不是只写目标。",
        "给每个 what-if 加一个可接受代价，例如预算、时间、关系压力。",
        "下一次重跑时只改一个关键变量，方便看出分支变化。",
    ]
    if not profile["includeSensitive"]:
        items.insert(0, "如果愿意，单独补充关系、家庭或健康约束，但保留删除权。")
    if not missing:
        items.append("把 90 天行动结果补回系统，比较路径概率是否移动。")
    return items[:4]


def build_profile_review(profile: Dict[str, Any], missing: List[str]) -> Dict[str, Any]:
    return {
        "summary": f"{profile['name']}，{profile['age']} 岁，当前在 {profile['location']}，身份是 {profile['career']}。",
        "decision_frame": profile["question"] or "本次还没有写清最想推演的问题。",
        "key_values": text_words(profile["interests"])[:8],
        "constraints": profile["constraints"],
        "missing": missing,
    }


def safe_session_id(profile: Dict[str, Any]) -> str:
    seed = "|".join(
        [
            profile["name"],
            profile["career"],
            profile["question"],
            datetime.utcnow().isoformat(timespec="microseconds"),
        ]
    )
    return "run-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def build_engine_contract(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "target": "simulate_life.SimulationRequest",
        "mapping": {
            "person.name": profile["name"],
            "person.age": profile["age"],
            "person.summary": profile["background"][:280],
            "person.career.current_role": profile["career"],
            "person.location.metro_area": profile["location"],
            "person.values.priorities": text_words(profile["interests"])[:6],
            "interventions": [WHAT_IF_LABELS.get(item, item) for item in profile["whatif"]],
        },
        "future_backend_entrypoint": "simulated_life.simulator.run_simulation(request, config, provider)",
    }


def build_life_reading(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = normalize_payload(payload)
    missing = missing_signals(profile)
    branches = build_branches(profile)
    avg_confidence = int(round(sum(branch["confidence"] for branch in branches) / len(branches)))
    lead = branches[0]
    summary = (
        f"当前更像是“{lead['title']}”领先，但不是命运预测。真正的分歧在于"
        f"{'你愿意承受多大波动' if profile['risk'] >= 6 else '你愿意牺牲多少上限'}，以及"
        f"{'生活稳定能否成为主约束' if profile['balance'] >= 7 else '生活稳定是否会被延后处理'}。"
    )
    run_id = safe_session_id(profile)
    return {
        "run_id": run_id,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": "deterministic-web-mvp",
        "profile": profile,
        "profile_review": build_profile_review(profile, missing),
        "one_screen": {
            "title": f"{profile['name']} 的三条可能人生",
            "summary": summary,
            "confidence": avg_confidence,
            "top_path": lead["title"],
            "main_challenger": branches[1]["title"],
            "biggest_risk": branches[0]["watch"][0],
            "biggest_uncertainty": missing[0] if missing else "关键输入足够生成第一版推演",
            "next_action": "补充一个能改变路径排序的真实约束，然后只改一个 what-if 重跑。",
        },
        "branches": branches,
        "timeline": build_timeline(profile, branches),
        "trust": {
            "evidence": build_evidence(profile),
            "missing": missing or ["关键输入足够生成第一版推演"],
            "rerun": build_rerun_guidance(profile, missing),
        },
        "safety": {
            "framing": "多路径模拟，不是命运预测。",
            "advice_boundary": "不提供医疗、法律、投资或心理诊断建议。",
            "privacy_mode": "raw_redacted_on_disk" if profile["localOnly"] else "explicit_server_storage_required_later",
        },
        "engine_contract": build_engine_contract(profile),
    }
