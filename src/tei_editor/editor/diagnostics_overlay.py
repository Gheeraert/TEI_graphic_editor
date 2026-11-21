"""Soulignement des diagnostics dans l'éditeur (phase 4).

Choix Qt : ``QPlainTextEdit.setExtraSelections`` plutôt qu'une
intégration dans ``XmlHighlighter`` (``QSyntaxHighlighter``). Les
diagnostics changent à chaque re-parsing différé (toutes les 400 ms au
plus, voir ``main_window._update_structural_info``), sur des plages qui
ne correspondent à aucune règle lexicale stable : les recalculer comme
des ``ExtraSelection`` est une simple liste remplacée en bloc, sans
déclencher de nouvelle passe de coloration syntaxique sur tout le
document (ce que ferait rehighlight() sur un ``QSyntaxHighlighter``).
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit

from tei_editor.editor.diagnostics import SEVERITY_ERROR, Diagnostic

_ERROR_COLOR = QColor("#c0392b")
_WARNING_COLOR = QColor("#b58900")


def _format_for(severity: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
    fmt.setUnderlineColor(_ERROR_COLOR if severity == SEVERITY_ERROR else _WARNING_COLOR)
    return fmt


def apply_diagnostic_highlights(editor: QPlainTextEdit, diagnostics: list[Diagnostic]) -> None:
    """Remplace les ``ExtraSelection`` de ``editor`` par une sélection
    ondulée par diagnostic, sur toute la ligne concernée (lxml/libxml2 ne
    donnant pas systématiquement de portée de colonne à colonne)."""
    document = editor.document()
    selections = []
    for diagnostic in diagnostics:
        block = document.findBlockByNumber(max(0, diagnostic.line - 1))
        if not block.isValid():
            continue
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.format = _format_for(diagnostic.severity)
        selections.append(selection)
    editor.setExtraSelections(selections)
