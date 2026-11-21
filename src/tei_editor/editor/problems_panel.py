"""Widget Qt du dock « Problèmes » (phase 4) : liste des diagnostics
courants (erreurs de bonne formation/RelaxNG + avertissements hors
profil), avec icône de sévérité, position « ligne:colonne » et message
français. Clic sur une entrée → déplace le curseur de l'éditeur et lui
donne le focus (signal ``jump_requested``).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from tei_editor.editor.diagnostics import SEVERITY_ERROR, Diagnostic

_ROLE_DIAGNOSTIC = Qt.ItemDataRole.UserRole

_SEVERITY_ICON = {SEVERITY_ERROR: "✖", "avertissement": "⚠"}
_SEVERITY_COLOR = {SEVERITY_ERROR: QColor("#c0392b"), "avertissement": QColor("#b58900")}


class ProblemsPanel(QListWidget):
    """Liste des diagnostics courants. ``jump_requested(line, column)``
    est émis (lignes/colonnes 1-indexées, colonne 1 si inconnue) quand
    l'utilisateur double-clique ou active une entrée."""

    jump_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._diagnostics: list[Diagnostic] = []
        self.itemActivated.connect(self._on_item_activated)
        self.itemDoubleClicked.connect(self._on_item_activated)

    def set_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        self._diagnostics = list(diagnostics)
        self.clear()
        if not self._diagnostics:
            self.addItem(QListWidgetItem("Aucun problème détecté."))
            return
        for diagnostic in self._diagnostics:
            position = f"{diagnostic.line}:{diagnostic.column}" if diagnostic.column else f"{diagnostic.line}"
            icon = _SEVERITY_ICON.get(diagnostic.severity, "•")
            item = QListWidgetItem(f"{icon} [{position}] {diagnostic.message}")
            item.setForeground(_SEVERITY_COLOR.get(diagnostic.severity, QColor("#000000")))
            item.setData(_ROLE_DIAGNOSTIC, diagnostic)
            self.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        diagnostic = item.data(_ROLE_DIAGNOSTIC)
        if diagnostic is None:
            return
        self.jump_requested.emit(diagnostic.line, diagnostic.column or 1)
