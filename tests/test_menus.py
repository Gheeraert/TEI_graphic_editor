"""Vérifie par introspection Qt (``menuBar().actions()``) que tous les
menus décrits par la phase 3 existent, avec les actions attendues
(``docs/ROADMAP.md`` §5)."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow


def _make_window(tmp_path, qapp: QApplication) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")


def _menu_titles(window: MainWindow) -> list[str]:
    return [action.text().replace("&", "") for action in window.menuBar().actions()]


def test_top_level_menus_exist(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    assert _menu_titles(window) == [
        "Fichier",
        "Édition",
        "Insertion",
        "Balises",
        "Affichage",
        "Outils",
        "Aide",
    ]
    window.close()


def test_file_menu_has_expected_actions(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    file_menu = window.menuBar().actions()[0].menu()
    labels = [action.text().replace("&", "") for action in file_menu.actions() if not action.isSeparator()]
    assert labels == [
        "Nouveau",
        "Ouvrir...",
        "Fichiers récents",
        "Enregistrer",
        "Enregistrer sous...",
        "Exporter une copie...",
        "Quitter",
    ]
    window.close()


def test_edit_menu_has_expected_actions(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    edit_menu = window.menuBar().actions()[1].menu()
    labels = [action.text().replace("&", "") for action in edit_menu.actions() if not action.isSeparator()]
    assert labels == [
        "Annuler",
        "Rétablir",
        "Couper",
        "Copier",
        "Coller",
        "Rechercher/remplacer...",
        "Aller à la ligne...",
    ]
    window.close()


def test_insertion_menu_points_to_palette_dock(qapp: QApplication, tmp_path) -> None:
    # Phase 5 : la palette de balises est un dock dédié (Affichage >
    # Palette), pas un menu "Insertion" rempli d'actions individuelles.
    window = _make_window(tmp_path, qapp)
    insertion_menu = window.menuBar().actions()[2].menu()
    assert len(insertion_menu.actions()) == 1
    assert not insertion_menu.actions()[0].isEnabled()
    window.close()


def test_tags_menu_has_phase5_commands(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    tags_menu = window.menuBar().actions()[3].menu()
    labels = [action.text().replace("&", "") for action in tags_menu.actions() if not action.isSeparator()]
    assert labels == [
        "Envelopper la sélection...",
        "Dégrouper la balise",
        "Renommer la balise...",
        "Scinder le paragraphe",
        "Fusionner avec le paragraphe suivant",
        "Générer un xml:id",
    ]
    window.close()


def test_view_menu_has_docks_zoom_and_theme(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    view_menu = window.menuBar().actions()[4].menu()
    direct_actions = [
        action.text().replace("&", "") for action in view_menu.actions() if not action.isSeparator()
    ]
    assert "Plan" in direct_actions
    assert "Inspecteur" in direct_actions
    assert "Problèmes" in direct_actions
    assert "Palette" in direct_actions
    submenu_titles = [action.text().replace("&", "") for action in view_menu.actions() if action.menu()]
    assert "Zoom" in submenu_titles
    assert "Thème" in submenu_titles
    window.close()


def test_tools_menu_has_validate_profile_and_preferences(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    tools_menu = window.menuBar().actions()[5].menu()
    labels = [action.text().replace("&", "") for action in tools_menu.actions() if not action.isSeparator()]
    assert "Valider" in labels
    assert "Préférences..." in labels
    profile_submenu = next(
        action.menu() for action in tools_menu.actions() if action.menu() is not None
    )
    profile_labels = [action.text() for action in profile_submenu.actions()]
    assert "TEI (complet)" in profile_labels or any("TEI" in label for label in profile_labels)
    window.close()


def test_help_menu_has_about(qapp: QApplication, tmp_path) -> None:
    window = _make_window(tmp_path, qapp)
    help_menu = window.menuBar().actions()[6].menu()
    labels = [action.text().replace("&", "") for action in help_menu.actions()]
    assert "À propos de TIGRE" in labels
    window.close()
