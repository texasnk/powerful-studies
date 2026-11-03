from __future__ import annotations

from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QTextCharFormat,
    QTextEdit,
    QTextListFormat,
    QVBoxLayout,
    QWidget,
    QFont,
)


class SubdeckDialog(QDialog):
    def __init__(self, parent: QWidget, parent_name: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo subdeck")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Nome do subdeck")
        self.description = QPlainTextEdit()
        self.description.setPlaceholderText("Descrição opcional")
        self.description.setMaximumHeight(100)
        parent_field = QLineEdit(parent_name)
        parent_field.setReadOnly(True)
        form.addRow("Deck pai", parent_field)
        form.addRow("Nome", self.name)
        form.addRow("Descrição", self.description)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Criar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CardDialog(QDialog):
    def __init__(self, parent: QWidget, deck_name: str, model_names: list[str]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo card")
        self.create_another = False
        layout = QVBoxLayout(self)
        form = QFormLayout()
        destination = QLineEdit(deck_name)
        destination.setReadOnly(True)
        self.model = QComboBox()
        self.model.addItems(model_names)
        self.front = QTextEdit()
        self.front.setPlaceholderText("Frente")
        self.front.setMinimumHeight(120)
        self.back = QTextEdit()
        self.back.setPlaceholderText("Verso")
        self.back.setMinimumHeight(120)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("tag1 tag2")
        form.addRow("Deck", destination)
        form.addRow("Tipo de nota", self.model)
        form.addRow("Frente", self._editor_with_toolbar(self.front))
        form.addRow("Verso", self._editor_with_toolbar(self.back))
        form.addRow("Tags", self.tags)
        layout.addLayout(form)
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        self.preview.setMinimumHeight(100)
        layout.addWidget(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Criar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.model.currentTextChanged.connect(self._update_field_labels)
        self.front.textChanged.connect(self._update_preview)
        self.back.textChanged.connect(self._update_preview)
        self._update_field_labels(self.model.currentText())

    @staticmethod
    def _editor_with_toolbar(editor: QTextEdit) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        tools = QHBoxLayout()
        for label, callback in (
            ("B", lambda: CardDialog._toggle_weight(editor)),
            ("I", lambda: CardDialog._toggle_property(editor, "italic")),
            ("U", lambda: CardDialog._toggle_property(editor, "underline")),
            ("• Lista", lambda: CardDialog._insert_list(editor, QTextListFormat.Style.ListDisc)),
            ("1. Lista", lambda: CardDialog._insert_list(editor, QTextListFormat.Style.ListDecimal)),
        ):
            button = QPushButton(label)
            button.setMaximumWidth(72)
            button.clicked.connect(callback)
            tools.addWidget(button)
        tools.addStretch()
        layout.addLayout(tools)
        layout.addWidget(editor)
        return container

    @staticmethod
    def _toggle_weight(editor: QTextEdit) -> None:
        value = QFont.Weight.Normal if editor.fontWeight() > QFont.Weight.Normal else QFont.Weight.Bold
        fmt = QTextCharFormat()
        fmt.setFontWeight(value)
        editor.mergeCurrentCharFormat(fmt)

    @staticmethod
    def _toggle_property(editor: QTextEdit, property_name: str) -> None:
        fmt = QTextCharFormat()
        if property_name == "italic":
            fmt.setFontItalic(not editor.fontItalic())
        else:
            fmt.setFontUnderline(not editor.fontUnderline())
        editor.mergeCurrentCharFormat(fmt)

    @staticmethod
    def _insert_list(editor: QTextEdit, style: QTextListFormat.Style) -> None:
        list_format = QTextListFormat()
        list_format.setStyle(style)
        editor.textCursor().createList(list_format)

    def _update_field_labels(self, model_name: str) -> None:
        is_cloze = "cloze" in model_name.casefold()
        self.front.setPlaceholderText("Texto com {{c1::trecho oculto}}" if is_cloze else "Frente")
        self.back.setPlaceholderText("Extra opcional" if is_cloze else "Verso")

    def _update_preview(self) -> None:
        self.preview.setHtml(
            f"<h3>Pré-visualização — Frente</h3>{self.front.toHtml()}"
            f"<hr><h3>Verso</h3>{self.back.toHtml()}"
        )

    def values(self) -> tuple[str, str, list[str], str]:
        tags = [tag for tag in self.tags.text().split() if tag]
        return self.front.toHtml().strip(), self.back.toHtml().strip(), tags, self.model.currentText()
