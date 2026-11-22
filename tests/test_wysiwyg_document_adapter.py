"""Tests Qt hors écran (``QT_QPA_PLATFORM=offscreen``, ``tests/conftest.py``)
du convertisseur Blocs <-> ``QTextDocument`` (ADR-0012)."""

from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from tei_editor.wysiwyg.document_adapter import blocks_to_qtextdocument, qtextdocument_to_blocks
from tei_editor.wysiwyg.model import Block, InlineRun


def test_roundtrip_simple_paragraph(qapp: QApplication) -> None:
    blocks = [Block(kind="p", level=0, runs=[InlineRun(text="Bonjour le monde", style=None)])]
    document = QTextDocument()
    blocks_to_qtextdocument(blocks, document)
    result = qtextdocument_to_blocks(document)
    assert result == blocks


def test_roundtrip_mixed_styles_and_heading_level(qapp: QApplication) -> None:
    blocks = [
        Block(kind="head", level=2, runs=[InlineRun(text="Titre")]),
        Block(
            kind="p",
            level=1,
            runs=[
                InlineRun(text="Du texte "),
                InlineRun(text="important", style="hi"),
                InlineRun(text=" et "),
                InlineRun(text="Jean Dupont", style="persName"),
                InlineRun(text="."),
            ],
        ),
    ]
    document = QTextDocument()
    blocks_to_qtextdocument(blocks, document)
    result = qtextdocument_to_blocks(document)
    assert result == blocks


def test_foreign_lang_roundtrips(qapp: QApplication) -> None:
    blocks = [Block(kind="p", level=0, runs=[InlineRun(text="mixte", style="foreign", lang="la")])]
    document = QTextDocument()
    blocks_to_qtextdocument(blocks, document)
    result = qtextdocument_to_blocks(document)
    assert result == blocks


def test_item_bullet_marker_is_not_leaked_into_runs(qapp: QApplication) -> None:
    blocks = [Block(kind="item", level=1, runs=[InlineRun(text="Un point")])]
    document = QTextDocument()
    blocks_to_qtextdocument(blocks, document)
    result = qtextdocument_to_blocks(document)
    assert result == blocks
    assert "•" not in result[0].runs[0].text
