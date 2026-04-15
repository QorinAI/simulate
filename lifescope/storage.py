"""Local JSON storage for LifeScope MVP runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


RAW_FIELDS = {"background", "interests", "question", "constraints"}


def _replacement(field: str, value: str) -> str:
    return "[redacted:{field}:{count} chars]".format(field=field, count=len(value))


def _redact_strings(value: Any, raw_values: Dict[str, str]):
    if isinstance(value, str):
        redacted = value
        for field, raw in raw_values.items():
            if raw:
                redacted = redacted.replace(raw, _replacement(field, raw))
        return redacted
    if isinstance(value, list):
        return [_redact_strings(item, raw_values) for item in value]
    if isinstance(value, dict):
        return {key: _redact_strings(item, raw_values) for key, item in value.items()}
    return value


def redacted_payload(reading: Dict[str, Any]) -> Dict[str, Any]:
    """Return a storage-safe snapshot.

    The MVP stores generated output and non-sensitive profile fields by default.
    Raw free-text fields are replaced with length metadata so local demos do not
    accumulate private life stories on disk.
    """
    stored = json.loads(json.dumps(reading, ensure_ascii=False))
    profile = stored.get("profile") or {}
    raw_values = {}
    for field in RAW_FIELDS:
        value = str(profile.get(field) or "")
        raw_values[field] = value
        profile[field] = {
            "redacted": True,
            "char_count": len(value),
        }
    stored["profile"] = profile
    return _redact_strings(stored, raw_values)


class RunStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.index_path = self.root / "index.jsonl"

    def ensure(self) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure()
        snapshot = redacted_payload(reading)
        run_id = snapshot["run_id"]
        path = self.runs_dir / f"{run_id}.json"
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
        index_record = {
            "run_id": run_id,
            "created_at": snapshot.get("created_at"),
            "name": snapshot.get("profile", {}).get("name"),
            "top_path": snapshot.get("one_screen", {}).get("top_path"),
            "confidence": snapshot.get("one_screen", {}).get("confidence"),
            "path": str(path),
        }
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(index_record, ensure_ascii=False, sort_keys=True) + "\n")
        return {
            "run_id": run_id,
            "path": str(path),
            "redacted": True,
        }

    def get(self, run_id: str):
        safe_name = Path(str(run_id)).name
        path = self.runs_dir / f"{safe_name}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def delete(self, run_id: str) -> bool:
        safe_name = Path(str(run_id)).name
        path = self.runs_dir / f"{safe_name}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_recent(self, limit: int = 20):
        if not self.index_path.exists():
            return []
        rows = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(rows[-limit:]))
