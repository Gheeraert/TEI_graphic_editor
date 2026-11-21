"""Tests Qt (hors écran) du panneau « Problèmes »."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from tei_editor.editor.diagnostics import SEVERITY_ERROR, SEVERITY_WARNING, Diagnostic
from tei_editor.editor.problems_panel import ProblemsPanel


def test_problems_panel_affiche_un_message_quand_aucun_diagnostic(qapp: QApplication) -> None:
    panel = ProblemsPanel()
    panel.set_diagnostics([])
    assert panel.count() == 1
    assert "Aucun probl" in panel.item(0).text()


def test_problems_panel_affiche_une_ligne_par_diagnostic(qapp: QApplication) -> None:
    panel = ProblemsPanel()
    diagnostics = [
        Diagnostic(SEVERITY_ERROR, 5, 12, "Un message d'erreur."),
        Diagnostic(SEVERITY_WARNING, 8, None, "Un avertissement hors profil."),
    ]
    panel.set_diagnostics(diagnostics)
    assert panel.count() == 2
    assert "5:12" in panel.item(0).text()
    assert "8" in panel.item(1).text()


def test_problems_panel_clic_emet_jump_requested(qapp: QApplication) -> None:
    panel = ProblemsPanel()
    diagnostics = [Diagnostic(SEVERITY_ERROR, 3, 7, "Erreur.")]
    panel.set_diagnostics(diagnostics)
    received = []
    panel.jump_requested.connect(lambda line, column: received.append((line, column)))
    panel._on_item_activated(panel.item(0))
    assert received == [(3, 7)]
