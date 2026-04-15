"""Engine selection for LifeScope readings."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

from lifescope.core import build_life_reading, normalize_payload
from lifescope.engine_mapper import to_simulation_request_payload


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIMULATE_LIFE_ROOT = PROJECT_ROOT.parent / "simulate_life"
TONE_ORDER = ["green", "red", "gold", "blue", "green"]


@contextmanager
def pushd(path: Path):
    previous = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(str(previous))


def selected_engine(explicit_engine: str = None) -> str:
    engine = explicit_engine or os.getenv("LIFESCOPE_ENGINE", "deterministic")
    normalized = str(engine or "").strip().lower()
    if normalized in ("kimi", "kimi2.5", "kimi-2.5", "moonshot", "simulate_life"):
        return "simulate_life"
    return "deterministic"


def fallback_on_engine_error() -> bool:
    value = os.getenv("LIFESCOPE_FALLBACK_ON_ENGINE_ERROR", "1")
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def _safe_error_message(error: Exception) -> str:
    message = str(error) or error.__class__.__name__
    for env_name in ("MOONSHOT_API_KEY", "kimi_api_key", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"):
        secret = os.getenv(env_name, "")
        if secret:
            message = message.replace(secret, "[redacted-secret]")
    message = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-secret]", message)
    return message[:500]


def _deterministic_reading(payload: Dict[str, Any], engine_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    reading = build_life_reading(payload)
    reading["engine"] = engine_metadata or {
        "mode": "deterministic",
        "provider": "local",
        "model": "deterministic-web-mvp",
    }
    return reading


def run_reading(payload: Dict[str, Any], engine: str = None, progress_hook=None) -> Dict[str, Any]:
    resolved = selected_engine(engine)
    if resolved == "simulate_life":
        try:
            return run_simulate_life_reading(payload, progress_hook=progress_hook)
        except Exception as error:
            if not fallback_on_engine_error():
                raise
            _engine_progress(
                progress_hook,
                "fallback",
                "simulate_life failed; returning deterministic fallback",
            )
            return _deterministic_reading(
                payload,
                {
                    "mode": "deterministic",
                    "provider": "local",
                    "model": "deterministic-web-mvp",
                    "fallback_from": "simulate_life",
                    "error": _safe_error_message(error),
                },
            )
    return _deterministic_reading(payload)


def _simulate_life_root() -> Path:
    return Path(os.getenv("SIMULATE_LIFE_ROOT", str(DEFAULT_SIMULATE_LIFE_ROOT))).resolve()


def _ensure_import_path(root: Path) -> None:
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def _engine_progress(progress_hook, stage: str, message: str) -> None:
    if progress_hook:
        progress_hook(stage, message)


def _adapt_progress_hook(progress_hook):
    if progress_hook is None:
        return None

    def hook(stage=None, message=None, *args, **kwargs):
        resolved_stage = stage
        resolved_message = message
        if resolved_stage is None and args:
            resolved_stage = args[0]
        if resolved_message is None and len(args) > 1:
            resolved_message = args[1]
        if resolved_stage is None:
            resolved_stage = kwargs.get("stage", "progress")
        if resolved_message is None:
            resolved_message = kwargs.get("message", "")
        _engine_progress(progress_hook, str(resolved_stage), str(resolved_message))

    return hook


def run_simulate_life_reading(payload: Dict[str, Any], progress_hook=None) -> Dict[str, Any]:
    root = _simulate_life_root()
    if not root.exists():
        raise RuntimeError("simulate_life root not found: {root}".format(root=root))
    _ensure_import_path(root)

    from simulated_life.config import ProviderConfig
    from simulated_life.models import SimulationRequest
    from simulated_life.providers import create_provider
    from simulated_life.simulator import run_simulation

    profile = normalize_payload(payload)
    request_payload = SimulationRequest.parse_obj(to_simulation_request_payload(profile))
    output_root = PROJECT_ROOT / "data" / "simulate_life_runs"
    db_path = PROJECT_ROOT / "data" / "simulate_life_engine.db"
    output_root.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _engine_progress(progress_hook, "config", "Loading Moonshot / Kimi 2.5 configuration")
    with pushd(root):
        config = ProviderConfig.from_env(
            provider_override="moonshot",
            model_override=os.getenv("LIFESCOPE_KIMI_MODEL", "kimi-k2.5"),
            db_path=str(db_path),
            output_root=str(output_root),
        )
        provider = create_provider(config)
        _engine_progress(progress_hook, "simulate_life", "Running simulate_life with Kimi 2.5")
        artifacts = run_simulation(
            request_payload,
            config,
            provider,
            output_root=str(output_root),
            progress_hook=_adapt_progress_hook(progress_hook),
        )

    return reading_from_simulation_artifacts(profile, artifacts)


def _branch_gain(branch) -> List[str]:
    gains = []
    for event in list(branch.life_events or [])[:2]:
        if str(event.impact_summary or "").strip():
            gains.append(event.impact_summary)
    if not gains and str(branch.final_state.career or "").strip():
        gains.append(branch.final_state.career)
    if not gains:
        gains.append(branch.summary[:90])
    return gains[:2]


def _branch_cost(branch) -> List[str]:
    costs = []
    for note in list(branch.uncertainty_notes or [])[:2]:
        costs.append(note)
    for outlook in list(branch.extended_outlooks or [])[:1]:
        costs.extend(list(outlook.major_risks or [])[:1])
    if not costs:
        costs.append("这条路径的真实代价仍需要更多个人约束来判断。")
    return costs[:2]


def _timeline_from_branch(branch) -> List[Dict[str, str]]:
    yearly = list(branch.yearly_path or [])
    if not yearly:
        return []
    selected = []
    for target in (1, 3, 10):
        match = None
        for item in yearly:
            if item.year_offset == target:
                match = item
                break
        if match is None and yearly:
            match = yearly[min(len(yearly) - 1, max(0, target - 1))]
        if match is not None:
            selected.append(
                {
                    "year": "{year} 年".format(year=match.year_offset),
                    "title": "路径阶段",
                    "body": match.summary,
                }
            )
    return selected


def reading_from_simulation_artifacts(profile: Dict[str, Any], artifacts) -> Dict[str, Any]:
    result = artifacts.result
    branches = []
    for index, branch in enumerate(result.branches):
        branches.append(
            {
                "id": branch.branch_id,
                "title": branch.title,
                "tone": TONE_ORDER[index % len(TONE_ORDER)],
                "probability": int(round(branch.probability * 100)),
                "confidence": int(round(branch.confidence * 100)),
                "landing": branch.summary,
                "upside": _branch_gain(branch),
                "watch": _branch_cost(branch),
            }
        )
    branches = sorted(branches, key=lambda item: item["probability"], reverse=True)
    confidence = int(round(sum(branch["confidence"] for branch in branches) / len(branches)))
    top = branches[0]
    challenger = branches[1] if len(branches) > 1 else branches[0]
    source_branch = result.branches[0]
    timeline = _timeline_from_branch(source_branch)
    if not timeline:
        timeline = build_life_reading(profile)["timeline"]

    global_uncertainty = list(result.global_uncertainty_notes or [])
    evidence = [
        "{title}: {summary}".format(title=ref.title, summary=ref.summary)
        for ref in list(result.evidence_catalog or [])[:5]
    ]
    if not evidence:
        evidence = build_life_reading(profile)["trust"]["evidence"]

    return {
        "run_id": result.run_id,
        "created_at": result.generated_at,
        "source": "simulate_life",
        "profile": profile,
        "profile_review": build_life_reading(profile)["profile_review"],
        "one_screen": {
            "title": "{name} 的 Kimi 2.5 人生路径推演".format(name=profile["name"]),
            "summary": result.baseline_summary,
            "confidence": confidence,
            "top_path": top["title"],
            "main_challenger": challenger["title"],
            "biggest_risk": top["watch"][0],
            "biggest_uncertainty": global_uncertainty[0] if global_uncertainty else "Kimi run completed; inspect dossier for residual risk.",
            "next_action": "修改一个 what-if 或补一个关键缺失信息后重跑。",
        },
        "branches": branches,
        "timeline": timeline,
        "trust": {
            "evidence": evidence,
            "missing": global_uncertainty or ["Kimi 2.5 已完成结构化推演；缺失信息见 analysis dossier。"],
            "rerun": [
                "只改一个假设重跑，观察概率排序是否移动。",
                "补充关系、城市、现金流或健康约束会明显改变置信度。",
                "查看完整 report.md 和 analysis_dossier.json 做质量审查。",
            ],
        },
        "safety": {
            "framing": "多路径模拟，不是命运预测。",
            "advice_boundary": "不提供医疗、法律、投资或心理诊断建议。",
            "privacy_mode": "simulate_life_artifacts_written_locally",
        },
        "engine": {
            "mode": "simulate_life",
            "provider": result.provider,
            "model": result.model,
            "output_dir": str(artifacts.output_dir),
            "simulation_json": str(artifacts.json_path),
            "report_path": str(artifacts.report_path),
            "visual_summary_path": str(artifacts.visual_summary_path),
            "dossier_path": str(artifacts.dossier_path),
        },
    }
