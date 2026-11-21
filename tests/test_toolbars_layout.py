"""Cycle complet sauvegarde/restauration de la disposition
(``docs/ROADMAP.md`` §5, phase 8, point 5) : vérifie que
``saveState()``/``restoreState()`` (déjà présent depuis la phase 3,
``docs/DECISIONS.md`` ADR-0006) couvre bien les nouvelles barres
d'outils en plus des docks existants — chaque ``QToolBar``/``QDockWidget``
doit avoir un ``objectName`` pour que Qt les retrouve à la restauration
(piège classique sinon silencieux)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow


def test_every_toolbar_and_dock_has_an_object_name(qapp: QApplication, tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    toolbars = [window.toolbars.file, window.toolbars.edit, window.toolbars.tags, window.toolbars.view]
    docks = [window.outline_dock, window.inspector_dock, window.problems_dock, window.palette_dock]
    for widget in toolbars + docks:
        assert widget.objectName(), f"{widget} doit avoir un objectName explicite"
    window.close()


def test_toolbar_and_dock_visibility_round_trip(qapp: QApplication, tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.ini"
    recovery_dir = tmp_path / "recovery"

    settings1 = QSettings(str(settings_path), QSettings.Format.IniFormat)
    window1 = MainWindow(settings=settings1, recovery_dir=recovery_dir)
    # ``isVisible()`` ne reflète la visibilité réelle que si la fenêtre
    # elle-même est affichée (sinon tout widget enfant reste invisible,
    # quel que soit son indicateur « doit être visible »).
    window1.show()
    qapp.processEvents()
    window1.toolbars.tags.setVisible(False)
    window1.outline_dock.setVisible(True)
    qapp.processEvents()
    window1.close()
    settings1.sync()

    settings2 = QSettings(str(settings_path), QSettings.Format.IniFormat)
    window2 = MainWindow(settings=settings2, recovery_dir=recovery_dir)
    window2.show()
    qapp.processEvents()
    assert window2.toolbars.tags.isVisible() is False
    assert window2.outline_dock.isVisible() is True
    window2.close()
