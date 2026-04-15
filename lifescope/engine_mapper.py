"""Map LifeScope web intake into the existing simulate_life engine contract."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from lifescope.core import WHAT_IF_LABELS, clean_text, normalize_payload, text_words


def risk_tolerance(value: int) -> str:
    if value >= 7:
        return "high"
    if value <= 3:
        return "low"
    return "moderate"


def intervention_payload(what_if: str, index: int) -> Dict[str, Any]:
    title = WHAT_IF_LABELS.get(what_if, what_if)
    return {
        "id": f"what-if-{what_if}",
        "title": title,
        "description": f"用户希望比较“{title}”是否会改变未来 3 到 10 年的路径排序。",
        "effective_year": min(index + 1, 3),
        "tradeoffs": ["需要真实成本约束", "会改变职业、城市、关系或现金流节奏"],
    }


def uncertainty_notes(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    notes = []
    if not profile["includeSensitive"]:
        notes.append(
            {
                "topic": "关系、家庭与健康信息未纳入",
                "note": "用户没有授权使用高敏生活信息，因此关系、家庭、健康路径只能保守处理。",
                "impact": "会降低长期生活节奏、家庭时机和健康韧性判断的置信度。",
                "severity": 0.68,
            }
        )
    if not profile["constraints"]:
        notes.append(
            {
                "topic": "现实约束不足",
                "note": "预算、时间、家庭、城市或精力约束没有说清。",
                "impact": "系统很难判断某条路径的真实可执行性。",
                "severity": 0.62,
            }
        )
    return notes


def evidence_references(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs = []
    if profile["background"]:
        refs.append(
            {
                "id": "user-background",
                "title": "用户背景自述",
                "summary": profile["background"][:240],
                "source_type": "user_input",
                "confidence": 0.9,
            }
        )
    if profile["interests"]:
        refs.append(
            {
                "id": "user-values",
                "title": "兴趣与价值观",
                "summary": profile["interests"][:180],
                "source_type": "user_input",
                "confidence": 0.86,
            }
        )
    if profile["question"]:
        refs.append(
            {
                "id": "user-question",
                "title": "本次推演问题",
                "summary": profile["question"][:180],
                "source_type": "user_input",
                "confidence": 0.9,
            }
        )
    return refs


def to_simulation_request_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = normalize_payload(payload)
    priorities = text_words(profile["interests"])[:8] or ["长期成长", "生活稳定", "选择权"]
    preferred_language = clean_text(
        payload.get("preferred_language"),
        os.getenv("LIFESCOPE_SIMULATE_LIFE_LANGUAGE", "en"),
    ).lower()
    if preferred_language not in ("en", "zh"):
        preferred_language = "en"
    return {
        "person": {
            "name": profile["name"],
            "age": profile["age"],
            "summary": profile["background"] or "用户希望进行多路径人生推演，但背景信息仍然有限。",
            "education": {
                "highest_degree": "unknown",
                "field_of_study": "unknown",
                "school_context": "unknown",
            },
            "career": {
                "current_role": profile["career"],
                "industry": "unknown",
                "years_experience": 0,
                "employment_status": "unknown",
                "trajectory": profile["question"] or "待通过用户补充信息明确",
            },
            "finance": {
                "annual_income_usd": 0,
                "savings_usd": 0,
                "debt_usd": 0,
                "housing_status": "unknown",
                "risk_tolerance": risk_tolerance(profile["risk"]),
            },
            "relationships": {
                "status": "undisclosed",
                "partner_support": "unknown",
                "dependents": 0,
                "family_goal": "unknown or evolving",
            },
            "location": {
                "country": "unknown",
                "metro_area": profile["location"],
                "mobility_preference": f"{profile['mobility']}/10",
            },
            "values": {
                "priorities": priorities,
                "work_life_balance_importance": profile["balance"],
            },
            "health_habits": [],
            "uncertainty_notes": uncertainty_notes(profile),
            "evidence_references": evidence_references(profile),
        },
        "interventions": [
            intervention_payload(item, index) for index, item in enumerate(profile["whatif"])
        ],
        "branch_count": 3,
        "horizon_years": 10,
        "extended_horizons": [20, 30],
        "request_notes": profile["question"],
        "preferred_language": preferred_language,
    }
