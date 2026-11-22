"""``WysiwygEditor`` : la surface d'édition WYSIWYG elle-même (ADR-0009).

Un simple ``QTextEdit`` : toute la logique de conversion vit dans
``document_adapter.py``/``xml_adapter.py`` (purs, testables indépendamment
de ce widget), conformément à la convention du projet « une fonctionnalité
= un module testable sans interface graphique + une fine couche Qt »
(``CLAUDE.md``)."""

from __future__ import annotations

from PySide6.QtWidgets import QTextEdit

from .document_adapter import blocks_to_qtextdocument, qtextdocument_to_blocks
from .model import Block


class WysiwygEditor(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Empêche un collage de texte riche étranger (ex. depuis un
        # navigateur) d'introduire une mise en forme Qt sans métadonnée
        # TEI associée : elle serait silencieusement perdue à la
        # resérialisation, pire que la politique de simplification
        # assumée pour le XML existant (ADR-0009).
        self.setAcceptRichText(False)

    def load_blocks(self, blocks: list[Block]) -> None:
        blocks_to_qtextdocument(blocks, self.document())
        self.document().setModified(False)

    def to_blocks(self) -> list[Block]:
        return qtextdocument_to_blocks(self.document())
