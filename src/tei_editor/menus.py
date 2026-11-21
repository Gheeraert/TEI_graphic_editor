"""Construction des menus à partir des ``QAction`` de :mod:`tei_editor.actions`.

Renvoie les références de menus que ``main_window.py`` doit garder sous
la main pour les mettre à jour dynamiquement (menu « Fichiers récents »,
reconstruit à chaque ouverture/fermeture).
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QMenu, QMenuBar

from tei_editor.actions import Actions


@dataclass
class Menus:
    recent_files_menu: QMenu


def build_menu_bar(menu_bar: QMenuBar, actions: Actions) -> Menus:
    menu_bar.clear()

    file_menu = menu_bar.addMenu("&Fichier")
    file_menu.addAction(actions.new)
    file_menu.addAction(actions.open)
    recent_files_menu = file_menu.addMenu("Fichiers &récents")
    recent_files_menu.setEnabled(False)
    file_menu.addSeparator()
    file_menu.addAction(actions.save)
    file_menu.addAction(actions.save_as)
    file_menu.addAction(actions.export)
    file_menu.addSeparator()
    file_menu.addAction(actions.quit)

    edit_menu = menu_bar.addMenu("&Édition")
    edit_menu.addAction(actions.undo)
    edit_menu.addAction(actions.redo)
    edit_menu.addSeparator()
    edit_menu.addAction(actions.cut)
    edit_menu.addAction(actions.copy)
    edit_menu.addAction(actions.paste)
    edit_menu.addSeparator()
    edit_menu.addAction(actions.find_replace)
    edit_menu.addAction(actions.goto_line)

    insertion_menu = menu_bar.addMenu("&Insertion")
    insertion_menu.addAction(actions.insertion_unavailable)

    tags_menu = menu_bar.addMenu("&Balises")
    tags_menu.addAction(actions.tags.wrap_selection)
    tags_menu.addAction(actions.tags.unwrap)
    tags_menu.addAction(actions.tags.rename)
    tags_menu.addSeparator()
    tags_menu.addAction(actions.tags.split_paragraph)
    tags_menu.addAction(actions.tags.merge_paragraph)
    tags_menu.addSeparator()
    tags_menu.addAction(actions.tags.generate_xml_id)

    view_menu = menu_bar.addMenu("&Affichage")
    view_menu.addAction(actions.docks.outline)
    view_menu.addAction(actions.docks.inspector)
    view_menu.addAction(actions.docks.problems)
    view_menu.addAction(actions.docks.palette)
    view_menu.addSeparator()
    zoom_menu = view_menu.addMenu("&Zoom")
    zoom_menu.addAction(actions.zoom_in)
    zoom_menu.addAction(actions.zoom_out)
    zoom_menu.addAction(actions.zoom_reset)
    theme_menu = view_menu.addMenu("&Thème")
    for theme_action in actions.themes.by_name.values():
        theme_menu.addAction(theme_action)

    tools_menu = menu_bar.addMenu("&Outils")
    tools_menu.addAction(actions.validate)
    profile_menu = tools_menu.addMenu("Pro&fil actif")
    for profile_action in actions.profiles.by_id.values():
        profile_menu.addAction(profile_action)
    tools_menu.addSeparator()
    tools_menu.addAction(actions.preferences)

    help_menu = menu_bar.addMenu("&Aide")
    help_menu.addAction(actions.about)

    return Menus(recent_files_menu=recent_files_menu)


def rebuild_recent_files_menu(menu: QMenu, paths: list[str], *, on_choose) -> None:
    """Reconstruit le contenu du menu « Fichiers récents » depuis ``paths``.

    ``on_choose`` est appelé avec le chemin choisi quand une entrée est
    cliquée. Le menu est désactivé quand ``paths`` est vide.
    """
    menu.clear()
    menu.setEnabled(bool(paths))
    for path in paths:
        action = menu.addAction(path)
        action.triggered.connect(lambda checked=False, chosen=path: on_choose(chosen))
