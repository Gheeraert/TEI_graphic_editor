from __future__ import annotations

from PySide6.QtWidgets import QApplication

from tei_editor.wysiwyg.editor_widget import WysiwygEditor
from tei_editor.wysiwyg.model import Block, InlineRun


def test_load_blocks_then_to_blocks_roundtrips(qapp: QApplication) -> None:
    editor = WysiwygEditor()
    blocks = [
        Block(kind="head", level=1, runs=[InlineRun(text="Titre")]),
        Block(kind="p", level=0, runs=[InlineRun(text="Un paragraphe.")]),
    ]
    editor.load_blocks(blocks)
    assert editor.to_blocks() == blocks


def test_load_blocks_resets_modified_flag(qapp: QApplication) -> None:
    editor = WysiwygEditor()
    editor.load_blocks([Block(kind="p", level=0, runs=[InlineRun(text="x")])])
    assert editor.document().isModified() is False


def test_rich_text_paste_is_disabled(qapp: QApplication) -> None:
    editor = WysiwygEditor()
    assert editor.acceptRichText() is False
