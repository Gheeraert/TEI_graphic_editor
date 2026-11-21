"""Tests Qt (hors écran) du soulignement des diagnostics dans l'éditeur."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QPlainTextEdit

from tei_editor.editor.diagnostics import SEVERITY_ERROR, SEVERITY_WARNING, Diagnostic
from tei_editor.editor.diagnostics_overlay import apply_diagnostic_highlights


def test_apply_diagnostic_highlights_une_selection_par_diagnostic(qapp: QApplication) -> None:
    editor = QPlainTextEdit()
    editor.setPlainText("ligne 1\nligne 2\nligne 3\n")
    diagnostics = [
        Diagnostic(SEVERITY_ERROR, 2, 1, "erreur"),
        Diagnostic(SEVERITY_WARNING, 3, None, "avertissement"),
    ]
    apply_diagnostic_highlights(editor, diagnostics)
    assert len(editor.extraSelections()) == 2


def test_apply_diagnostic_highlights_vide_la_liste_sans_diagnostic(qapp: QApplication) -> None:
    editor = QPlainTextEdit()
    editor.setPlainText("ligne 1\n")
    apply_diagnostic_highlights(editor, [Diagnostic(SEVERITY_ERROR, 1, 1, "x")])
    apply_diagnostic_highlights(editor, [])
    assert editor.extraSelections() == []


def test_apply_diagnostic_highlights_ignore_une_ligne_hors_limites(qapp: QApplication) -> None:
    editor = QPlainTextEdit()
    editor.setPlainText("une seule ligne\n")
    apply_diagnostic_highlights(editor, [Diagnostic(SEVERITY_ERROR, 999, None, "x")])
    assert editor.extraSelections() == []
