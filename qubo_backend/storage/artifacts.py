from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    """Local artifact store with the same shape expected from object storage later."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.root / name

    def exists(self, name: str) -> bool:
        return self.path(name).exists()

    def read_json(self, name: str) -> dict[str, Any] | None:
        path = self.path(name)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def write_json(self, name: str, data: dict[str, Any], safe: bool = False) -> Path:
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + f".{id(data)}.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=False)
            if safe:
                # Try to replace, but don't crash if locked
                try:
                    tmp_path.replace(path)
                except OSError:
                    pass 
            else:
                tmp_path.replace(path)
        finally:
            if tmp_path.exists():
                try: tmp_path.unlink()
                except: pass
        return path

