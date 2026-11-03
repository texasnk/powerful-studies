from __future__ import annotations

from aqt.qt import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QVBoxLayout


class SettingsDialog(QDialog):
    def __init__(self, parent, settings: dict) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações — Powerful Studies")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.reviewer_compatibility_mode = QCheckBox("Modo de compatibilidade com templates")
        self.reviewer_compatibility_mode.setChecked(settings.get("reviewer_compatibility_mode", True))
        self.reviewer_visual_layout = QCheckBox("Usar layout visual do Powerful Studies na revisão")
        self.reviewer_visual_layout.setChecked(settings.get("reviewer_visual_layout", True))
        self.reviewer_card_width = QSpinBox()
        self.reviewer_card_width.setRange(900, 1000)
        self.reviewer_card_width.setSuffix(" px")
        self.reviewer_card_width.setValue(settings.get("reviewer_card_width", 960))
        self.reviewer_base_typography = QCheckBox("Aplicar tipografia base ao conteúdo")
        self.reviewer_base_typography.setChecked(settings.get("reviewer_base_typography", True))
        self.reviewer_highlight_answer = QCheckBox("Destacar visualmente a resposta")
        self.reviewer_highlight_answer.setChecked(settings.get("reviewer_highlight_answer", True))
        self.descriptions = QCheckBox("Mostrar descrições")
        self.descriptions.setChecked(settings["show_descriptions"])
        self.counters = QCheckBox("Mostrar contadores")
        self.counters.setChecked(settings["show_counters"])
        self.animations = QCheckBox("Ativar animações")
        self.animations.setChecked(settings["animations"])
        self.ambient = QCheckBox("Ativar fundo ambiente")
        self.ambient.setChecked(settings["ambient_background"])
        self.sort = QComboBox(); self.sort.addItem("Nome (A–Z)", "name"); self.sort.addItem("Nome (Z–A)", "name_desc"); self.sort.addItem("Mais revisões", "review")
        self.sort.setCurrentIndex(max(0, self.sort.findData(settings["sort"])))
        form.addRow(self.reviewer_visual_layout); form.addRow("Largura máxima do card", self.reviewer_card_width); form.addRow(self.reviewer_base_typography); form.addRow(self.reviewer_highlight_answer); form.addRow(self.reviewer_compatibility_mode); form.addRow(self.descriptions); form.addRow(self.counters); form.addRow("Ordenação", self.sort); form.addRow(self.animations); form.addRow(self.ambient)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value(self) -> dict:
        return {"enabled": True, "overview_enabled": True, "reviewer_enabled": True, "reviewer_compatibility_mode": self.reviewer_compatibility_mode.isChecked(), "reviewer_visual_layout": self.reviewer_visual_layout.isChecked(), "reviewer_card_width": self.reviewer_card_width.value(), "reviewer_base_typography": self.reviewer_base_typography.isChecked(), "reviewer_highlight_answer": self.reviewer_highlight_answer.isChecked(), "show_descriptions": self.descriptions.isChecked(), "show_counters": self.counters.isChecked(), "sort": self.sort.currentData(), "icon_style": "folder", "animations": self.animations.isChecked(), "ambient_background": self.ambient.isChecked()}
