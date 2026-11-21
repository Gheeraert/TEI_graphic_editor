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


# -- Phase 4 : vérifications supplémentaires à la main (calcul par positions lxml) --

NESTED_DOC = (
    "<TEI>\n"
    "  <text>\n"
    "    <body>\n"
    '      <div n="1">\n'
    "        <p>Premier paragraphe du premier div.</p>\n"
    "      </div>\n"
    '      <div n="2">\n'
    "        <p>Un paragraphe <hi>avec emphase</hi> dans le deuxième div.</p>\n"
    "        <p>Second paragraphe du deuxième div.</p>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_xpath_p_imbrique_dans_le_premier_div() -> None:
    offset = NESTED_DOC.index("Premier paragraphe")
    assert current_xpath(NESTED_DOC, offset) == "/TEI[1]/text[1]/body[1]/div[1]/p[1]"


def test_xpath_p_imbrique_dans_le_deuxieme_div() -> None:
    offset = NESTED_DOC.index("Second paragraphe")
    assert current_xpath(NESTED_DOC, offset) == "/TEI[1]/text[1]/body[1]/div[2]/p[2]"


def test_xpath_descend_jusquau_hi_imbrique() -> None:
    offset = NESTED_DOC.index("avec emphase")
    assert current_xpath(NESTED_DOC, offset) == "/TEI[1]/text[1]/body[1]/div[2]/p[1]/hi[1]"
