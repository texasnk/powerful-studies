from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anki.decks import DeckId
from anki.notes import NoteId
from aqt import dialogs, gui_hooks, mw
from aqt.browser.browser import Browser
from aqt.browser.previewer import Previewer
from aqt.deckbrowser import DeckBrowser
from aqt.deckoptions import display_options_for_deck, display_options_for_deck_id
from aqt.operations.deck import add_deck, remove_decks, rename_deck, set_current_deck
from aqt.operations.note import remove_notes
from aqt.overview import Overview
from aqt.reviewer import Reviewer
from aqt.qt import QAction, QCursor, QHBoxLayout, QMenu, QPushButton
from aqt.utils import askUser, getOnlyText, showWarning

from ..core.repositories.workspace_repository import WorkspaceRepository
from ..core.services.appearance_service import AppearanceService
from ..core.services.deck_cards_service import DeckCardsService
from ..integrations.anki_decks import AnkiDeckService
from ..ui.appearance_dialog import AppearanceDialog
from ..ui.creation_dialogs import SubdeckDialog
from ..ui.settings_dialog import SettingsDialog

DEFAULT_SETTINGS = {"enabled": True, "overview_enabled": True, "reviewer_enabled": True, "reviewer_compatibility_mode": True, "reviewer_visual_layout": True, "reviewer_card_width": 960, "reviewer_base_typography": True, "reviewer_highlight_answer": True, "show_descriptions": True, "show_counters": True, "sort": "name", "icon_style": "folder", "animations": True, "ambient_background": False}
PREFIX = "powerful-studies:"


class CardPreviewer(Previewer):
    def __init__(self, card: Any) -> None:
        super().__init__(parent=None, mw=mw, on_close=lambda: None)
        self._card = card

    def card(self) -> Any:
        return self._card

    def card_changed(self) -> bool:
        return False

    def _create_gui(self) -> None:
        super()._create_gui()
        controls = QHBoxLayout()
        controls.addStretch()
        self._show_answer_button = QPushButton("Mostrar verso")
        self._show_answer_button.setMinimumWidth(180)
        self._show_answer_button.clicked.connect(self._toggle_side)
        controls.addWidget(self._show_answer_button)
        controls.addStretch()
        self.vbox.insertLayout(1, controls)

    def _toggle_side(self) -> None:
        self._state = "answer" if self._state == "question" else "question"
        self.render_card()

    def _render_scheduled(self) -> None:
        super()._render_scheduled()
        self._show_answer_button.setText(
            "Mostrar frente" if self._state == "answer" else "Mostrar verso"
        )
        if self._state == "answer" and self._web is not None:
            answer = DeckCardsService.answer_side(self._card)
            answer = self.mw.prepare_card_text_for_display(answer)
            self._web.eval(f"document.getElementById('qa').innerHTML = {json.dumps(answer)};")


class ExplorerController:
    def __init__(self) -> None:
        self.current_deck_id: int | None = None
        self.selected_deck_ids: set[int] = set()
        self.decks = AnkiDeckService()

    def repository(self) -> WorkspaceRepository:
        return WorkspaceRepository(Path(mw.pm.profileFolder()))

    def appearances(self) -> AppearanceService:
        return AppearanceService(self.repository())

    def settings(self) -> dict[str, Any]:
        return self.appearances().settings(DEFAULT_SETTINGS)

    def render(self, browser: DeckBrowser, content: Any) -> None:
        settings = self.settings()
        tree = getattr(browser, "_render_data", None)
        if tree is None:
            return
        root = tree.tree
        selected = self.decks.find(root, self.current_deck_id) if self.current_deck_id else None
        if self.current_deck_id is not None and selected is None:
            self.current_deck_id = None
        ancestors = self.decks.ancestors(root, self.current_deck_id) if selected else ()
        cards = self.decks.children(root if selected is None else selected, ())
        self.selected_deck_ids.intersection_update(card.id for card in cards)
        if settings["sort"] == "review":
            cards.sort(key=lambda card: (-card.review_count, card.name.casefold()))
        elif settings["sort"] == "name_desc":
            cards.sort(key=lambda card: card.name.casefold(), reverse=True)
        else:
            cards.sort(key=lambda card: card.name.casefold())
        content.tree = self._html(cards, ancestors, settings)
        content.stats = ""

    def _html(self, cards, ancestors, settings) -> str:
        breadcrumbs = ['<button class="ps-breadcrumb__home" data-action="home" aria-label="Início">⌂</button>']
        breadcrumbs.append('<button class="ps-breadcrumb__item" data-action="home">Meus decks</button>')
        for deck_id, label in ancestors:
            breadcrumbs.append('<span class="ps-separator">/</span>')
            breadcrumbs.append(f'<button class="ps-breadcrumb__item" data-action="open" data-id="{deck_id}">{html.escape(label)}</button>')
        selected_name = "Meus decks" if not ancestors else ancestors[-1][1]
        output = ['<tr class="ps-shell-row"><td class="ps-shell-cell" colspan="9">', f'<main id="ps-explorer" data-animations="{str(settings["animations"]).lower()}" data-ambient="{str(settings["ambient_background"]).lower()}">', '<header class="ps-header"><nav class="ps-breadcrumb" aria-label="Navegação">', *breadcrumbs, '</nav></header>', f'<section class="ps-section-heading"><div><h1>{html.escape(selected_name)} <span>({len(cards)})</span></h1><p>Organize e explore seus decks</p></div><div class="ps-tools"><input id="ps-search" type="search" placeholder="Buscar decks" aria-label="Buscar decks"><select id="ps-sort" aria-label="Ordenar decks"><option value="name"', ' selected' if settings["sort"] == "name" else '', '>Nome (A–Z)</option><option value="name_desc"', ' selected' if settings["sort"] == "name_desc" else '', '>Nome (Z–A)</option><option value="review"', ' selected' if settings["sort"] == "review" else '', '>Mais revisões</option></select><button class="ps-toolbar-button" data-action="settings" aria-label="Configurações">⚙</button></div></section>', '<section class="ps-deck-grid" aria-label="Decks">']
        selected_count = len(self.selected_deck_ids)
        output.append(f'<div class="ps-deck-bulk"><label><input id="ps-select-all" type="checkbox"> Selecionar tudo</label><span id="ps-selection-count">{selected_count} selecionado(s)</span><button data-action="clear-selection" id="ps-clear-selection" {"disabled" if not selected_count else ""}>Limpar</button><button data-action="delete-selected" id="ps-delete-selected" {"disabled" if not selected_count else ""}>Excluir selecionados</button></div>')
        appearances = self.appearances()
        for card in cards:
            appearance = appearances.appearance_for(card.id)
            color = appearance.background or "var(--ps-card)"
            description = html.escape(appearance.description) if settings["show_descriptions"] else ""
            icon = html.escape(appearance.emoji) if appearance.emoji else self._icon(appearance.icon)
            counters = "" if not settings["show_counters"] else f'<div class="ps-deck-card__stats"><span class="ps-stat ps-stat--new"><b>{card.new_count}</b> novos</span><span class="ps-stat ps-stat--learn"><b>{card.learn_count}</b> aprender</span><span class="ps-stat ps-stat--review"><b>{card.review_count}</b> revisar</span></div>'
            filtered = '<span class="ps-filtered">Filtrado</span>' if card.filtered else ""
            checked = " checked" if card.id in self.selected_deck_ids else ""
            output.append(f'<article class="ps-deck-card" style="--ps-custom-background:{html.escape(color)}" data-name="{html.escape(card.name.casefold())}" tabindex="0"><div class="ps-deck-card__header"><label class="ps-deck-card__select"><input type="checkbox" data-deck-select data-id="{card.id}"{checked} aria-label="Selecionar {html.escape(card.name)}"> Selecionar</label><button class="ps-deck-card__open" data-action="open" data-id="{card.id}" aria-label="Abrir {html.escape(card.name)}"><span class="ps-deck-card__icon">{icon}</span></button><button class="ps-deck-card__menu" data-action="menu" data-id="{card.id}" aria-label="Menu de {html.escape(card.name)}">•••</button></div><button class="ps-deck-card__content" data-action="open" data-id="{card.id}"><h3 class="ps-deck-card__title">{html.escape(card.name)}</h3><p class="ps-deck-card__description">{description}</p>{filtered}</button><footer class="ps-deck-card__footer"><span class="ps-deck-card__children">{card.child_count} subdeck(s)</span>{counters}<button class="ps-deck-card__study" data-action="study" data-id="{card.id}">Estudar</button></footer></article>')
        if not cards:
            output.append('<p class="ps-empty">Não há subdecks aqui. Use “Criar deck” na barra inferior do Anki.</p>')
        output.append('</section></main></td></tr>')
        return "".join(output)

    @staticmethod
    def _icon(name: str) -> str:
        icons = {"folder": "▰", "book": "▤", "spark": "✦", "target": "◎"}
        return icons.get(name, icons["folder"])

    def message(self, handled, message: str, context: Any):
        if not isinstance(context, DeckBrowser) or not message.startswith(PREFIX):
            return handled
        try:
            payload = json.loads(message[len(PREFIX):])
            action = payload["action"]
            if not isinstance(action, str):
                raise ValueError("action must be a string")
            deck_id = int(payload["id"]) if action in {"open", "study", "menu", "select"} else None
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return (True, None)
        if action == "home": self.current_deck_id = None; context.refresh()
        elif action == "open" and deck_id is not None: self._open(context, deck_id)
        elif action == "study" and deck_id is not None: self._study(deck_id)
        elif action == "menu" and deck_id is not None: self._menu(context, deck_id)
        elif action == "select" and deck_id is not None: self._select(context, deck_id, bool(payload.get("selected")))
        elif action == "select-all": self._select_all(context, payload.get("ids"))
        elif action == "clear-selection": self.selected_deck_ids.clear()
        elif action == "delete-selected": self.delete_selected(context)
        elif action == "settings": self.show_settings()
        elif action == "sort" and payload.get("value") in {"name", "name_desc", "review"}: self._change_sort(payload["value"]); context.refresh()
        return (True, None)

    def _open(self, browser: DeckBrowser, deck_id: int) -> None:
        node = self.decks.find(browser._render_data.tree, deck_id)
        if node is not None and node.children:
            self.current_deck_id = deck_id
            browser.refresh()
        else:
            self._study(deck_id)

    def _current_deck_ids(self, browser: DeckBrowser) -> set[int]:
        tree = getattr(browser, "_render_data", None)
        if tree is None:
            return set()
        root = tree.tree
        selected = self.decks.find(root, self.current_deck_id) if self.current_deck_id else None
        return {card.id for card in self.decks.children(root if selected is None else selected, ())}

    def _select(self, browser: DeckBrowser, deck_id: int, selected: bool) -> None:
        if deck_id not in self._current_deck_ids(browser):
            return
        if selected:
            self.selected_deck_ids.add(deck_id)
        else:
            self.selected_deck_ids.discard(deck_id)

    def _select_all(self, browser: DeckBrowser, ids: Any) -> None:
        if not isinstance(ids, list):
            return
        selectable = self._current_deck_ids(browser)
        try:
            requested = {int(deck_id) for deck_id in ids}
        except (TypeError, ValueError):
            return
        self.selected_deck_ids.update(selectable.intersection(requested))

    def delete_selected(self, browser: DeckBrowser) -> None:
        deck_ids = sorted(self.selected_deck_ids.intersection(self._current_deck_ids(browser)))
        if not deck_ids:
            return
        names = [mw.col.decks.name_if_exists(DeckId(deck_id)) for deck_id in deck_ids]
        if any(name is None for name in names):
            return
        if not askUser(f"Excluir {len(deck_ids)} deck(s) selecionado(s), seus subdecks e cartões?", parent=mw):
            return
        remove_decks(parent=mw, deck_ids=[DeckId(deck_id) for deck_id in deck_ids], deck_name=", ".join(name for name in names if name)).success(lambda _: self._after_bulk_delete(browser)).run_in_background(initiator=self)

    def _after_bulk_delete(self, browser: DeckBrowser) -> None:
        self.selected_deck_ids.clear()
        browser.refresh()

    def _change_sort(self, sort: str) -> None:
        settings = self.settings()
        settings["sort"] = sort
        self.appearances().save_settings(settings)

    def _study(self, deck_id: int) -> None:
        if mw.col.decks.name_if_exists(DeckId(deck_id)) is None:
            return
        set_current_deck(parent=mw, deck_id=DeckId(deck_id)).success(lambda _: mw.onOverview()).run_in_background(initiator=self)

    def _menu(self, browser: DeckBrowser, deck_id: int) -> None:
        name = mw.col.decks.name_if_exists(DeckId(deck_id))
        if name is None:
            return
        menu = QMenu(mw)
        for label, callback in [("Estudar", lambda: self._study(deck_id)), ("Personalizar deck", lambda: self.customize(deck_id, name)), ("Opções do deck", lambda: display_options_for_deck_id(DeckId(deck_id))), ("Renomear", lambda: self.rename(deck_id, name)), ("Exportar", lambda: mw.onExport(did=DeckId(deck_id))), ("Excluir", lambda: self.delete(deck_id, name))]:
            action = menu.addAction(label)
            action.triggered.connect(lambda _checked=False, callback=callback: callback())
        menu.popup(QCursor.pos())

    def delete(self, deck_id: int, name: str) -> None:
        if askUser(f"Excluir o deck '{name}' e seus cartões?", parent=mw):
            remove_decks(parent=mw, deck_ids=[DeckId(deck_id)], deck_name=name).run_in_background()

    def customize(self, deck_id: int, name: str) -> None:
        service = self.appearances(); dialog = AppearanceDialog(mw, name, service.appearance_for(deck_id))
        if dialog.exec():
            if dialog.restore_defaults: service.restore_default(deck_id)
            else: service.save(deck_id, dialog.value())
            mw.deckBrowser.refresh()

    def rename(self, deck_id: int, name: str) -> None:
        if new_name := getOnlyText("Novo nome do deck", default=name, parent=mw).strip():
            rename_deck(parent=mw, deck_id=DeckId(deck_id), new_name=new_name).run_in_background()

    def show_settings(self) -> None:
        dialog = SettingsDialog(mw, self.settings())
        if dialog.exec():
            self.appearances().save_settings(dialog.value()); mw.deckBrowser.refresh()

    def disable_for_native(self) -> None:
        settings = self.settings(); settings["enabled"] = False; self.appearances().save_settings(settings); mw.deckBrowser.refresh()

    def inject_assets(self, content, context) -> None:
        if isinstance(context, DeckBrowser):
            package = mw.addonManager.addonFromModule(__package__.split(".")[0])
            content.css.append(f"/_addons/{package}/web/explorer.css")
            content.js.append(f"/_addons/{package}/web/explorer.js")
        elif isinstance(context, Overview):
            package = mw.addonManager.addonFromModule(__package__.split(".")[0])
            content.css.append(f"/_addons/{package}/web/overview.css")
            content.js.append(f"/_addons/{package}/web/overview.js")
        elif isinstance(context, Reviewer):
            package = mw.addonManager.addonFromModule(__package__.split(".")[0])
            content.css.append(f"/_addons/{package}/web/reviewer.css")
            content.js.append(f"/_addons/{package}/web/reviewer.js")

    def refresh_after_operation(self, changes, handler) -> None:
        if mw.state == "deckBrowser":
            deck_ids = {int(deck.id) for deck in mw.col.decks.all_names_and_ids()}
            self.appearances().cleanup(deck_ids)


@dataclass
class OverviewState:
    deck_id: int = 0
    page: int = 1
    search: str = ""
    state: str = "all"
    include_subdecks: bool = False
    selected_card_ids: set[int] = field(default_factory=set)


class DeckOverviewController:
    def __init__(self) -> None:
        self.cards = DeckCardsService()
        self.state = OverviewState()

    def render(self, overview: Overview, content: Any) -> None:
        deck = mw.col.decks.current()
        deck_id = int(deck["id"])
        if self.state.deck_id != deck_id:
            self.state = OverviewState(deck_id=deck_id)
        page = self.cards.page(mw.col, deck_id, deck["name"], self.state.page, self.state.search, self.state.state, self.state.include_subdecks)
        self.state.page = page.page
        content.deck = ""
        content.shareLink = ""
        content.desc = ""
        content.table = self._html(deck, page)

    def render_finished(self, overview: Overview) -> None:
        """Keep the workspace available when Anki routes an empty queue to Congrats."""
        if not mw.col.sched._is_finished():
            return
        deck = mw.col.decks.current()
        deck_id = int(deck["id"])
        if self.state.deck_id != deck_id:
            self.state = OverviewState(deck_id=deck_id)
        page = self.cards.page(
            mw.col,
            deck_id,
            deck["name"],
            self.state.page,
            self.state.search,
            self.state.state,
            self.state.include_subdecks,
        )
        overview.web.stdHtml(
            self._html(deck, page),
            context=overview,
        )

    def _html(self, deck: dict[str, Any], page: Any) -> str:
        counts = mw.col.sched.counts()
        description = html.escape(str(deck.get("desc", "")).strip())
        selected_count = len(self.state.selected_card_ids)
        cards = "".join(self._card_html(item) for item in page.items)
        state_options = "".join(
            f'<option value="{value}"{" selected" if self.state.state == value else ""}>{label}</option>'
            for value, label in (("all", "Todos"), ("new", "Novos"), ("learn", "Aprendendo"), ("review", "Revisão"))
        )
        if not cards:
            cards = '<p class="ps-overview__empty">Nenhum flashcard corresponde aos filtros atuais.</p>'
        breadcrumb = " / ".join(html.escape(part) for part in deck["name"].split("::"))
        checked = " checked" if self.state.include_subdecks else ""
        subdecks = "".join(self._subdeck_html(item) for item in self._direct_subdecks(deck["name"]))
        if not subdecks:
            subdecks = '<p class="ps-overview__empty">Nenhum subdeck neste nível.</p>'
        finished = '<p class="ps-overview__finished">Revisões concluídas por hoje.</p>' if not any(counts[:3]) else ""
        return f'''<main id="ps-overview">
<header class="ps-overview__header"><div><nav class="ps-overview__breadcrumb"><button data-overview-action="decks">Meus decks</button> / {breadcrumb}</nav><h1>{html.escape(deck["name"].split("::")[-1])}</h1><p>{description}</p>{finished}</div><div class="ps-overview__actions"><button data-overview-action="new-subdeck">Novo subdeck</button><button data-overview-action="new-card">Novo card</button><button data-overview-action="study" class="ps-overview__study">Estudar</button><button data-overview-action="options">Configurações</button></div></header>
<section class="ps-overview__summary"><div><b>{counts[0]}</b><span>Novos</span></div><div><b>{counts[1]}</b><span>Aprendendo</span></div><div><b>{counts[2]}</b><span>Revisar</span></div><div><b>{page.total}</b><span>Flashcards</span></div></section>
<section class="ps-overview__subdecks"><header><h2>Subdecks</h2><button data-overview-action="new-subdeck">Novo subdeck</button></header><div class="ps-overview__subdeck-grid">{subdecks}</div></section>
<section class="ps-overview__cards"><header><div><h2>Flashcards <span>({page.total})</span></h2><p>{selected_count} selecionado(s)</p></div><div class="ps-overview__filters"><input id="ps-card-search" value="{html.escape(self.state.search, quote=True)}" placeholder="Buscar conteúdo"><select id="ps-card-state">{state_options}</select><label><input id="ps-include-subdecks" type="checkbox"{checked}> Incluir subdecks</label></div></header>
<div class="ps-overview__bulk"><label><input id="ps-select-page" type="checkbox"> Selecionar página</label><button data-overview-action="clear">Desmarcar</button><button data-overview-action="delete-selected" {'disabled' if not selected_count else ''}>Excluir selecionados</button></div><div class="ps-card-list">{cards}</div><footer class="ps-pagination"><button data-overview-action="previous" {'disabled' if page.page <= 1 else ''}>Anterior</button><span>Página {page.page} de {page.pages}</span><button data-overview-action="next" {'disabled' if page.page >= page.pages else ''}>Próxima</button></footer></section></main>'''

    def _card_html(self, item: Any) -> str:
        checked = " checked" if item.card_id in self.state.selected_card_ids else ""
        return f'''<article class="ps-flashcard" data-card-id="{item.card_id}"><header><label><input class="ps-card-select" type="checkbox" data-card-id="{item.card_id}"{checked}> Selecionar</label><div><button data-overview-action="answer" data-card-id="{item.card_id}">Ver resposta</button><button data-overview-action="preview" data-card-id="{item.card_id}" aria-label="Visualizar flashcard" title="Visualizar flashcard">&#128065;</button><button data-overview-action="edit" data-card-id="{item.card_id}">Editar</button><button class="ps-flashcard__delete" data-overview-action="delete" data-card-id="{item.card_id}" aria-label="Excluir flashcard" title="Excluir flashcard">&#128465;</button></div></header><div class="ps-flashcard__question">{html.escape(item.question)}</div><div class="ps-flashcard__answer" hidden>{html.escape(item.answer)}</div></article>'''

    @staticmethod
    def _subdeck_html(deck: Any) -> str:
        return f'<article class="ps-overview__subdeck"><span>▰</span><h3>{html.escape(deck.name.rsplit("::", 1)[-1])}</h3><button data-overview-action="open-deck" data-deck-id="{int(deck.id)}">Abrir</button></article>'

    @staticmethod
    def _direct_subdecks(parent_name: str) -> list[Any]:
        prefix = f"{parent_name}::"
        return [deck for deck in mw.col.decks.all_names_and_ids() if deck.name.startswith(prefix) and "::" not in deck.name[len(prefix):]]

    def message(self, handled, message: str, context: Any):
        if not isinstance(context, Overview) or not message.startswith(PREFIX):
            return handled
        try:
            payload = json.loads(message[len(PREFIX):])
            action = payload["action"]
            if not isinstance(action, str):
                raise ValueError()
            card_id = int(payload["card_id"]) if action in {"select", "answer", "preview", "edit", "delete"} else None
            deck_id = int(payload["deck_id"]) if action == "open-deck" else None
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return (True, None)
        if action == "study":
            mw.col.startTimebox(); mw.moveToState("review")
        elif action == "decks":
            mw.moveToState("deckBrowser")
        elif action == "open-deck" and deck_id is not None:
            set_current_deck(parent=mw, deck_id=DeckId(deck_id)).success(lambda _: mw.onOverview()).run_in_background(initiator=self)
        elif action == "new-subdeck":
            self._new_subdeck(context)
        elif action == "new-card":
            self._new_card(context)
        elif action == "options":
            display_options_for_deck(mw.col.decks.current())
        elif action == "query":
            self._update_query(payload); context.refresh()
        elif action == "page":
            try:
                self.state.page = max(1, int(payload.get("page", 1)))
            except (TypeError, ValueError):
                return (True, None)
            context.refresh()
        elif action == "select" and card_id is not None:
            self._select(card_id, bool(payload.get("selected"))); context.refresh()
        elif action == "select-page":
            self._select_page(bool(payload.get("selected"))); context.refresh()
        elif action == "clear":
            self.state.selected_card_ids.clear(); context.refresh()
        elif action == "answer" and card_id is not None:
            context.web.eval(f"document.querySelector('[data-card-id=\"{card_id}\"] .ps-flashcard__answer').hidden = false;")
        elif action == "preview" and card_id is not None:
            self._preview(card_id)
        elif action == "edit" and card_id is not None:
            self._edit(card_id)
        elif action == "delete" and card_id is not None:
            self._delete_cards(context, {card_id})
        elif action == "delete-selected":
            self._delete_cards(context, self.state.selected_card_ids)
        return (True, None)

    def _new_subdeck(self, overview: Overview) -> None:
        parent = mw.col.decks.current()
        dialog = SubdeckDialog(mw, parent["name"])
        if not dialog.exec():
            return
        name = dialog.name.text().strip()
        if not name or "::" in name:
            showWarning("Informe um nome de subdeck sem '::'.", parent=mw)
            return
        full_name = f'{parent["name"]}::{name}'
        if mw.col.decks.id_for_name(full_name) is not None:
            showWarning("Já existe um deck com esse nome neste nível.", parent=mw)
            return
        add_deck(parent=mw, name=full_name).success(lambda _: overview.refresh()).run_in_background(initiator=self)

    def _new_card(self, overview: Overview) -> None:
        self._open_native_add_cards(int(mw.col.decks.current()["id"]))

    @staticmethod
    def _open_native_add_cards(deck_id: int) -> None:
        window = dialogs.open("NewAddCards", mw)
        window.load_new_note(deck_id=DeckId(deck_id))

    def _update_query(self, payload: dict[str, Any]) -> None:
        self.state.search = str(payload.get("search", ""))[:500]
        self.state.state = payload.get("state") if payload.get("state") in {"all", "new", "learn", "review"} else "all"
        self.state.include_subdecks = bool(payload.get("include_subdecks"))
        self.state.page = 1
        self.state.selected_card_ids.clear()

    def _select(self, card_id: int, selected: bool) -> None:
        if selected:
            self.state.selected_card_ids.add(card_id)
        else:
            self.state.selected_card_ids.discard(card_id)

    def _select_page(self, selected: bool) -> None:
        deck = mw.col.decks.current()
        page = self.cards.page(mw.col, int(deck["id"]), deck["name"], self.state.page, self.state.search, self.state.state, self.state.include_subdecks)
        card_ids = {item.card_id for item in page.items}
        if selected:
            self.state.selected_card_ids.update(card_ids)
        else:
            self.state.selected_card_ids.difference_update(card_ids)

    def _edit(self, card_id: int) -> None:
        card = mw.col.get_card(card_id)
        Browser(mw, card=card, search=(f"nid:{int(card.note().id)}",))

    @staticmethod
    def _preview(card_id: int) -> None:
        previewer = CardPreviewer(mw.col.get_card(card_id))
        previewer.open()

    def _delete_cards(self, overview: Overview, card_ids: set[int]) -> None:
        if not card_ids:
            return
        note_ids, impacted_cards = self.cards.note_impact(mw.col, sorted(card_ids))
        message = f"Excluir {len(card_ids)} card(s) selecionado(s)? Isso removerá {len(note_ids)} nota(s) e {impacted_cards} card(s) associado(s), inclusive cards irmãos."
        if not askUser(message, parent=mw):
            return
        remove_notes(parent=mw, note_ids=[NoteId(note_id) for note_id in note_ids]).success(lambda _: self._after_delete(overview, card_ids)).run_in_background(initiator=self)

    def _after_delete(self, overview: Overview, card_ids: set[int]) -> None:
        self.state.selected_card_ids.difference_update(card_ids)
        overview.refresh()

    def refresh_after_operation(self, changes: Any, handler: Any) -> None:
        if mw.state == "overview" and (getattr(changes, "card", False) or getattr(changes, "note_text", False)):
            mw.overview.refresh()


class ReviewerController:
    """Adds navigation and note actions without replacing Anki's reviewer flow."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self._card_css = (root / "web" / "reviewer.css").read_text(encoding="utf-8")
        self._card_javascript = (root / "web" / "reviewer.js").read_text(encoding="utf-8")

    def _payload(self, card: Any, side: str) -> dict[str, Any]:
        settings = ExplorerController().settings()
        deck_name = mw.col.decks.name(card.current_deck_id())
        return {
            "breadcrumb": ["Meus decks", *deck_name.split("::")],
            "compatibility": settings.get("reviewer_compatibility_mode", True),
            "visualLayout": settings.get("reviewer_visual_layout", True),
            "baseTypography": settings.get("reviewer_base_typography", True),
            "highlightAnswer": settings.get("reviewer_highlight_answer", True),
            "cardWidth": min(1000, max(900, int(settings.get("reviewer_card_width", 960)))),
            "side": side,
        }

    @staticmethod
    def _inline_json(value: dict[str, Any]) -> str:
        """Encode JSON safely when it is placed inside an inline script."""
        return json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    def show_card(self, card: Any) -> None:
        """Synchronize metadata after Anki has shown a question or answer."""
        side = "answer" if mw.reviewer.state == "answer" else "question"
        payload_json = self._inline_json(self._payload(card, side))
        mw.web.eval(
            f"window.powerfulStudiesReview?.show({payload_json});"
        )

    def prepare_card_html(self, text: str, card: Any, kind: str) -> str:
        if kind not in {"reviewQuestion", "reviewAnswer"}:
            return text
        if not ExplorerController().settings().get("reviewer_visual_layout", True):
            return text
        side = "question" if kind == "reviewQuestion" else "answer"
        if side == "answer":
            text = DeckCardsService.answer_side(card)
        payload_json = self._inline_json(self._payload(card, side))
        bootstrap = ""
        if side == "question":
            bootstrap = f"<style id=\"ps-review-card-style\">{self._card_css}</style><script>{self._card_javascript}</script>"
        hook = f"<script>onUpdateHook.push(function(){{window.powerfulStudiesReview?.show({payload_json});}});</script>"
        title = "Frente" if side == "question" else "Verso"
        return f'{bootstrap}<section class="ps-review-panel ps-review-panel--{side}" data-ps-card-id="{int(card.id)}"><h2 class="ps-review-panel__title">{title}</h2><div class="ps-review-panel__content">{text}</div></section>{hook}'

    def end(self) -> None:
        # The review page can stay alive between transitions; remove stale controls.
        mw.web.eval("window.powerfulStudiesReview && window.powerfulStudiesReview.clear();")

    def message(self, handled, message: str, context: Any):
        if not isinstance(context, Reviewer) or not message.startswith(PREFIX):
            return handled
        try:
            payload = json.loads(message[len(PREFIX):])
            action = payload["action"]
            if action not in {"reviewer-decks", "reviewer-overview", "reviewer-edit", "reviewer-delete"}:
                return (True, None)
        except (KeyError, TypeError, json.JSONDecodeError):
            return (True, None)
        if action == "reviewer-decks":
            mw.moveToState("deckBrowser")
        elif action == "reviewer-overview":
            mw.moveToState("overview")
        elif action == "reviewer-edit":
            self._edit_current(context)
        elif action == "reviewer-delete":
            self._delete_current(context)
        return (True, None)

    def _edit_current(self, reviewer: Reviewer) -> None:
        if reviewer.card is not None:
            Browser(mw, card=reviewer.card, search=(f"nid:{int(reviewer.card.note().id)}",))

    def _delete_current(self, reviewer: Reviewer) -> None:
        if reviewer.card is None:
            return
        card = reviewer.card
        note_id = int(card.note().id)
        related_cards = len(mw.col.card_ids_of_note(NoteId(note_id)))
        message = f"Excluir a nota deste flashcard? Isso removerá {related_cards} card(s) gerado(s) por esta nota."
        if not askUser(message, parent=mw):
            return
        remove_notes(parent=mw, note_ids=[NoteId(note_id)]).run_in_background(initiator=self)


controller = ExplorerController()
overview_controller = DeckOverviewController()
reviewer_controller = ReviewerController()


def install() -> None:
    gui_hooks.deck_browser_will_render_content.append(controller.render)
    gui_hooks.overview_will_render_content.append(overview_controller.render)
    gui_hooks.overview_did_refresh.append(overview_controller.render_finished)
    gui_hooks.webview_will_set_content.append(controller.inject_assets)
    gui_hooks.webview_did_receive_js_message.append(controller.message)
    gui_hooks.webview_did_receive_js_message.append(overview_controller.message)
    gui_hooks.webview_did_receive_js_message.append(reviewer_controller.message)
    gui_hooks.operation_did_execute.append(controller.refresh_after_operation)
    gui_hooks.operation_did_execute.append(overview_controller.refresh_after_operation)
    gui_hooks.reviewer_did_show_question.append(reviewer_controller.show_card)
    gui_hooks.reviewer_did_show_answer.append(reviewer_controller.show_card)
    gui_hooks.reviewer_will_end.append(reviewer_controller.end)
    gui_hooks.card_will_show.append(reviewer_controller.prepare_card_html)
    action = QAction("Powerful Studies", mw)
    action.triggered.connect(controller.show_settings)
    mw.form.menuTools.addAction(action)
