"""Tests Qt hors écran de la barre d'outils à passage à la ligne
(`tei_editor.ui.wrapping_toolbar`)."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from tei_editor.ui.wrapping_toolbar import WrappingToolBar


def test_wrapping_toolbar_instanciation_et_ajout_action(qapp: QApplication) -> None:
    toolbar = WrappingToolBar()
    action = QAction("Gras")
    action.setToolTip("Mettre en gras")

    button = toolbar.add_action(action)

    assert button in toolbar.buttons
    assert toolbar.actions_in_order == [action]
    assert button.defaultAction() is action
    toolbar.add_separator()
    assert toolbar.flow_layout.count() == 2


def test_wrapping_toolbar_row_count_augmente_quand_la_largeur_diminue(
    qapp: QApplication,
) -> None:
    toolbar = WrappingToolBar()
    for label in ("A", "B", "C", "D", "E", "F"):
        toolbar.add_action(QAction(label))

    rows_large = toolbar.row_count_for_width(2000)
    rows_small = toolbar.row_count_for_width(50)

    assert rows_small >= rows_large
    assert rows_small >= 1
