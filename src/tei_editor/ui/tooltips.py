"""Infobulles explicites avec raccourci (``docs/ROADMAP.md`` §5, phase 8,
point 4) : le tooltip effectif d'une action affiche son texte **et** son
raccourci (ex. « Enregistrer (Ctrl+S) »), posé explicitement plutôt que
de compter sur le comportement par défaut de Qt (variable selon la
plateforme/le style)."""

from __future__ import annotations

from PySide6.QtGui import QAction

from tei_editor.actions import Actions
from tei_editor.ui.action_registry import flatten_actions


def display_text(action: QAction) -> str:
    """Texte de l'action sans l'accélérateur de mnémonique (``&``)."""
    return action.text().replace("&", "")


def tooltip_with_shortcut(action: QAction) -> str:
    text = display_text(action)
    shortcut = action.shortcut()
    if shortcut.isEmpty():
        return text
    return f"{text} ({shortcut.toString()})"


def apply_tooltip_with_shortcut(action: QAction) -> None:
    action.setToolTip(tooltip_with_shortcut(action))


def apply_tooltips_with_shortcuts(actions: Actions) -> None:
    for action in flatten_actions(actions).values():
        apply_tooltip_with_shortcut(action)
