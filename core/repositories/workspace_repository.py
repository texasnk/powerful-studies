from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class WorkspaceRepository:
    """Versioned, profile-local JSON storage outside the collection and add-on source."""

    VERSION = 1

    def __init__(self, profile_directory: Path) -> None:
        self.path = profile_directory / "powerful-studies" / "workspace.json"

    def load(self) -> dict[str, Any]:
        default = {"schema_version": self.VERSION, "settings": {}, "appearances": {}, "documents": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default
        if not isinstance(data, dict) or data.get("schema_version") != self.VERSION:
            return default
        for key, expected in (("settings", dict), ("appearances", dict), ("documents", list)):
            if not isinstance(data.get(key), expected):
                return default
        return data

    def save(self, data: dict[str, Any]) -> None:
        if data.get("schema_version") != self.VERSION:
            raise ValueError("Unsupported workspace schema")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(prefix="workspace-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as output:
                json.dump(data, output, ensure_ascii=False, indent=2, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary_name, self.path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
