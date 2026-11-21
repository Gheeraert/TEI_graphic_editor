"""Point d'entrée de l'assistant d'en-tête TEI (phase 6,
``docs/ROADMAP.md`` §5) : dialogue à onglets qui lit le ``<teiHeader>``
courant (:mod:`tei_editor.tei.header_reader`), le présente dans 7
onglets, et n'écrit que les sous-éléments modifiés à l'« Appliquer »
(:mod:`tei_editor.tei.header_writer`).

Toutes les modifications d'un « Appliquer » forment un seul pas
d'annulation natif (:func:`tei_editor.editor.structured_edits.apply_edits_with_cursor`,
même mécanisme que la phase 5, ADR-0008), exactement comme
``editor/tag_commands_mixin.py`` applique ses propres plans d'édition.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QTabWidget, QVBoxLayout, QWidget

from tei_editor.editor.structured_edits import apply_edits_with_cursor
from tei_editor.header_dialog.tab_edition_source import EditionTab, SourceTab
from tei_editor.header_dialog.tab_encoding_profile import EncodingTab, ProfileTab
from tei_editor.header_dialog.tab_publication import PublicationTab
from tei_editor.header_dialog.tab_revisions import RevisionsTab
from tei_editor.header_dialog.tab_title import TitleResponsibilityTab
from tei_editor.tei.header_model import TeiHeaderData
from tei_editor.tei.header_reader import HeaderReadResult, read_header
from tei_editor.tei.header_writer import plan_header_edits


class HeaderWizardDialog(QDialog):
    """``editor`` : l'``XmlTextEditor`` de la fenêtre principale (texte
    source de vérité, ADR-0001). Le dialogue ne modifie jamais le texte
    hors d'un « Appliquer » explicite."""

    def __init__(self, editor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Assistant d'en-tête TEI")
        self.resize(760, 640)

        self.read_result: HeaderReadResult = read_header(editor.toPlainText())
        data = self.read_result.data

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        self.title_tab = TitleResponsibilityTab(self)
        self.title_tab.load(data.titles, data.responsible_parties)
        self.tabs.addTab(self.title_tab, "Titre et responsabilités")

        self.edition_tab = EditionTab(self)
        self.edition_tab.load(data.edition, data.extent)
        self.tabs.addTab(self.edition_tab, "Édition")

        self.publication_tab = PublicationTab(self)
        self.publication_tab.load(data.publication)
        self.tabs.addTab(self.publication_tab, "Publication")

        self.source_tab = SourceTab(self)
        self.source_tab.load(data.source)
        self.tabs.addTab(self.source_tab, "Source")

        self.encoding_tab = EncodingTab(self)
        self.encoding_tab.load(data.encoding)
        self.tabs.addTab(self.encoding_tab, "Encodage")

        self.profile_tab = ProfileTab(self)
        self.profile_tab.load(data.profile)
        self.tabs.addTab(self.profile_tab, "Profil")

        self.revisions_tab = RevisionsTab(self)
        self.revisions_tab.load(data.revisions)
        self.tabs.addTab(self.revisions_tab, "Révisions")

        if not self.read_result.header_exists or not self.read_result.file_desc_exists:
            QMessageBox.warning(
                self,
                "Assistant d'en-tête",
                "Ce document n'a pas de <teiHeader>/<fileDesc> complet : "
                "l'assistant affiche ce qu'il peut, mais ne pourra pas "
                "écrire les sous-éléments dont l'emplacement n'a pas été "
                "trouvé (limitation assumée, voir docs/DECISIONS.md).",
            )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("&Appliquer")
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -- Collecte -------------------------------------------------------------
    def collect(self) -> TeiHeaderData:
        edited = TeiHeaderData()
        edited.titles, edited.responsible_parties = self.title_tab.collect()
        edited.edition, edited.extent = self.edition_tab.collect()
        edited.publication = self.publication_tab.collect()
        edited.source = self.source_tab.collect()
        edited.encoding = self.encoding_tab.collect()
        edited.profile = self.profile_tab.collect()
        edited.revisions = self.revisions_tab.collect()
        return edited

    # -- Application ------------------------------------------------------------
    def _apply(self) -> None:
        edited = self.collect()
        edits = plan_header_edits(self.read_result, edited)
        if edits:
            cursor = self.editor.textCursor()
            apply_edits_with_cursor(cursor, edits)
            self.editor.setTextCursor(cursor)
        self.accept()
