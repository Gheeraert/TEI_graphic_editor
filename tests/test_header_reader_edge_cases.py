"""Cas limites de lecture de :mod:`tei_editor.tei.header_reader` non
couverts par `tests/test_header_reader.py` : sous-éléments absents ou
sans leur enfant structuré habituel, repli sur le texte brut, détection
de l'ORCID via un ``<idno>`` imbriqué, mots-clés en texte libre
(phase 9, `docs/ROADMAP.md` §5 : couverture ciblée)."""

from __future__ import annotations

from tei_editor.tei.header_reader import read_header

_HEADER_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      {file_desc_body}\n"
    "    </fileDesc>\n"
    "    {header_body}\n"
    "  </teiHeader>\n"
    "  <text><body><p>Texte.</p></body></text>\n"
    "</TEI>\n"
)


def _build(file_desc_body: str = "<titleStmt><title>T</title></titleStmt>", header_body: str = "") -> str:
    return _HEADER_TEMPLATE.format(file_desc_body=file_desc_body, header_body=header_body)


def test_titre_absent_renvoie_listes_vides() -> None:
    text = _build(file_desc_body="<publicationStmt><p>Non publié.</p></publicationStmt>")
    result = read_header(text)
    assert result.data.titles == []
    assert result.data.responsible_parties == []


def test_commentaire_dans_titlestmt_est_ignore() -> None:
    text = _build(
        file_desc_body="<titleStmt><!-- commentaire --><title>T</title></titleStmt>"
    )
    result = read_header(text)
    assert [t.text for t in result.data.titles] == ["T"]


def test_orcid_detecte_via_idno_imbrique() -> None:
    text = _build(
        file_desc_body=(
            "<titleStmt><title>T</title>"
            '<author><persName>Simone Autrice</persName>'
            '<idno type="ORCID">0000-0000-0000-0001</idno></author>'
            "</titleStmt>"
        )
    )
    result = read_header(text)
    [author] = result.data.responsible_parties
    assert author.orcid == "0000-0000-0000-0001"


def test_edition_stmt_sans_enfant_edition_utilise_le_texte_direct() -> None:
    text = _build(
        file_desc_body=(
            "<titleStmt><title>T</title></titleStmt>"
            "<editionStmt>Mention d'édition en texte libre.</editionStmt>"
        )
    )
    result = read_header(text)
    assert result.data.edition.text == "Mention d'édition en texte libre."
    assert result.data.edition.n is None


def test_source_desc_sans_msdesc_ni_bibl_utilise_le_texte_direct() -> None:
    text = _build(
        file_desc_body=(
            "<titleStmt><title>T</title></titleStmt>"
            "<sourceDesc>Pas de structure, juste un texte.</sourceDesc>"
        )
    )
    result = read_header(text)
    assert result.data.source.mode == "bibl"
    assert result.data.source.bibl_text == "Pas de structure, juste un texte."


def test_source_desc_msdesc_est_lu() -> None:
    text = _build(
        file_desc_body=(
            "<titleStmt><title>T</title></titleStmt>"
            "<sourceDesc><msDesc><msIdentifier><repository>BnF</repository>"
            "<idno>MS 42</idno></msIdentifier>"
            "<physDesc><p>Résumé physique.</p></physDesc></msDesc></sourceDesc>"
        )
    )
    result = read_header(text)
    assert result.data.source.mode == "msDesc"
    assert result.data.source.msdesc_repository == "BnF"
    assert result.data.source.msdesc_idno == "MS 42"
    assert result.data.source.msdesc_summary == "Résumé physique."


def test_keywords_en_texte_libre_separes_par_des_virgules() -> None:
    text = _build(header_body="<profileDesc><textClass><keywords>poésie, théâtre,  roman</keywords></textClass></profileDesc>")
    result = read_header(text)
    assert result.data.profile.keywords == ["poésie", "théâtre", "roman"]


def test_document_sans_teiheader() -> None:
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <text><body><p>Texte.</p></body></text>\n"
        "</TEI>\n"
    )
    result = read_header(text)
    assert result.header_exists is False
    assert result.file_desc_exists is False
    assert result.well_formed is True
    assert result.locations == {}
