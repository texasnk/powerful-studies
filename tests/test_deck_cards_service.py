import unittest

from core.services.deck_cards_service import DeckCardsService


class FakeNote:
    def __init__(self, note_id):
        self.id = note_id


class FakeCard:
    def __init__(self, card_id):
        self.id = card_id

    def note(self):
        return FakeNote(self.id // 2)

    def question(self):
        return f"<b>Question {self.id}</b>"

    def answer(self):
        return f"<i>Answer {self.id}</i>"


class FakeCollection:
    def build_search_string(self, *terms):
        return " ".join(str(term) for term in terms)

    def find_cards(self, query, order=False):
        self.query = query
        return list(range(1, 61))

    def get_card(self, card_id):
        return FakeCard(card_id)

    def card_ids_of_note(self, note_id):
        return [note_id * 2, note_id * 2 + 1]


class DeckCardsServiceTests(unittest.TestCase):
    def test_paginates_real_card_ids_and_strips_html(self):
        page = DeckCardsService().page(FakeCollection(), 100, "Study", page=2)
        self.assertEqual(page.total, 60)
        self.assertEqual(page.page, 2)
        self.assertEqual(len(page.items), 25)
        self.assertEqual(page.items[0].card_id, 26)
        self.assertEqual(page.items[0].question, "Question 26")

    def test_reports_note_impact_separately_from_selected_cards(self):
        note_ids, impacted_cards = DeckCardsService().note_impact(FakeCollection(), [2, 3])
        self.assertEqual(note_ids, {1})
        self.assertEqual(impacted_cards, 2)


if __name__ == "__main__":
    unittest.main()
