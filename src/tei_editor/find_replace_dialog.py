"""Boîte de dialogue « Rechercher/remplacer », simple, sur
``QPlainTextEdit``/``QTextDocument.find()``.

Explicitement pas le code ``find_replace.py`` de Mérope (couplé au
pivot Markdown, écarté en phase 2 — voir ``docs/AUDIT_MEROPE.md``) :
réécrit ici sans aucune dépendance au pivot ``Block``/``InlineRun``.
Regex optionnelle via ``QRegularExpression``.
"""

from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class FindReplaceDialog(QDialog):
    def __init__(self, editor, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rechercher/remplacer")
        self._editor = editor

        self._find_edit = QLineEdit()
        self._replace_edit = QLineEdit()
        self._regex_checkbox = QCheckBox("Expression régulière")
        self._case_checkbox = QCheckBox("Respecter la casse")

        find_next_button = QPushButton("Suivant")
        replace_button = QPushButton("Remplacer")
        replace_all_button = QPushButton("Remplacer tout")
        close_button = QPushButton("Fermer")

        find_next_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_current)
        replace_all_button.clicked.connect(self.replace_all)
        close_button.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Rechercher :"))
        layout.addWidget(self._find_edit)
        layout.addWidget(QLabel("Remplacer par :"))
        layout.addWidget(self._replace_edit)
        layout.addWidget(self._regex_checkbox)
        layout.addWidget(self._case_checkbox)

        buttons_row = QHBoxLayout()
        for button in (find_next_button, replace_button, replace_all_button, close_button):
            buttons_row.addWidget(button)
        layout.addLayout(buttons_row)

    def _find_flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self._case_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _needle(self):
        text = self._find_edit.text()
        if self._regex_checkbox.isChecked():
            options = QRegularExpression.PatternOption.NoPatternOption
            if not self._case_checkbox.isChecked():
                options |= QRegularExpression.PatternOption.CaseInsensitiveOption
            return QRegularExpression(text, options)
        return text

    def find_next(self) -> bool:
        needle = self._needle()
        if not needle:
            return False
        found = self._editor.find(needle, self._find_flags())
        if not found:
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            found = self._editor.find(needle, self._find_flags())
            if not found:
                QMessageBox.information(self, "Rechercher", "Aucune occurrence trouvée.")
        return found

    def replace_current(self) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self._replace_edit.text())
        self.find_next()

    def replace_all(self) -> None:
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._editor.setTextCursor(cursor)
        count = 0
        while self.find_next():
            selection_cursor = self._editor.textCursor()
            selection_cursor.insertText(self._replace_edit.text())
            self._editor.setTextCursor(selection_cursor)
            count += 1
            if count > 100000:
                break  # garde-fou contre une boucle infinie (motif vide, etc.)
        QMessageBox.information(self, "Remplacer tout", f"{count} occurrence(s) remplacée(s).")
