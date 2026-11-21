"""Tests de `editor/current_element.py` (phase 5) : repérage de
l'élément courant et de ses bornes exactes, sans Qt."""

from __future__ import annotations

from tei_editor.editor.current_element import element_spans, locate_current_element
from tei_editor.tei.xml_safety import parse_xml_safely

DOC = (
    "<TEI>\n"
    "  <text>\n"
    "    <body>\n"
    '      <div n="1">\n'
    "        <p>Premier paragraphe.</p>\n"
    "        <p>Second paragraphe.</p>\n"
    "      </div>\n"
    "      <lb/>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_locate_current_element_inside_p() -> None:
    offset = DOC.index("Premier")
    located = locate_current_element(DOC, offset)
    assert located is not None
    assert located.element.tag == "p"


def test_locate_current_element_second_p_has_distinct_span() -> None:
    offset = DOC.index("Second")
    located = locate_current_element(DOC, offset)
    assert located.element.tag == "p"
    start_tag = DOC[located.span.start_tag_start : located.span.start_tag_end]
    assert start_tag == "<p>"
    end_tag = DOC[located.span.end_tag_start : located.span.end_tag_end]
    assert end_tag == "</p>"


def test_locate_current_element_self_closing_never_current() -> None:
    offset = DOC.index("<lb/>") + 3
    located = locate_current_element(DOC, offset)
    # <lb/> est auto-fermant, jamais retenu comme élément courant (pas de
    # contenu) : on reste donc rattaché au dernier élément non
    # auto-fermant ouvert avant lui (ici le second <p>, déjà refermé —
    # limite assumée documentée dans le module, héritée d'ADR-0007 §3).
    assert located.element.tag == "p"
    assert located.element.text == "Second paragraphe."


def test_locate_current_element_none_before_root() -> None:
    assert locate_current_element(DOC, 0) is None


def test_locate_current_element_none_after_root_closed() -> None:
    assert locate_current_element(DOC, len(DOC)) is None


def test_locate_current_element_none_for_malformed_document() -> None:
    assert locate_current_element("<TEI><a></TEI>", 7) is None


def test_element_spans_self_closing_has_no_end_tag() -> None:
    root = parse_xml_safely(DOC)
    spans = element_spans(root, DOC)
    lb = next(el for el in root.iter() if el.tag == "lb")
    span = spans[id(lb)]
    assert span.self_closing
    assert span.end_tag_start is None
    assert span.end_tag_end is None
