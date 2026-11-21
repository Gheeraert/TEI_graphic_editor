"""Onglets « Encodage » et « Profil » (phase 6). Champs texte libre
(``docs/ROADMAP.md`` §5 : « des champs texte libre suffisent, pas de
structure fine ») sauf langues/mots-clés, listés en tableaux simples."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QTextEdit, QVBoxLayout, QWidget

from tei_editor.header_dialog.widgets import EditableTable
from tei_editor.tei.header_model import EncodingDescription, LanguageUsage, ProfileDescription


class EncodingTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        form = QFormLayout(self)
        self.project_desc_field = QTextEdit(self)
        form.addRow("Description du projet", self.project_desc_field)
        self.editorial_decl_field = QTextEdit(self)
        form.addRow("Principes éditoriaux", self.editorial_decl_field)
        self.tags_decl_field = QTextEdit(self)
        form.addRow("Déclaration de balisage", self.tags_decl_field)

    def load(self, encoding: EncodingDescription) -> None:
        self.project_desc_field.setPlainText(encoding.project_desc)
        self.editorial_decl_field.setPlainText(encoding.editorial_decl)
        self.tags_decl_field.setPlainText(encoding.tags_decl)

    def collect(self) -> EncodingDescription:
        return EncodingDescription(
            project_desc=self.project_desc_field.toPlainText(),
            editorial_decl=self.editorial_decl_field.toPlainText(),
            tags_decl=self.tags_decl_field.toPlainText(),
        )


class ProfileTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        languages_box = QGroupBox("Langues", self)
        languages_layout = QVBoxLayout(languages_box)
        self.languages_table = EditableTable(["Code (ident)", "Nom", "Usage (%)"], parent=languages_box)
        languages_layout.addWidget(self.languages_table)
        layout.addWidget(languages_box)

        keywords_box = QGroupBox("Mots-clés", self)
        keywords_layout = QVBoxLayout(keywords_box)
        self.keywords_table = EditableTable(["Mot-clé"], parent=keywords_box)
        keywords_layout.addWidget(self.keywords_table)
        layout.addWidget(keywords_box)

        form = QFormLayout()
        self.abstract_field = QTextEdit(self)
        form.addRow("Résumé", self.abstract_field)
        self.participants_field = QTextEdit(self)
        form.addRow("Participants", self.participants_field)
        layout.addLayout(form)

    def load(self, profile: ProfileDescription) -> None:
        self.languages_table.set_rows(
            [[lang.ident, lang.name, lang.usage_percent or ""] for lang in profile.languages]
        )
        self.keywords_table.set_rows([[keyword] for keyword in profile.keywords])
        self.abstract_field.setPlainText(profile.abstract)
        self.participants_field.setPlainText(profile.participants)

    def collect(self) -> ProfileDescription:
        languages = [
            LanguageUsage(ident=row[0], name=row[1], usage_percent=row[2].strip() or None)
            for row in self.languages_table.all_rows()
            if row[0].strip()
        ]
        keywords = [row[0] for row in self.keywords_table.all_rows() if row[0].strip()]
        return ProfileDescription(
            languages=languages,
            keywords=keywords,
            abstract=self.abstract_field.toPlainText(),
            participants=self.participants_field.toPlainText(),
        )
