"""Accessibilité : navigation clavier (``docs/ROADMAP.md`` §5, phase 8,
point 7). Vérifie que les contrôles interactifs principaux (éditeur,
panneaux des docks, boutons des barres d'outils) ont un
``focusPolicy()`` différent de ``NoFocus`` — condition nécessaire pour
qu'ils entrent dans la chaîne ``Tab``/``Shift+Tab``."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow


def _make_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    for dock in (window.outline_dock, window.inspector_dock, window.problems_dock, window.palette_dock):
        dock.setVisible(True)
    return window


def test_main_editor_accepts_keyboard_focus(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    assert window.editor.focusPolicy() != Qt.FocusPolicy.NoFocus
    window.close()


def test_dock_panels_accept_keyboard_focus(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    panels = [
        window.outline_panel,
        window.inspector_panel,
        window.problems_panel,
        window.palette_panel,
    ]
    for panel in panels:
        assert panel.focusPolicy() != Qt.FocusPolicy.NoFocus or any(
            child.focusPolicy() != Qt.FocusPolicy.NoFocus for child in panel.findChildren(object)
            if hasattr(child, "focusPolicy")
        ), f"{panel} (et ses enfants) n'acceptent pas le focus clavier"
    window.close()


def test_toolbar_buttons_are_in_the_focus_chain(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    # Qt construit la chaîne de focus par défaut dans l'ordre de création
    # des widgets ; on vérifie ici la condition nécessaire (focusPolicy)
    # plutôt que de simuler des évènements Tab, peu fiable hors écran.
    buttons = window.toolbars.file.findChildren(object)
    # On exclut les widgets internes de Qt sans action associée (ex. le
    # bouton d'extension « >> » ajouté automatiquement quand la barre est
    # trop étroite) : seuls les vrais boutons d'action nous intéressent.
    interactive = [
        b
        for b in buttons
        if hasattr(b, "focusPolicy") and hasattr(b, "defaultAction") and b.defaultAction() is not None
    ]
    assert interactive, "la barre d'outils Fichier doit exposer des QToolButton"
    for button in interactive:
        assert button.focusPolicy() != Qt.FocusPolicy.NoFocus
    window.close()
