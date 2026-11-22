"""Test Qt bout en bout (hors écran) de la bascule Texte XML <-> WYSIWYG
(phase 10, ADR-0012), branchée via ``MainWindow``."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from tei_editor.main_window import MainWindow

NS = "http://www.tei-c.org/ns/1.0"
SIMPLE_DOCUMENT = (
    f'<TEI xmlns="{NS}">'
    "<teiHeader><fileDesc><titleStmt><title>T</title></titleStmt>"
    "<publicationStmt><p>P</p></publicationStmt>"
    "<sourceDesc><p>S</p></sourceDesc></fileDesc></teiHeader>"
    "<text><body><div><head>Titre</head>"
    "<p>Un paragraphe avec <hi>une mise en valeur</hi>.</p></div></body></text>"
    "</TEI>"
)


def _make_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    window.editor.setPlainText(SIMPLE_DOCUMENT)
    window._update_structural_info()
    return window


def test_toggle_to_wysiwyg_hides_body_tags_then_back_roundtrips(
    qapp: QApplication, tmp_path: Path
) -> None:
    window = _make_window(qapp, tmp_path)
    header_prefix = SIMPLE_DOCUMENT.split("<text>")[0]

    window.actions.wysiwyg.toggle.setChecked(True)
    assert window._view_stack.currentWidget() is window.wysiwyg_editor

    window.actions.wysiwyg.toggle.setChecked(False)
    assert window._view_stack.currentWidget() is window.editor
    new_text = window.editor.toPlainText()
    assert new_text.startswith(header_prefix)
    assert "<div><head>Titre</head><p>Un paragraphe avec <hi>une mise en valeur</hi>.</p></div>" in new_text
    window.close()


def test_toggle_refused_on_malformed_document(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    window = _make_window(qapp, tmp_path)
    window.editor.setPlainText("<TEI><text><body><p>mal formé</body></text></TEI>")

    window.actions.wysiwyg.toggle.setChecked(True)

    assert window._view_stack.currentWidget() is window.editor
    assert window.actions.wysiwyg.toggle.isChecked() is False
    window.close()


def test_toggle_refused_without_body(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    window = _make_window(qapp, tmp_path)
    window.editor.setPlainText(f'<TEI xmlns="{NS}"><teiHeader/><text><front/></text></TEI>')

    window.actions.wysiwyg.toggle.setChecked(True)

    assert window._view_stack.currentWidget() is window.editor
    assert window.actions.wysiwyg.toggle.isChecked() is False
    window.close()


def test_save_commits_wysiwyg_edits_to_xml(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    window.actions.wysiwyg.toggle.setChecked(True)

    target = tmp_path / "out.xml"
    window._save_to_path(target)

    saved = target.read_text(encoding="utf-8")
    assert "<body>" in saved and "</body>" in saved
    assert "Un paragraphe avec" in saved
    window.close()
