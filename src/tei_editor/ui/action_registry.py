"""Aplatit les ``QAction`` de :class:`tei_editor.actions.Actions` en un
dictionnaire ``{nom_logique: QAction}``.

Les clefs correspondent exactement à celles de
``data/icons/action_icons.json`` : un seul point de correspondance entre
une action et son « nom logique », réutilisé à la fois pour les icônes
(``tei_editor.ui.icons``) et pour les infobulles
(``tei_editor.ui.tooltips``), au lieu de dupliquer la liste des actions
dans chaque module (``CLAUDE.md`` : pas de liste codée en dur répétée)."""

from __future__ import annotations

from PySide6.QtGui import QAction

from tei_editor.actions import Actions


def flatten_actions(actions: Actions) -> dict[str, QAction]:
    flat: dict[str, QAction] = {
        "new": actions.new,
        "open_": actions.open,
        "save": actions.save,
        "save_as": actions.save_as,
        "export": actions.export,
        "quit_": actions.quit,
        "undo": actions.undo,
        "redo": actions.redo,
        "cut": actions.cut,
        "copy": actions.copy,
        "paste": actions.paste,
        "find_replace": actions.find_replace,
        "goto_line": actions.goto_line,
        "tags.wrap_selection": actions.tags.wrap_selection,
        "tags.unwrap": actions.tags.unwrap,
        "tags.rename": actions.tags.rename,
        "tags.split_paragraph": actions.tags.split_paragraph,
        "tags.merge_paragraph": actions.tags.merge_paragraph,
        "tags.generate_xml_id": actions.tags.generate_xml_id,
        "snippets.group_as_choice": actions.snippets.group_as_choice,
        "snippets.insert_cast_list": actions.snippets.insert_cast_list,
        "snippets.mark_shared_verse": actions.snippets.mark_shared_verse,
        "snippets.insert_apparatus": actions.snippets.insert_apparatus,
        "docks.outline": actions.docks.outline,
        "docks.inspector": actions.docks.inspector,
        "docks.problems": actions.docks.problems,
        "docks.palette": actions.docks.palette,
        "zoom_in": actions.zoom_in,
        "zoom_out": actions.zoom_out,
        "zoom_reset": actions.zoom_reset,
        "validate": actions.validate,
        "header_wizard": actions.header_wizard,
        "preferences": actions.preferences,
        "about": actions.about,
    }
    for theme_id, theme_action in actions.themes.by_name.items():
        flat[f"themes.{theme_id}"] = theme_action
    return flat
