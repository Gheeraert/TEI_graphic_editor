"""Couverture ciblée des branches de sérialisation de
:mod:`tei_editor.tei.header_writer` non exercées par
`tests/test_header_writer.py` (qui vérifie surtout la non-perte) : chaque
branche conditionnelle de chaque fonction ``serialize_*`` (phase 9,
`docs/ROADMAP.md` §5 : couverture ciblée des modules d'opérations
d'édition, pas de tests qui ne testent rien de nouveau)."""

from __future__ import annotations

import copy

from lxml import etree

from tei_editor.editor.structured_edits import apply_edits_to_text
from tei_editor.tei.header_model import (
    EditionStatement,
    EncodingDescription,
    IdentifierEntry,
    LanguageUsage,
    ProfileDescription,
    PublicationStatement,
    ResponsibleParty,
    RevisionDescription,
    SourceDescription,
    ChangeEntry,
)
from tei_editor.tei.header_reader import read_header
from tei_editor.tei.header_writer import (
    changed_keys,
    plan_header_edits,
    serialize_edition_stmt,
    serialize_encoding_desc,
    serialize_profile_desc,
    serialize_publication_stmt,
    serialize_revision_desc,
    serialize_source_desc,
    serialize_title_stmt,
)
from tei_editor.tei.xml_safety import safe_xml_parser


def _parse_fragment(xml_fragment: str) -> etree._Element:
    wrapped = f'<root xmlns="http://www.tei-c.org/ns/1.0">{xml_fragment}</root>'
    return etree.fromstring(wrapped.encode("utf-8"), parser=safe_xml_parser())


# -- titleStmt : affiliation sur author/respStmt -----------------------------


def test_serialize_title_stmt_author_avec_affiliation_et_orcid() -> None:
    parties = [
        ResponsibleParty(
            role="author",
            name="Simone Autrice",
            orcid="https://orcid.org/0000-0000-0000-0001",
            affiliation="Université de Test",
        )
    ]
    xml = serialize_title_stmt([], parties, "  ")
    assert "<affiliation>Université de Test</affiliation>" in xml
    assert 'ref="https://orcid.org/0000-0000-0000-0001"' in xml
    root = _parse_fragment(xml)
    assert root is not None


def test_serialize_title_stmt_resp_stmt_avec_affiliation() -> None:
    parties = [
        ResponsibleParty(
            role="respStmt", name="Jean Relecteur", resp_label="Relecture", affiliation="Labo X"
        )
    ]
    xml = serialize_title_stmt([], parties, "  ")
    assert "<resp>Relecture</resp>" in xml
    assert "<affiliation>Labo X</affiliation>" in xml


# -- editionStmt --------------------------------------------------------------


def test_serialize_edition_stmt() -> None:
    edition = EditionStatement(text="Édition revue et corrigée", n="2")
    xml = serialize_edition_stmt(edition, "  ")
    assert '<edition n="2">Édition revue et corrigée</edition>' in xml


# -- publicationStmt : toutes les branches -----------------------------------


def test_serialize_publication_stmt_date_texte_sans_when() -> None:
    publication = PublicationStatement(date_text="vers 1850")
    xml = serialize_publication_stmt(publication, "  ")
    assert "<date>vers 1850</date>" in xml


def test_serialize_publication_stmt_identifiant_vide_est_ignore() -> None:
    publication = PublicationStatement(
        identifiers=[IdentifierEntry(type="URI", value=""), IdentifierEntry(type="ISBN", value="978-0")]
    )
    xml = serialize_publication_stmt(publication, "  ")
    assert xml.count("<idno") == 1
    assert '<idno type="ISBN">978-0</idno>' in xml


def test_serialize_publication_stmt_avec_licence_nommee() -> None:
    publication = PublicationStatement(
        availability_status="free",
        license_name="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
    )
    xml = serialize_publication_stmt(publication, "  ")
    assert (
        '<licence target="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</licence>'
        in xml
    )


def test_serialize_publication_stmt_availability_avec_statut_sans_licence() -> None:
    publication = PublicationStatement(availability_status="restricted", rights_statement="Usage réservé.\nContact requis.")
    xml = serialize_publication_stmt(publication, "  ")
    assert '<availability status="restricted">' in xml
    assert "<p>Usage réservé.</p>" in xml
    assert "<p>Contact requis.</p>" in xml


def test_serialize_publication_stmt_vide_produit_un_repli() -> None:
    publication = PublicationStatement()
    xml = serialize_publication_stmt(publication, "  ")
    assert "<p>Non publié.</p>" in xml


def test_serialize_publication_stmt_vide_avec_extra_ne_produit_pas_le_repli() -> None:
    publication = PublicationStatement()
    xml = serialize_publication_stmt(publication, "  ", extra="\n  <sponsor>Non géré</sponsor>")
    assert "Non publié." not in xml
    assert "<sponsor>Non géré</sponsor>" in xml


# -- sourceDesc : msDesc complet ----------------------------------------------


def test_serialize_source_desc_msdesc_complet() -> None:
    source = SourceDescription(
        mode="msDesc",
        msdesc_repository="Bibliothèque nationale",
        msdesc_idno="MS 123",
        msdesc_summary="Parchemin, XIVe siècle.",
    )
    xml = serialize_source_desc(source, "  ")
    assert "<repository>Bibliothèque nationale</repository>" in xml
    assert "<idno>MS 123</idno>" in xml
    assert "<physDesc><p>Parchemin, XIVe siècle.</p></physDesc>" in xml
    root = _parse_fragment(xml)
    assert root is not None


def test_serialize_source_desc_msdesc_sans_idno_utilise_le_repli() -> None:
    source = SourceDescription(mode="msDesc", msdesc_repository="Archives")
    xml = serialize_source_desc(source, "  ")
    assert "<idno>non précisé</idno>" in xml


# -- encodingDesc : chaque champ + repli --------------------------------------


def test_serialize_encoding_desc_editorial_decl_et_tags_decl() -> None:
    encoding = EncodingDescription(editorial_decl="Normalisation orthographique.", tags_decl="Rendu en italique.")
    xml = serialize_encoding_desc(encoding, "  ")
    assert "<editorialDecl><p>Normalisation orthographique.</p></editorialDecl>" in xml
    assert "<rendition>Rendu en italique.</rendition>" in xml


def test_serialize_encoding_desc_vide_produit_un_repli() -> None:
    xml = serialize_encoding_desc(EncodingDescription(), "  ")
    assert "Aucune déclaration d'encodage." in xml


def test_serialize_encoding_desc_vide_avec_extra_ne_produit_pas_le_repli() -> None:
    xml = serialize_encoding_desc(EncodingDescription(), "  ", extra="\n  <refsDecl/>")
    assert "Aucune déclaration" not in xml


# -- profileDesc : langues, mots-clés, résumé, participants + repli ----------


def test_serialize_profile_desc_complet() -> None:
    profile = ProfileDescription(
        languages=[LanguageUsage(ident="fr", name="français", usage_percent="80"), LanguageUsage(ident="la", name="latin")],
        keywords=["poésie", "XIXe siècle"],
        abstract="Résumé du corpus.",
        participants="Deux locuteurs principaux.",
    )
    xml = serialize_profile_desc(profile, "  ")
    assert '<language ident="fr" usage="80">français</language>' in xml
    assert "<language ident=\"la\">latin</language>" in xml
    assert "<term>poésie</term>" in xml
    assert "<term>XIXe siècle</term>" in xml
    assert "<abstract><p>Résumé du corpus.</p></abstract>" in xml
    assert "<particDesc><p>Deux locuteurs principaux.</p></particDesc>" in xml
    root = _parse_fragment(xml)
    assert root is not None


def test_serialize_profile_desc_vide_produit_un_repli() -> None:
    xml = serialize_profile_desc(ProfileDescription(), "  ")
    assert 'ident="fr"' in xml and "français" in xml


def test_serialize_profile_desc_vide_avec_extra_ne_produit_pas_le_repli() -> None:
    xml = serialize_profile_desc(ProfileDescription(), "  ", extra="\n  <creation>Note</creation>")
    assert "<langUsage>" not in xml


# -- revisionDesc : changements + statut + repli ------------------------------


def test_serialize_revision_desc_avec_changements_et_statut() -> None:
    revisions = RevisionDescription(
        status="unpublished",
        changes=[ChangeEntry(when="2024-01-01", who="#ed1", description="Relecture initiale.")],
    )
    xml = serialize_revision_desc(revisions, "  ")
    assert '<revisionDesc status="unpublished">' in xml
    assert '<change when="2024-01-01" who="#ed1">Relecture initiale.</change>' in xml


def test_serialize_revision_desc_vide_produit_un_repli() -> None:
    xml = serialize_revision_desc(RevisionDescription(), "  ")
    assert "Sans historique de révision." in xml


def test_serialize_revision_desc_vide_avec_extra_ne_produit_pas_le_repli() -> None:
    xml = serialize_revision_desc(RevisionDescription(), "  ", extra="\n  <listChange/>")
    assert "Sans historique" not in xml


# -- plan_header_edits : clef changée mais sans emplacement connu ------------


def test_plan_header_edits_ignore_une_clef_sans_emplacement_connu() -> None:
    """Quand `<fileDesc>` lui-même est absent, `header_reader` ne calcule
    aucun emplacement pour les clefs qui en dépendent (titleStmt,
    publicationStmt...) : `plan_header_edits` doit les ignorer
    silencieusement plutôt que produire une plage invalide (docstring de
    `plan_header_edits`, ligne « continue »)."""
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <teiHeader>\n"
        "    <encodingDesc><p>Déjà présent.</p></encodingDesc>\n"
        "  </teiHeader>\n"
        "  <text><body><p>Texte.</p></body></text>\n"
        "</TEI>\n"
    )
    result = read_header(text)
    assert result.file_desc_exists is False
    assert "titleStmt" not in result.locations
    assert "publicationStmt" not in result.locations

    edited = copy.deepcopy(result.data)
    edited.publication = PublicationStatement(publisher="Un éditeur")

    assert "publicationStmt" in changed_keys(result.data, edited)

    edits = plan_header_edits(result, edited)
    assert edits == []
    new_text = apply_edits_to_text(text, edits)
    assert new_text == text
