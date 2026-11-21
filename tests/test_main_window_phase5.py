"""Tests Qt bout en bout (hors écran) des commandes de la phase 5,
branchées via `MainWindow` : palette, menu Balises, inspecteur — vérifie
le câblage réel, pas seulement les modules isolés."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow


def _make_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    window.editor.setPlainText(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<text><body><p>Bonjour le monde</p><p>Suite.</p></body></text>"
        "</TEI>"
    )
    window._update_structural_info()
    return window


def _select(window: MainWindow, needle: str) -> None:
    text = window.editor.toPlainText()
    start = text.index(needle)
    cursor = window.editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + len(needle), QTextCursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)


def test_palette_insertion_sans_selection(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    cursor = window.editor.textCursor()
    cursor.setPosition(window.editor.toPlainText().index("Bonjour"))
    window.editor.setTextCursor(cursor)
    before_text = window.editor.toPlainText()
    window._on_palette_element_chosen("hi")
    assert "<hi></hi>Bonjour" in window.editor.toPlainText()
    window.editor.undo()
    assert window.editor.toPlainText() == before_text
    window.close()


def test_palette_enveloppe_la_selection(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    _select(window, "le monde")
    before_text = window.editor.toPlainText()
    window._on_palette_element_chosen("hi")
    assert "<hi>le monde</hi>" in window.editor.toPlainText()
    window.editor.undo()
    assert window.editor.toPlainText() == before_text
    window.close()


def test_menu_degrouper_desactive_sans_element_courant(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    window.editor.setPlainText("<lb/>")
    cursor = window.editor.textCursor()
    cursor.setPosition(0)
    window.editor.setTextCursor(cursor)
    window._update_structural_info()
    # Aucun élément non auto-fermant n'est jamais ouvert dans ce
    # document : pas d'élément courant, l'action doit rester désactivée.
    assert not window.actions.tags.unwrap.isEnabled()
    window.close()


def test_menu_degrouper_un_p(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    cursor = window.editor.textCursor()
    cursor.setPosition(window.editor.toPlainText().index("Bonjour"))
    window.editor.setTextCursor(cursor)
    window._update_structural_info()
    assert window.actions.tags.unwrap.isEnabled()
    before_text = window.editor.toPlainText()
    window._unwrap_current_element()
    assert "<p>" not in window.editor.toPlainText().split("Bonjour")[0][-5:]
    assert "Bonjour le monde" in window.editor.toPlainText()
    window.editor.undo()
    assert window.editor.toPlainText() == before_text
    window.close()


def test_generer_xml_id_depuis_le_menu(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    cursor = window.editor.textCursor()
    cursor.setPosition(window.editor.toPlainText().index("Bonjour"))
    window.editor.setTextCursor(cursor)
    window._update_structural_info()
    before_text = window.editor.toPlainText()
    window._on_generate_xml_id()
    assert 'xml:id="p-1"' in window.editor.toPlainText()
    window.editor.undo()
    assert window.editor.toPlainText() == before_text
    window.close()


def test_fusionner_les_deux_paragraphes(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    cursor = window.editor.textCursor()
    cursor.setPosition(window.editor.toPlainText().index("Bonjour"))
    window.editor.setTextCursor(cursor)
    window._update_structural_info()
    assert window.actions.tags.merge_paragraph.isEnabled()
    before_text = window.editor.toPlainText()
    window._merge_paragraph()
    assert "Bonjour le mondeSuite." in window.editor.toPlainText()
    window.editor.undo()
    assert window.editor.toPlainText() == before_text
    window.close()
