"""Tests du parsing XML durci (`tei_editor.tei.xml_safety`)."""

from __future__ import annotations

import pytest

from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

MINIMAL_TEI = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
    "<teiHeader/><text><body><p>Texte</p></body></text></TEI>"
)


def test_parse_xml_safely_accepte_un_document_bien_forme() -> None:
    root = parse_xml_safely(MINIMAL_TEI)
    assert root.tag.endswith("TEI")


def test_parse_xml_safely_refuse_un_doctype_externe() -> None:
    xml_avec_doctype = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE TEI SYSTEM "http://example.invalid/tei.dtd">'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
        "<text><body><p>x</p></body></text></TEI>"
    )
    with pytest.raises(UnsafeXmlError):
        parse_xml_safely(xml_avec_doctype)


def test_parse_xml_safely_refuse_un_doctype_avec_entite_interne() -> None:
    xml_avec_entite = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE TEI [<!ENTITY test "contenu">]>'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
        "<text><body><p>&test;</p></body></text></TEI>"
    )
    with pytest.raises(UnsafeXmlError):
        parse_xml_safely(xml_avec_entite)


def test_parse_xml_safely_refuse_le_xml_mal_forme() -> None:
    with pytest.raises(UnsafeXmlError):
        parse_xml_safely("<TEI><teiHeader></TEI>")


def test_parse_xml_safely_conserve_les_commentaires() -> None:
    xml_avec_commentaire = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><!-- un commentaire -->'
        "<teiHeader/><text><body><p>x</p></body></text></TEI>"
    )
    root = parse_xml_safely(xml_avec_commentaire)
    comments = [child for child in root if not isinstance(child.tag, str)]
    assert len(comments) == 1
