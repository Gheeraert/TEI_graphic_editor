"""Tests de construction du plan structurel (`editor.outline`), sans Qt."""

from __future__ import annotations

from tei_editor.editor.outline import build_outline
from tei_editor.tei.xml_safety import parse_xml_safely

DOC = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc/>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <body>\n"
    '      <div type="chapitre">\n'
    "        <head>Titre</head>\n"
    "        <p>Un <hi>paragraphe</hi> avec une <note>note</note>.</p>\n"
    "      </div>\n"
    '      <div type="chapitre">\n'
    "        <head>Second titre</head>\n"
    "        <p>Autre paragraphe.</p>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_build_outline_hierarchie_de_base() -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    assert outline is not None
    assert outline.tag == "TEI"
    top_level_tags = [child.tag for child in outline.children]
    assert top_level_tags == ["teiHeader", "text"]


def test_build_outline_descend_jusquaux_div_et_head() -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    text_node = next(c for c in outline.children if c.tag == "text")
    body_node = next(c for c in text_node.children if c.tag == "body")
    divs = [c for c in body_node.children if c.tag == "div"]
    assert len(divs) == 2
    first_div_children_tags = [c.tag for c in divs[0].children]
    assert first_div_children_tags == ["head"]


def test_build_outline_ignore_hi_et_note_dans_p() -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    text_node = next(c for c in outline.children if c.tag == "text")
    body_node = next(c for c in text_node.children if c.tag == "body")
    divs = [c for c in body_node.children if c.tag == "div"]
    # <p> n'est pas un élément structurant (hors liste) : ni lui, ni ses
    # enfants <hi>/<note> n'apparaissent dans le plan.
    for tag in ("p", "hi", "note"):
        assert tag not in [c.tag for c in divs[0].children]


def test_build_outline_label_inclut_le_type() -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    text_node = next(c for c in outline.children if c.tag == "text")
    body_node = next(c for c in text_node.children if c.tag == "body")
    first_div = next(c for c in body_node.children if c.tag == "div")
    assert "chapitre" in first_div.label


def test_build_outline_lines_sont_croissantes_dans_lordre_du_document() -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    text_node = next(c for c in outline.children if c.tag == "text")
    body_node = next(c for c in text_node.children if c.tag == "body")
    divs = [c for c in body_node.children if c.tag == "div"]
    assert divs[0].line < divs[1].line
