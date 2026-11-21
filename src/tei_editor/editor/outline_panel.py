"""Widget Qt du dock « Plan » (phase 4) : ``QTreeWidget`` reflétant la
hiérarchie construite par ``editor/outline.py``. Clic sur un nœud →
déplace le curseur de l'éditeur à la ligne de l'élément correspondant
(signal ``jump_requested``). ``select_line`` fait l'inverse : synchronise
le nœud sélectionné avec la position du curseur dans l'éditeur.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from tei_editor.editor.outline import OutlineNode

_ROLE_LINE = Qt.ItemDataRole.UserRole


class OutlinePanel(QTreeWidget):
    jump_requested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self._line_to_item: dict[int, QTreeWidgetItem] = {}
        self._updating_selection = False
        self.itemActivated.connect(self._on_item_activated)
        self.itemClicked.connect(self._on_item_activated)

    def set_outline(self, root: OutlineNode | None) -> None:
        self.clear()
        self._line_to_item.clear()
        if root is None:
            return
        self._add_node(None, root)
        self.expandToDepth(1)

    def _add_node(self, parent_item: QTreeWidgetItem | None, node: OutlineNode) -> None:
        item = QTreeWidgetItem([node.label])
        item.setData(0, _ROLE_LINE, node.line)
        if parent_item is None:
            self.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        # Une même ligne ne porte normalement qu'un seul élément
        # structurant ; en cas de collision on garde le premier (le plus
        # englobant), suffisant pour la synchronisation curseur → plan.
        self._line_to_item.setdefault(node.line, item)
        for child in node.children:
            self._add_node(item, child)

    def select_line(self, line: int) -> None:
        """Sélectionne/déplie le nœud correspondant à la ligne la plus
        proche (≤ ``line``), sans émettre ``jump_requested``."""
        if not self._line_to_item:
            return
        best_line = max((l for l in self._line_to_item if l <= line), default=None)
        if best_line is None:
            return
        item = self._line_to_item[best_line]
        self._updating_selection = True
        try:
            self.setCurrentItem(item)
            parent = item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()
            self.scrollToItem(item)
        finally:
            self._updating_selection = False

    def _on_item_activated(self, item: QTreeWidgetItem, *_args) -> None:
        if self._updating_selection:
            return
        line = item.data(0, _ROLE_LINE)
        if line is not None:
            self.jump_requested.emit(line)
