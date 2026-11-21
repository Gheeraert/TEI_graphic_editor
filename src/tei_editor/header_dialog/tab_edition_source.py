"""Onglets « Édition » et « Source » (phase 6). Regroupés dans un même
module (deux onglets simples) pour rester sous la limite indicative de
``CLAUDE.md`` sans multiplier les petits fichiers."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tei_editor.tei.header_model import EditionStatement, SourceDescription


class EditionTab(QWidget):
    """``editionStmt`` (mention d'édition + numéro) et ``extent``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        form = QFormLayout(self)
        self.text_field = QLineEdit(self)
        form.addRow("Mention d'édition", self.text_field)
        self.n_field = QLineEdit(self)
        form.addRow("Numéro (@n)", self.n_field)
        self.extent_field = QLineEdit(self)
        form.addRow("Étendue (extent)", self.extent_field)

    def load(self, edition: EditionStatement, extent: str) -> None:
        self.text_field.setText(edition.text)
        self.n_field.setText(edition.n or "")
        self.extent_field.setText(extent)

    def collect(self) -> tuple[EditionStatement, str]:
        edition = EditionStatement(text=self.text_field.text(), n=self.n_field.text().strip() or None)
        return edition, self.extent_field.text()


class SourceTab(QWidget):
    """``sourceDesc`` : ``bibl`` texte libre ou ``msDesc`` minimal — à
    l'exclusion d'un ``msDesc`` complet (``docs/ROADMAP.md`` §5, phase 6 :
    « garde ça simple »)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.mode_combo = QComboBox(self)
        self.mode_combo.addItem("Bibliographie simple (bibl)", "bibl")
        self.mode_combo.addItem("Manuscrit minimal (msDesc)", "msDesc")
        self.mode_combo.currentIndexChanged.connect(self._sync_stack)
        layout.addWidget(self.mode_combo)

        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        self.bibl_text = QTextEdit(self)
        self.stack.addWidget(self.bibl_text)

        msdesc_page = QWidget(self)
        msdesc_form = QFormLayout(msdesc_page)
        self.msdesc_repository = QLineEdit(msdesc_page)
        msdesc_form.addRow("Dépôt (repository)", self.msdesc_repository)
        self.msdesc_idno = QLineEdit(msdesc_page)
        msdesc_form.addRow("Identifiant (idno)", self.msdesc_idno)
        self.msdesc_summary = QTextEdit(msdesc_page)
        msdesc_form.addRow("Résumé physique", self.msdesc_summary)
        self.stack.addWidget(msdesc_page)

    def _sync_stack(self) -> None:
        self.stack.setCurrentIndex(0 if self.mode_combo.currentData() == "bibl" else 1)

    def load(self, source: SourceDescription) -> None:
        index = self.mode_combo.findData(source.mode)
        self.mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self._sync_stack()
        self.bibl_text.setPlainText(source.bibl_text)
        self.msdesc_repository.setText(source.msdesc_repository)
        self.msdesc_idno.setText(source.msdesc_idno)
        self.msdesc_summary.setPlainText(source.msdesc_summary)

    def collect(self) -> SourceDescription:
        return SourceDescription(
            mode=self.mode_combo.currentData(),
            bibl_text=self.bibl_text.toPlainText(),
            msdesc_repository=self.msdesc_repository.text(),
            msdesc_idno=self.msdesc_idno.text(),
            msdesc_summary=self.msdesc_summary.toPlainText(),
        )
