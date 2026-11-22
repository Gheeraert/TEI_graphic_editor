"""Tests purs Python (sans Qt) du convertisseur XML <-> Blocs (ADR-0012)."""

from __future__ import annotations

import pytest
from lxml import etree

from tei_editor.tei.xml_safety import parse_xml_safely
from tei_editor.wysiwyg.xml_adapter import (
    blocks_to_xml,
    find_body_element,
    replace_body_in_document,
    xml_to_blocks,
)

NS = "http://www.tei-c.org/ns/1.0"


def _document(body_inner: str) -> str:
    return (
        f'<TEI xmlns="{NS}">'
        "<teiHeader><fileDesc><titleStmt><title>T</title></titleStmt>"
        "<publicationStmt><p>P</p></publicationStmt>"
        "<sourceDesc><p>S</p></sourceDesc></fileDesc></teiHeader>"
        f"<text><body>{body_inner}</body></text></TEI>"
    )


def _body_of(xml: str) -> etree._Element:
    root = parse_xml_safely(xml)
    return find_body_element(root)


# -- Périmètre modélisé : round-trip exact ------------------------------------
def test_roundtrip_prose_with_div_head_p_and_inline_styles() -> None:
    body_inner = (
        "<div><head>Titre</head>"
        "<p>Du texte avec <hi>une mise en valeur</hi> et "
        '<persName>Jean Dupont</persName>.</p></div>'
    )
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    assert [b.kind for b in blocks] == ["head", "p"]
    assert blocks[0].level == 1
    regenerated = blocks_to_xml(blocks)
    assert regenerated == "<div><head>Titre</head><p>Du texte avec <hi>une mise en valeur</hi> et <persName>Jean Dupont</persName>.</p></div>"


def test_roundtrip_verse_groups_consecutive_l_into_lg() -> None:
    body_inner = "<lg><l>Premier vers</l><l>Second vers</l></lg>"
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    assert [b.kind for b in blocks] == ["l", "l"]
    regenerated = blocks_to_xml(blocks)
    assert regenerated == "<lg><l>Premier vers</l><l>Second vers</l></lg>"


def test_roundtrip_list_items() -> None:
    body_inner = "<list><item>Un</item><item>Deux</item></list>"
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    assert [(b.kind, b.level) for b in blocks] == [("item", 1), ("item", 1)]
    regenerated = blocks_to_xml(blocks)
    assert regenerated == "<list><item>Un</item><item>Deux</item></list>"


def test_foreign_lang_preserved_through_roundtrip() -> None:
    body_inner = '<p>Un mot <foreign xml:lang="la">mixte</foreign>.</p>'
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    run = next(r for r in blocks[0].runs if r.style == "foreign")
    assert run.lang == "la"
    regenerated = blocks_to_xml(blocks)
    assert regenerated == '<p>Un mot <foreign xml:lang="la">mixte</foreign>.</p>'


# -- Politique de simplification (ADR-0012), sans échappatoire ---------------
def test_unmodeled_inline_element_is_unwrapped_to_plain_text() -> None:
    body_inner = "<p>Une <choice><sic>erreur</sic><corr>correction</corr></choice> ici.</p>"
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    assert len(blocks) == 1
    regenerated = blocks_to_xml(blocks)
    assert "<choice>" not in regenerated
    assert "<sic>" not in regenerated
    assert "erreur" in regenerated and "correction" in regenerated


def test_unmodeled_block_element_is_flattened_to_a_paragraph() -> None:
    body_inner = "<app><lem>texte reçu</lem><rdg>variante</rdg></app>"
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    assert [b.kind for b in blocks] == ["p"]
    regenerated = blocks_to_xml(blocks)
    assert "<app>" not in regenerated and "<lem>" not in regenerated
    assert "texte reçu" in regenerated and "variante" in regenerated


def test_unmodeled_element_attributes_are_dropped() -> None:
    body_inner = '<p>Un <rs type="personnage">nom</rs> non modélisé.</p>'
    blocks = xml_to_blocks(_body_of(_document(body_inner)))
    regenerated = blocks_to_xml(blocks)
    assert "type=" not in regenerated
    assert "<rs" not in regenerated
    assert "nom" in regenerated


# -- replace_body_in_document : ce qui est hors <body> reste intact ----------
def test_replace_body_in_document_preserves_everything_outside_body() -> None:
    full_text = _document("<p>Ancien</p>")
    new_text = replace_body_in_document(full_text, "<p>Nouveau</p>")
    header_part = full_text.split("<text>")[0]
    assert new_text.startswith(header_part)
    assert "<p>Nouveau</p>" in new_text
    assert "<p>Ancien</p>" not in new_text


def test_replace_body_in_document_raises_on_malformed_xml() -> None:
    with pytest.raises(Exception):
        replace_body_in_document("<TEI><text><body><p>oops</body></text></TEI>", "<p>x</p>")


def test_replace_body_in_document_raises_without_body() -> None:
    document = f'<TEI xmlns="{NS}"><teiHeader/><text><front/></text></TEI>'
    with pytest.raises(ValueError):
        replace_body_in_document(document, "<p>x</p>")
