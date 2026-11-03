from __future__ import annotations

from aqt.qt import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

from ..core.models.deck_appearance import DeckAppearance, MAX_DESCRIPTION_LENGTH, PALETTE


class AppearanceDialog(QDialog):
    def __init__(self, parent, deck_name: str, appearance: DeckAppearance) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Personalizar deck — {deck_name}")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.icon = QComboBox()
        # IDs map to bundled assets/icons/*.svg. The WebView uses a safe inline
        # glyph fallback so a corrupt/missing asset cannot break navigation.
        self.icon.addItems(["folder", "book", "spark", "target"])
        self.icon.setCurrentText(appearance.icon)
        self.emoji = QLineEdit(appearance.emoji)
        self.emoji.setMaxLength(16)
        self.color = QComboBox()
        self.color.addItem("Padrão", "")
        for value in PALETTE:
            self.color.addItem(value, value)
        self.color.addItem("Cor personalizada (cole #RRGGBB abaixo)", "custom")
        self.color.setEditable(True)
        self.color.setCurrentText(appearance.background or "Padrão")
        self.description = QTextEdit(appearance.description)
        self.description.setMaximumHeight(110)
        self.description.textChanged.connect(self._limit_description)
        form.addRow("Ícone", self.icon)
        form.addRow("Emoji", self.emoji)
        form.addRow("Fundo", self.color)
        form.addRow(f"Descrição (máx. {MAX_DESCRIPTION_LENGTH})", self.description)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore)
        layout.addWidget(buttons)
        self.restore_defaults = False

    def _limit_description(self) -> None:
        text = self.description.toPlainText()
        if len(text) > MAX_DESCRIPTION_LENGTH:
            self.description.setPlainText(text[:MAX_DESCRIPTION_LENGTH])
            self.description.moveCursor(self.description.textCursor().MoveOperation.End)

    def _restore(self) -> None:
        self.restore_defaults = True
        self.accept()

    def value(self) -> DeckAppearance:
        background = self.color.currentText().strip()
        if background in {"Padrão", "Cor personalizada (cole #RRGGBB abaixo)"}:
            background = ""
        return DeckAppearance.from_dict({"icon": self.icon.currentText(), "emoji": self.emoji.text().strip(), "background": background, "description": self.description.toPlainText().strip()})
