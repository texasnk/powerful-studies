from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeckDocument:
    """Metadata for a future Markdown workspace document, never an Anki Note."""

    id: str
    deck_id: int
    title: str
    created_at: str
    updated_at: str
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: Any) -> "DeckDocument | None":
        if not isinstance(value, dict):
            return None
        required = ("id", "deck_id", "title", "created_at", "updated_at")
        if not all(key in value for key in required) or not isinstance(value["deck_id"], int):
            return None
        if not all(isinstance(value[key], str) for key in ("id", "title", "created_at", "updated_at")):
            return None
        tags = value.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            tags = []
        return cls(value["id"], value["deck_id"], value["title"], value["created_at"], value["updated_at"], tuple(tags))
