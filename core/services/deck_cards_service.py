from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Sequence

from anki.collection import SearchNode
from anki.decks import DeckId
from anki.utils import strip_html_media


@dataclass(frozen=True)
class DeckCardItem:
    card_id: int
    note_id: int
    question: str
    answer: str


@dataclass(frozen=True)
class DeckCardPage:
    items: tuple[DeckCardItem, ...]
    total: int
    page: int
    pages: int


class DeckCardsService:
    """Reads real cards through Collection search APIs without modifying scheduling."""

    PAGE_SIZE = 25

    def page(
        self,
        col: Any,
        deck_id: int,
        deck_name: str,
        page: int,
        search: str = "",
        state: str = "all",
        include_subdecks: bool = False,
    ) -> DeckCardPage:
        query = self._query(col, deck_id, deck_name, search, state, include_subdecks)
        card_ids = list(col.find_cards(query, order="c.id asc"))
        pages = max(1, ceil(len(card_ids) / self.PAGE_SIZE))
        page = min(max(1, page), pages)
        selected_ids = card_ids[(page - 1) * self.PAGE_SIZE : page * self.PAGE_SIZE]
        items = tuple(self._item(col.get_card(card_id)) for card_id in selected_ids)
        return DeckCardPage(items=items, total=len(card_ids), page=page, pages=pages)

    def note_impact(self, col: Any, card_ids: Sequence[int]) -> tuple[set[int], int]:
        note_ids: set[int] = set()
        related_cards = 0
        for card_id in card_ids:
            card = col.get_card(card_id)
            note_id = int(card.note().id)
            if note_id not in note_ids:
                note_ids.add(note_id)
                related_cards += len(col.card_ids_of_note(note_id))
        return note_ids, related_cards

    def _query(self, col: Any, deck_id: int, deck_name: str, search: str, state: str, include_subdecks: bool) -> str:
        scope: str | SearchNode
        if include_subdecks:
            scope = SearchNode(deck=deck_name)
        else:
            scope = f"did:{DeckId(deck_id)}"
        terms: list[str | SearchNode] = [scope]
        if state in {"new", "learn", "review"}:
            terms.append(f"is:{state}")
        if search.strip():
            terms.append(search.strip())
        return col.build_search_string(*terms)

    @staticmethod
    def _item(card: Any) -> DeckCardItem:
        # A safe text representation prevents card template CSS/JS from leaking
        # into Anki's main WebView. Editing opens the native card/note editor.
        return DeckCardItem(
            card_id=int(card.id),
            note_id=int(card.note().id),
            question=strip_html_media(card.question()).strip(),
            answer=strip_html_media(card.answer()).strip(),
        )
