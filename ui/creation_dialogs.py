from __future__ import annotations

from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
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


class BasicCardDialog(QDialog):
    def __init__(self, parent: QWidget, deck_name: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo card")
        self.create_another = False
        layout = QVBoxLayout(self)
        form = QFormLayout()
        destination = QLineEdit(deck_name)
        destination.setReadOnly(True)
        self.front = QPlainTextEdit()
        self.front.setPlaceholderText("Frente")
        self.front.setMinimumHeight(120)
        self.back = QPlainTextEdit()
        self.back.setPlaceholderText("Verso")
        self.back.setMinimumHeight(120)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("tag1 tag2")
        form.addRow("Deck", destination)
        form.addRow("Frente", self.front)
        form.addRow("Verso", self.back)
        form.addRow("Tags", self.tags)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Criar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, list[str]]:
        tags = [tag for tag in self.tags.text().split() if tag]
        return self.front.toPlainText().strip(), self.back.toPlainText().strip(), tags
