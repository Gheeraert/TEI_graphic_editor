"""Onglet « Titre et responsabilités » (phase 6) : titre(s) multiples +
liste de responsables (auteurs, éditeurs, financeurs, ``respStmt``
génériques), ajout/suppression/réordonnancement via
:class:`tei_editor.header_dialog.widgets.EditableTable`.
"""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from tei_editor.header_dialog.widgets import EditableTable
from tei_editor.tei.header_model import ResponsibleParty, TitleEntry

_ROLE_CHOICES = ["author", "editor", "funder", "respStmt"]


class TitleResponsibilityTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        titles_box = QGroupBox("Titres", self)
        titles_layout = QVBoxLayout(titles_box)
        titles_layout.addWidget(QLabel("Type libre : « main », « sub »... ou vide."))
        self.titles_table = EditableTable(["Titre", "Type"], parent=titles_box)
        titles_layout.addWidget(self.titles_table)
        layout.addWidget(titles_box)

        parties_box = QGroupBox("Responsables (respStmt multiples)", self)
        parties_layout = QVBoxLayout(parties_box)
        parties_layout.addWidget(
            QLabel(
                "« Libellé (resp) » n'est utilisé que pour le rôle respStmt "
                "(texte libre, ex. « Relecture »)."
            )
        )
        self.parties_table = EditableTable(
            ["Rôle", "Nom", "Libellé (resp)", "@role", "ORCID", "Affiliation"],
            combo_columns={0: _ROLE_CHOICES},
            parent=parties_box,
        )
        parties_layout.addWidget(self.parties_table)
        layout.addWidget(parties_box)

    def load(self, titles: list[TitleEntry], parties: list[ResponsibleParty]) -> None:
        self.titles_table.set_rows([[title.text, title.type or ""] for title in titles])
        self.parties_table.set_rows(
            [
                [
                    party.role,
                    party.name,
                    party.resp_label or "",
                    party.role_attribute or "",
                    party.orcid or "",
                    party.affiliation or "",
                ]
                for party in parties
            ]
        )

    def collect(self) -> tuple[list[TitleEntry], list[ResponsibleParty]]:
        titles = [
            TitleEntry(text=row[0], type=row[1].strip() or None)
            for row in self.titles_table.all_rows()
            if row[0].strip()
        ]
        parties = [
            ResponsibleParty(
                role=(row[0].strip() or "author"),  # type: ignore[arg-type]
                name=row[1],
                resp_label=row[2].strip() or None,
                role_attribute=row[3].strip() or None,
                orcid=row[4].strip() or None,
                affiliation=row[5].strip() or None,
            )
            for row in self.parties_table.all_rows()
            if row[1].strip()
        ]
        return titles, parties
