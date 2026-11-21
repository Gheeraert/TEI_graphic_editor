"""Tests de la fabrique de widgets Qt de l'inspecteur (phase 5) : le bon
type de widget est choisi selon le datatype/closed_values d'un
attribut réel du catalogue."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLineEdit

from tei_editor.editor.attribute_editors import (
    is_valid_temporal_value,
    make_editor_for_attribute,
)
from tei_editor.tei.catalog import attributes_of


def _attr(ident: str, element: str = "p") -> dict:
    return next(a for a in attributes_of(element) if a["ident"] == ident)


def test_xml_lang_est_un_combo_editable(qapp) -> None:
    widget = make_editor_for_attribute(_attr("xml:lang"))
    assert isinstance(widget, QComboBox)
    assert widget.isEditable()
    assert widget.findText("fr") >= 0


def test_closed_values_est_un_combo_ferme(qapp) -> None:
    attribute = _attr("part", "ab")
    assert attribute["closed_values"]
    widget = make_editor_for_attribute(attribute)
    assert isinstance(widget, QComboBox)
    assert not widget.isEditable()
    assert widget.findText("Y") >= 0


def test_ref_est_un_combo_editable_avec_completion_xmlid(qapp) -> None:
    attribute = _attr("ref", "persName")
    widget = make_editor_for_attribute(attribute, document_xml_ids=["intro", "ch1"])
    assert isinstance(widget, QComboBox)
    assert widget.isEditable()
    assert widget.findText("#intro") >= 0
    assert widget.findText("#ch1") >= 0


def test_ref_accepte_saisie_libre_externe(qapp) -> None:
    attribute = _attr("ref", "persName")
    widget = make_editor_for_attribute(
        attribute, current_value="https://example.org/x", document_xml_ids=[]
    )
    assert widget.currentText() == "https://example.org/x"


def test_autre_attribut_est_un_line_edit_simple(qapp) -> None:
    attribute = _attr("n")
    widget = make_editor_for_attribute(attribute, current_value="3")
    assert isinstance(widget, QLineEdit)
    assert widget.text() == "3"


def test_validation_temporelle() -> None:
    assert is_valid_temporal_value("")
    assert is_valid_temporal_value("2024")
    assert is_valid_temporal_value("2024-01-02")
    assert is_valid_temporal_value("2024-01-02T10:30:00")
    assert not is_valid_temporal_value("pas une date")
