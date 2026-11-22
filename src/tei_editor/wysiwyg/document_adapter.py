"""Conversion ``Block``/``InlineRun`` ↔ ``QTextDocument`` (ADR-0009).

Chaque bloc/run porte ses métadonnées TEI (``kind``/``level``/``style``/
``lang``) comme propriété personnalisée de ``QTextBlockFormat``/
``QTextCharFormat`` (``QTextFormat.setProperty``) : c'est ce qui permet de
relire un ``QTextDocument`` édité et de reconstruire la liste de blocs
sans dépendre uniquement de l'apparence (gras/couleur), qui elle peut
être partagée par plusieurs balises (ex. ``hi``/``emph``/``foreign``/
``title`` sont tous en italique)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextFormat

from .model import Block, InlineRun, merge_adjacent_runs

TEI_KIND_PROPERTY = QTextFormat.Property.UserProperty + 1
TEI_LEVEL_PROPERTY = QTextFormat.Property.UserProperty + 2
TEI_STYLE_PROPERTY = QTextFormat.Property.UserProperty + 3
TEI_LANG_PROPERTY = QTextFormat.Property.UserProperty + 4
TEI_BULLET_PROPERTY = QTextFormat.Property.UserProperty + 5

_INLINE_COLORS: dict[str, str] = {
    "persName": "#8a3b00",
    "placeName": "#006d5b",
    "orgName": "#4b3f72",
    "name": "#555555",
    "date": "#777777",
}
_ITALIC_STYLES = frozenset({"hi", "emph", "foreign", "title"})


def _char_format_for(style: str | None, lang: str | None, *, base_bold: bool, base_size: float | None) -> QTextCharFormat:
    char_format = QTextCharFormat()
    if base_bold:
        char_format.setFontWeight(QFont.Weight.Bold)
    if base_size is not None:
        char_format.setFontPointSize(base_size)
    if style is not None:
        char_format.setProperty(TEI_STYLE_PROPERTY, style)
        if lang:
            char_format.setProperty(TEI_LANG_PROPERTY, lang)
        if style in _ITALIC_STYLES:
            char_format.setFontItalic(True)
        color = _INLINE_COLORS.get(style)
        if color is not None:
            char_format.setFontUnderline(style != "date")
            char_format.setForeground(QColor(color))
    return char_format


def blocks_to_qtextdocument(blocks: list[Block], document) -> None:
    """Reconstruit intégralement ``document`` à partir de ``blocks``.

    Appelé uniquement au chargement/à la bascule vers le mode WYSIWYG
    (jamais pendant la frappe) : un ``QTextDocument`` entier est reconstruit,
    ce qui est sans risque pour l'undo natif de ``QTextEdit`` puisque
    c'est justement le point où ce document commence une nouvelle vie
    (ADR-0009 : le pivot de blocs, pas le texte XML, est la source de
    vérité pendant l'édition WYSIWYG)."""
    document.clear()
    cursor = QTextCursor(document)
    first = True
    for block in blocks:
        block_format = QTextBlockFormat()
        block_format.setProperty(TEI_KIND_PROPERTY, block.kind)
        block_format.setProperty(TEI_LEVEL_PROPERTY, block.level)
        block_format.setIndent(block.level if block.kind != "item" else max(0, block.level - 1))
        if block.kind == "note":
            block_format.setBackground(QColor("#f3ecd8"))
        if first:
            cursor.setBlockFormat(block_format)
            first = False
        else:
            cursor.insertBlock(block_format)

        base_bold = block.kind == "head"
        base_size = max(10.0, 20.0 - (block.level - 1) * 2) if block.kind == "head" else None
        if block.kind == "item":
            bullet_format = QTextCharFormat()
            bullet_format.setProperty(TEI_BULLET_PROPERTY, True)
            cursor.insertText("• ", bullet_format)
        for run in block.runs:
            char_format = _char_format_for(run.style, run.lang, base_bold=base_bold, base_size=base_size)
            cursor.insertText(run.text, char_format)


def qtextdocument_to_blocks(document) -> list[Block]:
    """Relit ``document`` (tel qu'édité par l'utilisateur) et reconstruit
    la liste de blocs. Contrepartie exacte de :func:`blocks_to_qtextdocument`."""
    blocks: list[Block] = []
    qblock = document.begin()
    while qblock.isValid():
        kind = qblock.blockFormat().property(TEI_KIND_PROPERTY)
        if not kind:
            qblock = qblock.next()
            continue
        level = qblock.blockFormat().property(TEI_LEVEL_PROPERTY)
        level = int(level) if level else 0
        runs: list[InlineRun] = []
        it = qblock.begin()
        while not it.atEnd():
            fragment = it.fragment()
            if fragment.isValid():
                char_format = fragment.charFormat()
                if not char_format.property(TEI_BULLET_PROPERTY):
                    style = char_format.property(TEI_STYLE_PROPERTY) or None
                    lang = char_format.property(TEI_LANG_PROPERTY) or None
                    text = fragment.text()
                    if text:
                        runs.append(InlineRun(text=text, style=style, lang=lang))
            it += 1
        blocks.append(Block(kind=kind, level=level, runs=merge_adjacent_runs(runs)))
        qblock = qblock.next()
    return blocks
