"""Construction/validation basique du modèle de données de l'assistant
d'en-tête (phase 6)."""

from __future__ import annotations

from tei_editor.tei.header_model import (
    ChangeEntry,
    EditionStatement,
    EncodingDescription,
    IdentifierEntry,
    LanguageUsage,
    ProfileDescription,
    PublicationStatement,
    ResponsibleParty,
    RevisionDescription,
    SourceDescription,
    TeiHeaderData,
    TitleEntry,
)


def test_default_tei_header_data_is_empty():
    data = TeiHeaderData()
    assert data.titles == []
    assert data.responsible_parties == []
    assert data.edition == EditionStatement()
    assert data.extent == ""
    assert data.publication == PublicationStatement()
    assert data.source.mode == "bibl"
    assert data.encoding == EncodingDescription()
    assert data.profile == ProfileDescription()
    assert data.revisions == RevisionDescription()


def test_responsible_party_roles():
    author = ResponsibleParty(role="author", name="Alice Auteur")
    resp = ResponsibleParty(role="respStmt", name="Camille Encodeuse", resp_label="Encodage TEI")
    assert author.role == "author"
    assert resp.resp_label == "Encodage TEI"


def test_title_entry_equality_for_change_detection():
    assert TitleEntry(text="Titre", type="main") == TitleEntry(text="Titre", type="main")
    assert TitleEntry(text="Titre", type="main") != TitleEntry(text="Autre", type="main")


def test_tei_header_data_equality_by_value():
    first = TeiHeaderData(titles=[TitleEntry(text="A")])
    second = TeiHeaderData(titles=[TitleEntry(text="A")])
    third = TeiHeaderData(titles=[TitleEntry(text="B")])
    assert first == second
    assert first != third


def test_publication_statement_identifiers_and_license():
    pub = PublicationStatement(
        publisher="Presses",
        identifiers=[IdentifierEntry(type="URI", value="https://example.org")],
        license_spdx_id="CC-BY-4.0",
    )
    assert pub.identifiers[0].value == "https://example.org"
    assert pub.license_spdx_id == "CC-BY-4.0"


def test_source_description_modes():
    bibl = SourceDescription(mode="bibl", bibl_text="Une source.")
    msdesc = SourceDescription(mode="msDesc", msdesc_repository="BnF", msdesc_idno="ms. 1234")
    assert bibl.mode == "bibl"
    assert msdesc.mode == "msDesc"


def test_profile_description_languages_and_keywords():
    profile = ProfileDescription(
        languages=[LanguageUsage(ident="fr", name="français")],
        keywords=["correspondance", "XIXe siècle"],
    )
    assert profile.languages[0].ident == "fr"
    assert "correspondance" in profile.keywords


def test_revision_description_changes():
    revisions = RevisionDescription(changes=[ChangeEntry(when="2026-11-21", who="#p1", description="Création.")])
    assert revisions.changes[0].description == "Création."
