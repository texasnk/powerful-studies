import tempfile
import unittest
from pathlib import Path

from core.models.deck_appearance import DeckAppearance, MAX_DESCRIPTION_LENGTH
from core.models.deck_document import DeckDocument
from core.repositories.workspace_repository import WorkspaceRepository
from core.services.appearance_service import AppearanceService


class AppearanceTests(unittest.TestCase):
    def test_invalid_appearance_is_safe_default(self):
        appearance = DeckAppearance.from_dict({"background": "javascript:bad", "description": "x" * 999})
        self.assertEqual(appearance.background, "")
        self.assertEqual(len(appearance.description), MAX_DESCRIPTION_LENGTH)

    def test_repository_is_profile_isolated_and_cleanup_removes_deleted_deck(self):
        with tempfile.TemporaryDirectory() as directory:
            first = AppearanceService(WorkspaceRepository(Path(directory) / "one"))
            second = AppearanceService(WorkspaceRepository(Path(directory) / "two"))
            first.save(10, DeckAppearance(description="Private"))
            self.assertEqual(second.appearance_for(10).description, "")
            first.cleanup({20})
            self.assertEqual(first.appearance_for(10).description, "")


class DocumentContractTests(unittest.TestCase):
    def test_document_contract_is_not_an_anki_note(self):
        document = DeckDocument.from_dict({"id": "doc-1", "deck_id": 42, "title": "Summary", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z", "tags": ["math"]})
        self.assertIsNotNone(document)
        self.assertEqual(document.deck_id, 42)
        self.assertIsNone(DeckDocument.from_dict({"deck_id": "42"}))


if __name__ == "__main__":
    unittest.main()
