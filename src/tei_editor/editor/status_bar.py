"""Barre d'état : position du curseur, XPath courant, profil actif, validité.

Chaque indicateur est un simple ``QLabel`` ; cette classe ne calcule
rien elle-même (le calcul d'XPath différé/débouncé vit dans
``main_window.py``, qui appelle :mod:`tei_editor.editor.xpath`) — elle
ne fait qu'afficher ce qu'on lui donne.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStatusBar


class EditorStatusBar(QStatusBar):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._position_label = QLabel("Ligne 1, colonne 1")
        self._xpath_label = QLabel("—")
        self._profile_label = QLabel("")
        self._validity_label = QLabel("")

        for label in (
            self._position_label,
            self._xpath_label,
            self._profile_label,
            self._validity_label,
        ):
            self.addPermanentWidget(label)

    def set_cursor_position(self, line: int, column: int) -> None:
        self._position_label.setText(f"Ligne {line}, colonne {column}")

    def set_xpath(self, xpath: str | None) -> None:
        self._xpath_label.setText(xpath if xpath else "— (document mal formé)")

    def set_active_profile(self, label: str) -> None:
        self._profile_label.setText(f"Profil : {label}")

    def set_validity(self, *, well_formed: bool, message: str | None = None) -> None:
        if well_formed:
            self._validity_label.setText(message or "Document bien formé")
        else:
            self._validity_label.setText(message or "Document mal formé")
