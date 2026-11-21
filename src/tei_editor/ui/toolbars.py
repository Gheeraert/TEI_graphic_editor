"""Barres d'outils (``docs/ROADMAP.md`` §5, phase 8) : regroupement
logique des actions les plus fréquentes, construites à partir des
``QAction`` centralisées (``tei_editor.actions``) — même principe que
``menus.py`` pour la barre de menus, séparé de ``main_window.py`` pour
rester sous la limite indicative de ``CLAUDE.md`` (~600 lignes).

Chaque ``QToolBar`` reçoit un ``objectName`` explicite : sans lui,
``QMainWindow.saveState()``/``restoreState()`` ne restaure pas
silencieusement sa position/visibilité (piège Qt classique). Chaque
barre reçoit aussi un nom accessible en français
(``setAccessibleName``), pour l'accessibilité (point 7 de la phase)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QToolBar

from tei_editor.actions import Actions


@dataclass
class Toolbars:
    file: QToolBar
    edit: QToolBar
    tags: QToolBar
    view: QToolBar


def _enable_keyboard_focus(toolbar: QToolBar) -> None:
    """Les ``QToolButton`` n'acceptent pas le focus clavier par défaut
    dans Qt (``Qt.FocusPolicy.NoFocus``) : on l'active explicitement
    pour qu'ils entrent dans la chaîne ``Tab``/``Shift+Tab``
    (accessibilité, ``docs/ROADMAP.md`` §5 phase 8, point 7)."""
    for action in toolbar.actions():
        widget = toolbar.widgetForAction(action)
        if widget is not None:
            widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)


def build_toolbars(window: QMainWindow, actions: Actions) -> Toolbars:
    file_toolbar = QToolBar("Fichier", window)
    file_toolbar.setObjectName("toolbar_fichier")
    file_toolbar.setAccessibleName("Barre d'outils Fichier")
    file_toolbar.addAction(actions.new)
    file_toolbar.addAction(actions.open)
    file_toolbar.addAction(actions.save)
    file_toolbar.addAction(actions.save_as)
    window.addToolBar(file_toolbar)

    edit_toolbar = QToolBar("Édition", window)
    edit_toolbar.setObjectName("toolbar_edition")
    edit_toolbar.setAccessibleName("Barre d'outils Édition")
    edit_toolbar.addAction(actions.undo)
    edit_toolbar.addAction(actions.redo)
    edit_toolbar.addSeparator()
    edit_toolbar.addAction(actions.cut)
    edit_toolbar.addAction(actions.copy)
    edit_toolbar.addAction(actions.paste)
    edit_toolbar.addSeparator()
    edit_toolbar.addAction(actions.find_replace)
    window.addToolBar(edit_toolbar)

    tags_toolbar = QToolBar("Balises", window)
    tags_toolbar.setObjectName("toolbar_balises")
    tags_toolbar.setAccessibleName("Barre d'outils Balises")
    tags_toolbar.addAction(actions.tags.wrap_selection)
    tags_toolbar.addAction(actions.tags.unwrap)
    tags_toolbar.addAction(actions.tags.rename)
    tags_toolbar.addSeparator()
    tags_toolbar.addAction(actions.tags.generate_xml_id)
    window.addToolBar(tags_toolbar)

    view_toolbar = QToolBar("Affichage", window)
    view_toolbar.setObjectName("toolbar_affichage")
    view_toolbar.setAccessibleName("Barre d'outils Affichage")
    view_toolbar.addAction(actions.docks.outline)
    view_toolbar.addAction(actions.docks.inspector)
    view_toolbar.addAction(actions.docks.problems)
    view_toolbar.addAction(actions.docks.palette)
    view_toolbar.addSeparator()
    view_toolbar.addAction(actions.zoom_in)
    view_toolbar.addAction(actions.zoom_out)
    view_toolbar.addAction(actions.zoom_reset)
    window.addToolBar(view_toolbar)

    for toolbar in (file_toolbar, edit_toolbar, tags_toolbar, view_toolbar):
        _enable_keyboard_focus(toolbar)

    return Toolbars(file=file_toolbar, edit=edit_toolbar, tags=tags_toolbar, view=view_toolbar)
