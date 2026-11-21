"""Onglet « Révisions » (phase 6) : liste de ``<change>`` + statut, et
une case à cocher « ajouter automatiquement une entrée de révision à
l'enregistrement ».

**Limitation assumée** (``docs/ROADMAP.md`` §5, phase 6 laisse ce choix
à l'implémentation : « si le câblage complet est trop risqué pour cette
phase, documente-le comme limitation plutôt que de le bâcler ») : cette
case n'est **pas** branchée sur le flux d'enregistrement de
``main_window.py``/``editor/text_editor.py``. La relier demanderait de
décider, à l'enregistrement, *quel* `xml:id` utiliser pour ``@who`` (pas
de notion d'« utilisateur courant » dans l'application) et de recalculer
un plan d'édition de révision à chaque `Ctrl+S`, potentiellement sur un
document dont le `teiHeader` a changé depuis l'ouverture du dialogue —
un risque de corruption plus grand que le bénéfice pour cette phase. La
case reste visible et son état est lisible par du code appelant futur
(:meth:`RevisionsTab.auto_add_on_save_requested`), mais n'a aucun effet
pour l'instant.
"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget

from tei_editor.header_dialog.widgets import EditableTable
from tei_editor.tei.header_model import ChangeEntry, RevisionDescription


class RevisionsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.status_field = QLineEdit(self)
        self.status_field.setPlaceholderText("draft, published...")
        form.addRow("Statut (@status)", self.status_field)
        layout.addLayout(form)

        self.changes_table = EditableTable(["Date (@when)", "Responsable (#id)", "Description"], parent=self)
        layout.addWidget(self.changes_table)

        self.auto_add_checkbox = QCheckBox(
            "Ajouter automatiquement une entrée de révision à l'enregistrement "
            "(non câblé dans cette phase — voir le docstring du module)",
            self,
        )
        layout.addWidget(self.auto_add_checkbox)

    def load(self, revisions: RevisionDescription) -> None:
        self.status_field.setText(revisions.status or "")
        self.changes_table.set_rows(
            [[change.when, change.who, change.description] for change in revisions.changes]
        )
        self.auto_add_checkbox.setChecked(False)

    def collect(self) -> RevisionDescription:
        changes = [
            ChangeEntry(when=row[0], who=row[1], description=row[2])
            for row in self.changes_table.all_rows()
            if row[2].strip()
        ]
        return RevisionDescription(status=self.status_field.text().strip() or None, changes=changes)

    def auto_add_on_save_requested(self) -> bool:
        return self.auto_add_checkbox.isChecked()
