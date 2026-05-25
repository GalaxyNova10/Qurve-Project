from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class JobStore:
    """File-backed job store, ready to be swapped for PostgreSQL/Redis metadata."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, params: dict[str, Any]) -> dict[str, Any]:
        job = {
            "task_id": str(uuid.uuid4()),
            "status": "pending",
            "progress": 0.0,
            "step": "Queued",
            "params": params,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        self.save(job)
        return job

    def get(self, task_id: str) -> dict[str, Any] | None:
        path = self._path(task_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, job: dict[str, Any]) -> None:
        job["updated_at"] = datetime.utcnow().isoformat() + "Z"
        path = self._path(job["task_id"])
        tmp = path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(job, handle, indent=2)
        tmp.replace(path)

    def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        job = self.get(task_id)
        if job is None:
            raise KeyError(task_id)
        job.update(changes)
        self.save(job)
        return job

    def list_recent(self, limit: int = 25) -> list[dict[str, Any]]:
        jobs = []
        for path in sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            with path.open("r", encoding="utf-8") as handle:
                jobs.append(json.load(handle))
            if len(jobs) >= limit:
                break
        return jobs

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

