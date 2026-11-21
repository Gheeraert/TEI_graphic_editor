"""Calcul de l'XPath courant depuis une position de curseur, sans Qt."""

from __future__ import annotations

from tei_editor.editor.xpath import current_xpath

SIMPLE_DOC = (
    "<TEI>\n"
    "  <teiHeader>\n"
    "    <fileDesc/>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <body>\n"
    "      <p>Un paragraphe.</p>\n"
    "      <p>Un deuxième paragraphe.</p>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_xpath_at_start_of_document_is_root_only() -> None:
    offset = SIMPLE_DOC.index("<teiHeader") + len("<teiHeader>")
    assert current_xpath(SIMPLE_DOC, offset) == "/TEI[1]/teiHeader[1]"


def test_xpath_inside_first_paragraph() -> None:
    offset = SIMPLE_DOC.index("Un paragraphe")
    assert current_xpath(SIMPLE_DOC, offset) == "/TEI[1]/text[1]/body[1]/p[1]"


def test_xpath_inside_second_paragraph_has_sibling_index_two() -> None:
    offset = SIMPLE_DOC.index("Un deuxième")
    assert current_xpath(SIMPLE_DOC, offset) == "/TEI[1]/text[1]/body[1]/p[2]"


def test_xpath_before_root_element_is_slash() -> None:
    assert current_xpath(SIMPLE_DOC, 0) == "/"


def test_xpath_after_root_closes_is_slash() -> None:
    assert current_xpath(SIMPLE_DOC, len(SIMPLE_DOC)) == "/"


def test_xpath_is_none_for_malformed_document() -> None:
    assert current_xpath("<TEI><a></TEI>", 7) is None


def test_xpath_skips_self_closing_sibling_for_indexing() -> None:
    doc = "<TEI><a/><a>contenu</a></TEI>"
    offset = doc.index("contenu")
    assert current_xpath(doc, offset) == "/TEI[1]/a[2]"


def test_xpath_ignores_comments_and_processing_instructions() -> None:
    doc = '<?xml version="1.0"?>\n<!-- commentaire --><TEI><p>texte</p></TEI>'
    offset = doc.index("texte")
    assert current_xpath(doc, offset) == "/TEI[1]/p[1]"
