"""Tests du dock Inspecteur (phase 5)."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLineEdit

from tei_editor.editor.current_element import locate_current_element
from tei_editor.editor.inspector_panel import InspectorPanel


def test_inspector_sans_element_courant(qapp) -> None:
    panel = InspectorPanel()
    panel.set_element(None, "", [])
    assert "Aucun" in panel.title_label.text()
    assert not panel.generate_id_button.isEnabled()


def test_inspector_attributs_presents_et_proposables(qapp) -> None:
    text = '<p rend="italique">texte</p>'
    current = locate_current_element(text, text.index("texte"))
    assert current is not None
    panel = InspectorPanel()
    panel.set_element(current, text, [])
    assert "rend" in panel._rows
    assert "xml:id" in panel._rows  # proposable, absent
    assert panel.generate_id_button.isEnabled()


def test_inspector_xml_id_deja_present_desactive_le_bouton(qapp) -> None:
    text = '<p xml:id="p-1">texte</p>'
    current = locate_current_element(text, text.index("texte"))
    panel = InspectorPanel()
    panel.set_element(current, text, [])
    assert not panel.generate_id_button.isEnabled()


def test_inspector_emet_attribute_committed_sur_line_edit(qapp) -> None:
    text = "<p>texte</p>"
    current = locate_current_element(text, text.index("texte"))
    panel = InspectorPanel()
    panel.set_element(current, text, [])
    widget = panel._rows["n"]
    assert isinstance(widget, QLineEdit)
    received = []
    panel.attribute_committed.connect(lambda name, value: received.append((name, value)))
    widget.setText("3")
    widget.editingFinished.emit()
    assert received == [("n", "3")]


def test_inspector_emet_attribute_removed_quand_vide(qapp) -> None:
    text = '<p rend="italique">texte</p>'
    current = locate_current_element(text, text.index("texte"))
    panel = InspectorPanel()
    panel.set_element(current, text, [])
    widget = panel._rows["rend"]
    received = []
    panel.attribute_removed.connect(received.append)
    widget.setText("")
    widget.editingFinished.emit()
    assert received == ["rend"]


def test_inspector_generate_id_requested(qapp) -> None:
    text = "<p>texte</p>"
    current = locate_current_element(text, text.index("texte"))
    panel = InspectorPanel()
    panel.set_element(current, text, [])
    received = []
    panel.generate_xml_id_requested.connect(lambda: received.append(True))
    panel.generate_id_button.click()
    assert received == [True]
