"""Widget Qt du dock « Inspecteur » (phase 5, `docs/ROADMAP.md` §5.7) :
attributs déjà présents sur l'élément courant + attributs connus du
catalogue mais absents (proposables), avec un éditeur Qt adapté au
``datatype`` (délégué à ``editor/attribute_editors.py``).

Ce panneau ne modifie jamais lui-même le texte XML : il affiche l'état
courant et émet des signaux (``attribute_committed``,
``attribute_removed``, ``generate_xml_id_requested``) que
``main_window.py`` traduit en opérations de
``editor/structured_edits.py`` (un bloc d'annulation par opération,
voir ce module). Après chaque opération, ``main_window.py`` rappelle
:meth:`set_element` (même timer débouncé que le plan/les problèmes) :
c'est ce qui fait réapparaître la nouvelle valeur/le nouvel attribut.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tei_editor.editor.attribute_editors import make_editor_for_attribute
from tei_editor.editor.current_element import CurrentElement
from tei_editor.tei.catalog import attribute_gloss, attributes_of, element_gloss


class InspectorPanel(QWidget):
    """``attribute_committed(attr_name, new_value)``,
    ``attribute_removed(attr_name)`` et ``generate_xml_id_requested()``
    sont émis sur action de l'utilisateur ; ``main_window.py`` s'abonne
    pour appliquer l'opération correspondante."""

    attribute_committed = Signal(str, str)
    attribute_removed = Signal(str)
    generate_xml_id_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current: CurrentElement | None = None

        outer = QVBoxLayout(self)
        self.title_label = QLabel("Aucun élément courant.")
        outer.addWidget(self.title_label)

        self.generate_id_button = QPushButton("Générer un xml:id")
        self.generate_id_button.clicked.connect(self.generate_xml_id_requested.emit)
        outer.addWidget(self.generate_id_button)

        self.form = QFormLayout()
        outer.addLayout(self.form)
        outer.addStretch(1)

        self._rows: dict[str, QWidget] = {}
        self.set_element(None, "", [])

    # -- Contenu -----------------------------------------------------------
    def set_element(self, current: CurrentElement | None, text: str, document_xml_ids: list[str]) -> None:
        """Reconstruit la liste d'attributs pour ``current`` (appelé
        depuis le même timer débouncé que les autres panneaux)."""
        self._current = current
        self._clear_form()

        if current is None:
            self.title_label.setText("Aucun élément courant.")
            self.generate_id_button.setEnabled(False)
            return

        element = current.element
        ident = element.tag if isinstance(element.tag, str) else str(element.tag)
        self.title_label.setText(f"Élément courant : {element_gloss(ident)}")

        known_attrs = attributes_of(ident)
        known_idents = {a["ident"] for a in known_attrs}
        present = dict(element.attrib)
        # xml:id/xml:lang sont exposés par lxml avec leur URI complète :
        # on les représente sous leur forme courte pour l'affichage/édition.
        present = {_short_name(k): v for k, v in present.items()}

        has_xml_id = "xml:id" in present
        self.generate_id_button.setEnabled(not has_xml_id)

        # Attributs présents (y compris ceux non connus du catalogue, par
        # prudence : on ne doit jamais "perdre" un attribut déjà écrit).
        for attr_name, value in sorted(present.items()):
            catalog_entry = next((a for a in known_attrs if a["ident"] == attr_name), None)
            self._add_row(attr_name, value, catalog_entry, document_xml_ids, present=True)

        # Attributs connus du catalogue mais absents (proposables).
        for attr in known_attrs:
            if attr["ident"] in present:
                continue
            self._add_row(attr["ident"], "", attr, document_xml_ids, present=False)

    def _clear_form(self) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        self._rows.clear()

    def _add_row(
        self,
        attr_name: str,
        value: str,
        catalog_entry: dict | None,
        document_xml_ids: list[str],
        *,
        present: bool,
    ) -> None:
        container = QWidget(self)
        from PySide6.QtWidgets import QHBoxLayout

        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)

        if catalog_entry is not None:
            widget = make_editor_for_attribute(
                catalog_entry, current_value=value, document_xml_ids=document_xml_ids
            )
        else:
            widget = QLineEdit(value)
        row_layout.addWidget(widget)

        remove_button = QPushButton("✖")
        remove_button.setMaximumWidth(24)
        remove_button.setVisible(present)
        remove_button.clicked.connect(lambda: self.attribute_removed.emit(attr_name))
        row_layout.addWidget(remove_button)

        self._connect_commit(widget, attr_name)

        label = attribute_gloss(attr_name)
        self.form.addRow(label, container)
        self._rows[attr_name] = widget

    def _connect_commit(self, widget: QWidget, attr_name: str) -> None:
        if isinstance(widget, QComboBox):
            widget.activated.connect(lambda _index: self._emit_commit(attr_name, widget))
            if widget.isEditable():
                widget.lineEdit().editingFinished.connect(lambda: self._emit_commit(attr_name, widget))
        elif isinstance(widget, QLineEdit):
            widget.editingFinished.connect(lambda: self._emit_commit(attr_name, widget))

    def _emit_commit(self, attr_name: str, widget: QWidget) -> None:
        if isinstance(widget, QComboBox):
            value = widget.currentText()
        elif isinstance(widget, QLineEdit):
            value = widget.text()
        else:
            return
        if not value:
            self.attribute_removed.emit(attr_name)
            return
        self.attribute_committed.emit(attr_name, value)


def _short_name(qualified_name: str) -> str:
    if qualified_name.startswith("{http://www.w3.org/XML/1998/namespace}"):
        return "xml:" + qualified_name.rsplit("}", 1)[1]
    if "}" in qualified_name:
        return qualified_name.rsplit("}", 1)[1]
    return qualified_name
