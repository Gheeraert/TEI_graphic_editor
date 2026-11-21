"""Coloration syntaxique XML générique (pas sémantique TEI).

``QSyntaxHighlighter`` à base d'expressions régulières (``QRegularExpression``),
suffisant pour cette phase (``docs/ROADMAP.md`` §5) : balises, noms
d'attributs, valeurs d'attributs, commentaires, instructions de
traitement, texte. Aucune connaissance du catalogue TEI ici — la
palette de balises contextuelle arrive en phase 5/7.
"""

from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)


def _format(color: str, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    fmt.setFontItalic(italic)
    return fmt


class XmlHighlighter(QSyntaxHighlighter):
    """Coloration XML générique appliquée à un ``QTextDocument``."""

    COMMENT_START = "<!--"
    COMMENT_END = "-->"

    def __init__(self, document) -> None:
        super().__init__(document)
        self._tag_format = _format("#8a2be2", bold=True)
        self._attr_name_format = _format("#b58900")
        self._attr_value_format = _format("#2aa198")
        self._pi_format = _format("#657b83", italic=True)
        self._comment_format = _format("#93a1a1", italic=True)
        self._entity_format = _format("#dc322f")

        self._attr_re = QRegularExpression(
            r"""([A-Za-z_:][\w:.\-]*)(\s*=\s*)((?:"[^"]*")|(?:'[^']*'))"""
        )
        self._tag_re = QRegularExpression(r"</?[A-Za-z_][\w:.\-]*")
        self._tag_end_re = QRegularExpression(r"/?>")
        self._pi_re = QRegularExpression(r"<\?.*?\?>")
        self._entity_re = QRegularExpression(r"&[A-Za-z#][A-Za-z0-9]*;")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (nom imposé par Qt)
        self._highlight_tags_and_attributes(text)
        self._highlight_matches(self._pi_re, text, self._pi_format)
        self._highlight_matches(self._entity_re, text, self._entity_format)
        self._highlight_multiline_comments(text)

    def _highlight_matches(self, pattern: QRegularExpression, text: str, fmt: QTextCharFormat) -> None:
        it = pattern.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

    def _highlight_tags_and_attributes(self, text: str) -> None:
        for pattern in (self._tag_re, self._tag_end_re):
            self._highlight_matches(pattern, text, self._tag_format)
        it = self._attr_re.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(1), match.capturedLength(1), self._attr_name_format)
            self.setFormat(match.capturedStart(3), match.capturedLength(3), self._attr_value_format)

    def _highlight_multiline_comments(self, text: str) -> None:
        self.setCurrentBlockState(0)
        start_index = 0 if self.previousBlockState() == 1 else text.find(self.COMMENT_START)

        while start_index >= 0:
            end_index = text.find(self.COMMENT_END, start_index)
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + len(self.COMMENT_END)
            self.setFormat(start_index, comment_length, self._comment_format)
            if end_index == -1:
                break
            start_index = text.find(self.COMMENT_START, start_index + comment_length)
