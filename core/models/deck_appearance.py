from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PALETTE = ("#D9F3E8", "#DDEBFF", "#EDE2FF", "#FFF1C9", "#FFE4C2", "#FFE0EA", "#E6E9E7")
MAX_DESCRIPTION_LENGTH = 530


@dataclass(frozen=True)
class DeckAppearance:
    icon: str = "folder"
    emoji: str = ""
    background: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, value: Any) -> "DeckAppearance":
        if not isinstance(value, dict):
            return cls()
        icon = value.get("icon", "folder")
        emoji = value.get("emoji", "")
        background = value.get("background", "")
        description = value.get("description", "")
        if not isinstance(icon, str) or icon not in {"folder", "book", "spark", "target"}:
            icon = "folder"
        if not isinstance(emoji, str) or len(emoji) > 16:
            emoji = ""
        if not isinstance(background, str) or (background and background not in PALETTE and not _is_hex(background)):
            background = ""
        if not isinstance(description, str):
            description = ""
        return cls(icon, emoji, background, description[:MAX_DESCRIPTION_LENGTH])

    def to_dict(self) -> dict[str, str]:
        return {"icon": self.icon, "emoji": self.emoji, "background": self.background, "description": self.description}


def _is_hex(value: str) -> bool:
    return len(value) == 7 and value.startswith("#") and all(char in "0123456789abcdefABCDEF" for char in value[1:])
