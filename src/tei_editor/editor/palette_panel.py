"""Widget Qt du dock « Palette » (phase 5, `docs/ROADMAP.md` §5.1) :
liste filtrable, groupée comme les profils (``groups[].label``/
``groups[].elements`` — jamais une liste de balises codée en dur,
`CLAUDE.md`), des éléments suggérés pour la position actuelle du
curseur. Permissif, pas bloquant : la recherche texte libre donne accès
à n'importe quel élément du catalogue, les suggestions (intersection
``children_approx``/profil, avec repli — voir
``tei_editor.tei.catalog.suggested_elements``) sont juste mises en
avant (gras) et triées en tête de chaque groupe.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from tei_editor.tei.catalog import element_gloss, profile_groups, suggested_elements

_ROLE_IDENT = Qt.ItemDataRole.UserRole


class PalettePanel(QWidget):
    """``element_chosen(ident)`` est émis sur double-clic ou Entrée sur
    une entrée."""

    element_chosen = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._profile_id = "tei_all"
        self._suggested: frozenset[str] = frozenset()

        layout = QVBoxLayout(self)
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Rechercher une balise...")
        self.search_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_edit)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.itemActivated.connect(self._on_item_activated)
        self.tree.itemDoubleClicked.connect(self._on_item_activated)
        layout.addWidget(self.tree)

    # -- Contenu ---------------------------------------------------------
    def set_context(self, current_element_name: str | None, profile_id: str) -> None:
        """Reconstruit la liste pour le profil ``profile_id`` et met en
        avant les éléments suggérés pour ``current_element_name``
        (appelé depuis le même timer débouncé que les autres panneaux,
        `main_window.py`)."""
        self._profile_id = profile_id
        self._suggested = frozenset(suggested_elements(current_element_name, profile_id))
        self._rebuild()

    def _rebuild(self) -> None:
        self.tree.clear()
        groups = profile_groups(self._profile_id)
        for group in groups:
            group_item = QTreeWidgetItem([group.get("label", group.get("id", ""))])
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tree.addTopLevelItem(group_item)
            elements = sorted(
                group.get("elements", []),
                key=lambda ident: (ident not in self._suggested, ident),
            )
            for ident in elements:
                label = element_gloss(ident)
                if ident in self._suggested:
                    label = f"★ {label}"
                item = QTreeWidgetItem([label])
                item.setData(0, _ROLE_IDENT, ident)
                if ident in self._suggested:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                group_item.addChild(item)
        self.tree.expandAll()
        self._apply_filter(self.search_edit.text())

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            any_visible = False
            for j in range(group_item.childCount()):
                child = group_item.child(j)
                ident = child.data(0, _ROLE_IDENT) or ""
                visible = not needle or needle in ident.lower() or needle in child.text(0).lower()
                child.setHidden(not visible)
                any_visible = any_visible or visible
            group_item.setHidden(not any_visible)

    def _on_item_activated(self, item: QTreeWidgetItem, *_args) -> None:
        ident = item.data(0, _ROLE_IDENT)
        if ident:
            self.element_chosen.emit(ident)
