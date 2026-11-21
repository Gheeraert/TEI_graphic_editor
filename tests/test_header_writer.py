"""Tests de non-perte de :mod:`tei_editor.tei.header_writer` (phase 6,
critère d'acceptation central de `docs/ROADMAP.md` §5) :

1. Aucun changement dans le dialogue -> le texte reste strictement
   identique, octet à octet.
2. Un seul champ modifié -> seule la plage du sous-élément concerné
   change ; tout le reste (y compris un élément non géré ajouté au
   document de test) reste identique au caractère près.
"""

from __future__ import annotations

import copy
from pathlib import Path

from lxml import etree

from tei_editor.editor.structured_edits import apply_edits_to_text
from tei_editor.tei.header_reader import read_header
from tei_editor.tei.header_writer import changed_keys, plan_header_edits
from tei_editor.tei.xml_safety import safe_xml_parser

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tei-samples"
COMPLETE_HEADER = FIXTURES / "02-entete" / "01-entete-complet.xml"

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "tei_editor"
    / "data"
    / "schemas"
    / "tei_all"
    / "tei_all.rng"
)


def _validate_relaxng(text: str) -> None:
    schema = etree.RelaxNG(etree.parse(str(SCHEMA_PATH)))
    root = etree.fromstring(text.encode("utf-8"), parser=safe_xml_parser())
    assert schema.validate(root.getroottree()), schema.error_log


def test_no_changes_means_byte_identical_text():
    text = COMPLETE_HEADER.read_text(encoding="utf-8")
    result = read_header(text)
    edited = copy.deepcopy(result.data)  # aucune modification

    assert changed_keys(result.data, edited) == []
    edits = plan_header_edits(result, edited)
    assert edits == []
    new_text = apply_edits_to_text(text, edits)
    assert new_text == text


def test_single_field_change_is_strictly_localized():
    text = COMPLETE_HEADER.read_text(encoding="utf-8")
    result = read_header(text)
    edited = copy.deepcopy(result.data)

    # Ajoute un auteur supplémentaire : seul titleStmt doit changer.
    from tei_editor.tei.header_model import ResponsibleParty

    edited.responsible_parties.append(ResponsibleParty(role="author", name="Ève Nouvelle Auteure"))

    assert changed_keys(result.data, edited) == ["titleStmt"]
    edits = plan_header_edits(result, edited)
    assert len(edits) == 1

    title_stmt_location = result.locations["titleStmt"]
    new_text = apply_edits_to_text(text, edits)

    # Tout le texte strictement avant/après la plage de titleStmt reste
    # identique au caractère près.
    before = text[: title_stmt_location.start]
    after = text[title_stmt_location.end :]
    assert new_text.startswith(before)
    assert new_text.endswith(after)
    assert "Ève Nouvelle Auteure" in new_text

    # Les autres sous-éléments gérés gardent leurs octets d'origine.
    for key in ("editionStmt", "extent", "publicationStmt", "sourceDesc", "encodingDesc", "profileDesc", "revisionDesc"):
        loc = result.locations[key]
        assert text[loc.start : loc.end] in new_text

    _validate_relaxng(new_text)


def test_single_field_change_preserves_unmanaged_elements():
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <teiHeader>\n"
        "    <fileDesc>\n"
        "      <titleStmt><title>Titre original</title></titleStmt>\n"
        "      <seriesStmt><title>Collection non géré</title></seriesStmt>\n"
        "      <publicationStmt><p>Non publié.</p></publicationStmt>\n"
        "      <sourceDesc><bibl>Source.</bibl></sourceDesc>\n"
        "    </fileDesc>\n"
        "    <encodingDesc>\n"
        "      <projectDesc><p>Projet.</p></projectDesc>\n"
        "      <customInconnu attr=\"valeur\">contenu personnalisé non géré</customInconnu>\n"
        "    </encodingDesc>\n"
        "  </teiHeader>\n"
        "  <text><body><p>Texte.</p></body></text>\n"
        "</TEI>\n"
    )
    result = read_header(text)
    edited = copy.deepcopy(result.data)
    edited.extent = "3 pages"  # extent n'existait pas : insertion.

    assert changed_keys(result.data, edited) == ["extent"]
    edits = plan_header_edits(result, edited)
    new_text = apply_edits_to_text(text, edits)

    assert "<seriesStmt><title>Collection non géré</title></seriesStmt>" in new_text
    assert (
        '<customInconnu attr="valeur">contenu personnalisé non géré</customInconnu>' in new_text
    )
    assert "<extent>3 pages</extent>" in new_text
    # Le reste du document (titleStmt, sourceDesc...) reste identique.
    assert "<titleStmt><title>Titre original</title></titleStmt>" in new_text
    assert "<sourceDesc><bibl>Source.</bibl></sourceDesc>" in new_text


def test_unmanaged_child_survives_even_when_its_own_container_is_regenerated():
    """Cas plus exigeant que la simple isolation entre sous-éléments :
    un élément non géré *à l'intérieur* d'un conteneur géré
    (`<customInconnu>` dans `<encodingDesc>`, au même niveau que
    `projectDesc`) doit survivre même quand CE conteneur est régénéré
    parce qu'un champ qu'il porte a changé (ici `projectDesc`)."""
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <teiHeader>\n"
        "    <fileDesc>\n"
        "      <titleStmt><title>Titre</title></titleStmt>\n"
        "      <publicationStmt><p>Non publié.</p></publicationStmt>\n"
        "      <sourceDesc><bibl>Source.</bibl></sourceDesc>\n"
        "    </fileDesc>\n"
        "    <encodingDesc>\n"
        "      <projectDesc><p>Projet original.</p></projectDesc>\n"
        "      <customInconnu attr=\"valeur\">contenu personnalisé non géré</customInconnu>\n"
        "    </encodingDesc>\n"
        "  </teiHeader>\n"
        "  <text><body><p>Texte.</p></body></text>\n"
        "</TEI>\n"
    )
    result = read_header(text)
    edited = copy.deepcopy(result.data)
    edited.encoding.project_desc = "Projet modifié."

    assert changed_keys(result.data, edited) == ["encodingDesc"]
    edits = plan_header_edits(result, edited)
    new_text = apply_edits_to_text(text, edits)

    assert "Projet modifié." in new_text
    assert "Projet original." not in new_text
    assert '<customInconnu attr="valeur">contenu personnalisé non géré</customInconnu>' in new_text


def test_writing_into_missing_subelements_produces_valid_header():
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <teiHeader>\n"
        "    <fileDesc>\n"
        "      <titleStmt></titleStmt>\n"
        "    </fileDesc>\n"
        "  </teiHeader>\n"
        "  <text><body><p>Texte.</p></body></text>\n"
        "</TEI>\n"
    )
    result = read_header(text)
    edited = copy.deepcopy(result.data)
    from tei_editor.tei.header_model import PublicationStatement, SourceDescription, TitleEntry

    edited.titles.append(TitleEntry(text="Nouveau titre"))
    edited.publication = PublicationStatement(publisher="Éditeur", pub_place="Paris")
    edited.source = SourceDescription(mode="bibl", bibl_text="Pas de source : document né numérique.")

    edits = plan_header_edits(result, edited)
    assert len(edits) == 3
    new_text = apply_edits_to_text(text, edits)

    assert "<title>Nouveau titre</title>" in new_text
    assert "<publicationStmt>" in new_text
    assert "<sourceDesc>" in new_text

    root = etree.fromstring(new_text.encode("utf-8"), parser=safe_xml_parser())
    assert root is not None
