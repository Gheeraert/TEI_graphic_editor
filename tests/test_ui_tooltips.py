"""Vérifie que les infobulles affichent le texte de l'action et son
raccourci (``docs/ROADMAP.md`` §5, phase 8, point 4)."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from tei_editor.actions import build_actions
from tei_editor.ui.tooltips import apply_tooltips_with_shortcuts


def _actions(qapp):
    # ``parent`` doit rester référencé par l'appelant : si le QWidget
    # Python est détruit par le GC, Qt détruit aussi les QAction qui lui
    # appartiennent, et toute opération ultérieure lève un RuntimeError
    # « objet C++ déjà supprimé ».
    parent = QWidget()
    actions = build_actions(parent, profile_ids_and_labels=[("tei_all", "TEI (tout)")])
    return parent, actions


def test_tooltip_contains_text_and_shortcut(qapp) -> None:
    parent, actions = _actions(qapp)
    apply_tooltips_with_shortcuts(actions)
    assert actions.save.toolTip() == "Enregistrer (Ctrl+S)"
    assert actions.undo.toolTip() == "Annuler (Ctrl+Z)"
    assert actions.find_replace.toolTip() == "Rechercher/remplacer... (Ctrl+F)"


def test_tooltip_without_shortcut_has_no_parentheses(qapp) -> None:
    parent, actions = _actions(qapp)
    apply_tooltips_with_shortcuts(actions)
    assert actions.tags.unwrap.shortcut().isEmpty()
    assert "(" not in actions.tags.unwrap.toolTip()
    assert actions.tags.unwrap.toolTip() == "Dégrouper la balise"


def test_tooltip_has_no_mnemonic_ampersand(qapp) -> None:
    parent, actions = _actions(qapp)
    apply_tooltips_with_shortcuts(actions)
    assert "&" not in actions.save.toolTip()
