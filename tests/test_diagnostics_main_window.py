"""Tests Qt bout en bout (hors écran) : validation enrichie et docks
Plan/Problèmes branchés sur le re-parsing différé de `MainWindow`."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "tei-samples"


def _make_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")


def test_document_valide_ne_produit_aucun_diagnostic_derreur(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    window.editor.load_file(FIXTURES_DIR / "01-structure" / "01-minimal.xml")
    window._update_structural_info()
    assert window._last_diagnostics == []
    assert window.problems_panel.count() == 1  # message "aucun problème"
    window.close()


def test_document_hors_modele_peuple_le_panneau_problemes(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    window.editor.load_file(FIXTURES_DIR / "99-invalides" / "04-hors-modele.xml")
    window._update_structural_info()
    assert len(window._last_diagnostics) >= 2
    assert window.problems_panel.count() == len(window._last_diagnostics)
    window.close()


def test_plan_structurel_peuple_apres_ouverture_dun_document_valide(
    qapp: QApplication, tmp_path: Path
) -> None:
    window = _make_window(qapp, tmp_path)
    window.editor.load_file(FIXTURES_DIR / "01-structure" / "01-minimal.xml")
    window._update_structural_info()
    assert window.outline_panel.topLevelItemCount() == 1
    window.close()


def test_plan_reste_vide_pour_un_document_mal_forme(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    window.editor.setPlainText("<TEI><teiHeader></TEI>")
    window._update_structural_info()
    assert window.outline_panel.topLevelItemCount() == 0
    window.close()
