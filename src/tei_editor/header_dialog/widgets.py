"""Petit widget réutilisable : une liste éditable (``QTableWidget`` +
boutons Ajouter/Supprimer/Monter/Descendre), pas de glisser-déposer
(``docs/ROADMAP.md`` §5, phase 6 : « pas besoin de glisser-déposer »).
Partagé par tous les onglets de l'assistant d'en-tête qui gèrent une
liste (responsables, identifiants, langues, mots-clés, révisions).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class EditableTable(QWidget):
    """``headers`` : libellés de colonnes. ``combo_columns`` (optionnel) :
    ``{index_colonne: [choix...]}`` pour afficher un ``QComboBox``
    éditable plutôt qu'une cellule texte libre dans cette colonne."""

    def __init__(
        self,
        headers: list[str],
        *,
        combo_columns: dict[int, list[str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._combo_columns = combo_columns or {}

        outer = QVBoxLayout(self)
        self.table = QTableWidget(0, len(headers), self)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        outer.addWidget(self.table)

        buttons = QHBoxLayout()
        add_button = QPushButton("&Ajouter")
        add_button.clicked.connect(lambda: self.add_row([""] * len(headers)))
        remove_button = QPushButton("&Supprimer")
        remove_button.clicked.connect(self._remove_selected)
        up_button = QPushButton("Monter")
        up_button.clicked.connect(lambda: self._move_selected(-1))
        down_button = QPushButton("Descendre")
        down_button.clicked.connect(lambda: self._move_selected(1))
        for button in (add_button, remove_button, up_button, down_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        outer.addLayout(buttons)

    # -- Construction des lignes ------------------------------------------
    def add_row(self, values: list[str]) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, value in enumerate(values):
            self._set_cell(row, column, value)
        return row

    def _set_cell(self, row: int, column: int, value: str) -> None:
        choices = self._combo_columns.get(column)
        if choices is not None:
            combo = QComboBox(self.table)
            combo.addItems(choices)
            if value and value not in choices:
                combo.addItem(value)
            if value:
                combo.setCurrentText(value)
            self.table.setCellWidget(row, column, combo)
        else:
            self.table.setItem(row, column, QTableWidgetItem(value))

    def _remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def _move_selected(self, direction: int) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            return
        for row in rows if direction < 0 else reversed(rows):
            target = row + direction
            if 0 <= target < self.table.rowCount():
                self._swap_rows(row, target)

    def _swap_rows(self, first: int, second: int) -> None:
        first_values = self.row_values(first)
        second_values = self.row_values(second)
        for column, value in enumerate(second_values):
            self._set_cell(first, column, value)
        for column, value in enumerate(first_values):
            self._set_cell(second, column, value)

    # -- Lecture ------------------------------------------------------------
    def row_values(self, row: int) -> list[str]:
        values: list[str] = []
        for column in range(self.table.columnCount()):
            if column in self._combo_columns:
                widget = self.table.cellWidget(row, column)
                values.append(widget.currentText() if widget is not None else "")
            else:
                item = self.table.item(row, column)
                values.append(item.text() if item is not None else "")
        return values

    def all_rows(self) -> list[list[str]]:
        return [self.row_values(row) for row in range(self.table.rowCount())]

    def set_rows(self, rows: list[list[str]]) -> None:
        self.table.setRowCount(0)
        for values in rows:
            self.add_row(values)
