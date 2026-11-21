"""Onglet « Publication » (phase 6) : éditeur, lieu, date, identifiants,
licence — combo de licence alimenté par
:mod:`tei_editor.tei.licenses` (déjà extrait en phase 2), conformément à
la consigne de cette phase."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLineEdit, QTextEdit, QVBoxLayout, QWidget

from tei_editor.header_dialog.widgets import EditableTable
from tei_editor.tei.header_model import PublicationStatement
from tei_editor.tei.licenses import SPDX_LICENSES

_FREE_LICENSE_CHOICE = "(texte libre, pas de licence standard)"


class PublicationTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.publisher_field = QLineEdit(self)
        form.addRow("Éditeur", self.publisher_field)
        self.pub_place_field = QLineEdit(self)
        form.addRow("Lieu de publication", self.pub_place_field)
        self.date_when_field = QLineEdit(self)
        self.date_when_field.setPlaceholderText("AAAA-MM-JJ")
        form.addRow("Date (@when)", self.date_when_field)
        self.date_text_field = QLineEdit(self)
        form.addRow("Date (texte affiché)", self.date_text_field)
        self.availability_status_field = QLineEdit(self)
        self.availability_status_field.setPlaceholderText("free, restricted...")
        form.addRow("Statut de disponibilité", self.availability_status_field)
        layout.addLayout(form)

        identifiers_box = QGroupBox("Identifiants (idno)", self)
        identifiers_layout = QVBoxLayout(identifiers_box)
        self.identifiers_table = EditableTable(["Type", "Valeur"], parent=identifiers_box)
        identifiers_layout.addWidget(self.identifiers_table)
        layout.addWidget(identifiers_box)

        license_box = QGroupBox("Licence", self)
        license_layout = QFormLayout(license_box)
        self.license_combo = QComboBox(license_box)
        self.license_combo.addItem(_FREE_LICENSE_CHOICE, "")
        for spdx_id, (name, _url) in SPDX_LICENSES.items():
            self.license_combo.addItem(f"{name} ({spdx_id})", spdx_id)
        license_layout.addRow("Licence standard (SPDX)", self.license_combo)
        self.license_name_field = QLineEdit(license_box)
        license_layout.addRow("Nom (si texte libre)", self.license_name_field)
        self.license_url_field = QLineEdit(license_box)
        license_layout.addRow("URL (si texte libre)", self.license_url_field)
        self.rights_statement_field = QTextEdit(license_box)
        license_layout.addRow("Mention de droits", self.rights_statement_field)
        layout.addWidget(license_box)

    def load(self, publication: PublicationStatement) -> None:
        self.publisher_field.setText(publication.publisher)
        self.pub_place_field.setText(publication.pub_place)
        self.date_when_field.setText(publication.date_when)
        self.date_text_field.setText(publication.date_text)
        self.availability_status_field.setText(publication.availability_status or "")
        self.identifiers_table.set_rows(
            [[identifier.type or "", identifier.value] for identifier in publication.identifiers]
        )
        index = self.license_combo.findData(publication.license_spdx_id or "")
        self.license_combo.setCurrentIndex(index if index >= 0 else 0)
        self.license_name_field.setText(publication.license_name or "")
        self.license_url_field.setText(publication.license_url or "")
        self.rights_statement_field.setPlainText(publication.rights_statement)

    def collect(self) -> PublicationStatement:
        from tei_editor.tei.header_model import IdentifierEntry

        identifiers = [
            IdentifierEntry(type=row[0].strip() or None, value=row[1])
            for row in self.identifiers_table.all_rows()
            if row[1].strip()
        ]
        spdx_id = self.license_combo.currentData() or None
        return PublicationStatement(
            publisher=self.publisher_field.text(),
            pub_place=self.pub_place_field.text(),
            date_when=self.date_when_field.text(),
            date_text=self.date_text_field.text(),
            identifiers=identifiers,
            availability_status=self.availability_status_field.text().strip() or None,
            license_spdx_id=spdx_id,
            license_name=self.license_name_field.text().strip() or None,
            license_url=self.license_url_field.text().strip() or None,
            rights_statement=self.rights_statement_field.toPlainText(),
        )
