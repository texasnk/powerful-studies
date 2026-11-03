from __future__ import annotations

from ..models.deck_document import DeckDocument
from ..repositories.workspace_repository import WorkspaceRepository


class DocumentService:
    """Persistence contract only; Markdown bodies deliberately have no storage in Phase 1."""

    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository

    def for_deck(self, deck_id: int) -> list[DeckDocument]:
        return [document for item in self.repository.load()["documents"] if (document := DeckDocument.from_dict(item)) and document.deck_id == deck_id]
