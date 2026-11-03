from __future__ import annotations

from typing import Any

from ..models.deck_appearance import DeckAppearance
from ..repositories.workspace_repository import WorkspaceRepository


class AppearanceService:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository
        self._data = repository.load()

    def appearance_for(self, deck_id: int) -> DeckAppearance:
        return DeckAppearance.from_dict(self._data["appearances"].get(str(deck_id)))

    def save(self, deck_id: int, appearance: DeckAppearance) -> None:
        self._data["appearances"][str(deck_id)] = appearance.to_dict()
        self.repository.save(self._data)

    def restore_default(self, deck_id: int) -> None:
        self._data["appearances"].pop(str(deck_id), None)
        self.repository.save(self._data)

    def cleanup(self, active_deck_ids: set[int]) -> None:
        appearances = self._data["appearances"]
        stale = [key for key in appearances if not key.isdigit() or int(key) not in active_deck_ids]
        if stale:
            for key in stale:
                appearances.pop(key, None)
            self.repository.save(self._data)

    def settings(self, defaults: dict[str, Any]) -> dict[str, Any]:
        result = defaults.copy()
        stored = self._data["settings"]
        for key, value in stored.items():
            if key in result and isinstance(value, type(result[key])):
                result[key] = value
        return result

    def save_settings(self, settings: dict[str, Any]) -> None:
        self._data["settings"] = settings
        self.repository.save(self._data)
