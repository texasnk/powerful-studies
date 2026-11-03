import unittest
from types import SimpleNamespace

from integrations.anki_decks import AnkiDeckService


def node(deck_id, name, children=(), filtered=False):
    return SimpleNamespace(deck_id=deck_id, name=name, children=list(children), new_count=1, learn_count=2, review_count=3, filtered=filtered)


class DeckTreeTests(unittest.TestCase):
    def test_only_direct_children_are_returned(self):
        algebra = node(3, "Estudos::Matemática::Álgebra")
        math = node(2, "Estudos::Matemática", [algebra])
        root = node(0, "", [node(1, "Estudos", [math])])
        service = AnkiDeckService()
        self.assertEqual([item.id for item in service.root(root)], [1])
        self.assertEqual([item.id for item in service.children(math, ())], [3])
        self.assertEqual(service.find(root, 3).name, "Estudos::Matemática::Álgebra")
        self.assertEqual(service.ancestors(root, 3), ((1, "Estudos"), (2, "Matemática"), (3, "Álgebra")))


if __name__ == "__main__":
    unittest.main()
