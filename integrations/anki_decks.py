from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeckView:
    id: int
    name: str
    path: tuple[str, ...]
    new_count: int
    learn_count: int
    review_count: int
    child_count: int
    filtered: bool


class AnkiDeckService:
    """Maps the scheduler's already-aggregated deck tree into UI-neutral views."""

    def root(self, tree: Any) -> list[DeckView]:
        return self.children(tree, ())

    def children(self, node: Any, parents: tuple[str, ...]) -> list[DeckView]:
        result = []
        for child in node.children:
            display_name = child.name.split("::")[-1]
            path = parents + (display_name,)
            result.append(DeckView(
                id=int(child.deck_id), name=display_name, path=path,
                new_count=int(child.new_count), learn_count=int(child.learn_count),
                review_count=int(child.review_count), child_count=len(child.children),
                filtered=bool(child.filtered),
            ))
        return result

    def find(self, node: Any, deck_id: int) -> Any | None:
        if int(getattr(node, "deck_id", 0)) == deck_id:
            return node
        for child in node.children:
            found = self.find(child, deck_id)
            if found:
                return found
        return None

    def ancestors(self, node: Any, deck_id: int | None) -> tuple[tuple[int, str], ...]:
        """Return the clickable ancestor path for a deck, excluding the tree root."""
        if deck_id is None:
            return ()

        def visit(current: Any, path: tuple[tuple[int, str], ...]) -> tuple[tuple[int, str], ...] | None:
            for child in current.children:
                child_path = path + ((int(child.deck_id), child.name.split("::")[-1]),)
                if int(child.deck_id) == deck_id:
                    return child_path
                if result := visit(child, child_path):
                    return result
            return None

        return visit(node, ()) or ()
