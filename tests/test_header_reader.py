"""Tests de :mod:`tei_editor.tei.header_reader` : lecture d'en-têtes réels,
lecture tolérante d'un en-tête incomplet, et préservation d'un élément non
géré (critère central de la phase 6, `docs/ROADMAP.md` §5)."""

from __future__ import annotations

from pathlib import Path

from tei_editor.tei.header_reader import read_header

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tei-samples"
COMPLETE_HEADER = FIXTURES / "02-entete" / "01-entete-complet.xml"
INCOMPLETE_HEADER = FIXTURES / "99-invalides" / "05-en-tete-incomplet.xml"


def test_reads_complete_header():
    text = COMPLETE_HEADER.read_text(encoding="utf-8")
    result = read_header(text)
    assert result.well_formed
    assert result.header_exists
    assert result.file_desc_exists

    data = result.data
    assert [t.text for t in data.titles] == ["Les Lettres d'exemple", "édition électronique"]
    assert data.titles[0].type == "main"
    assert data.titles[1].type == "sub"

    roles = [(p.role, p.name) for p in data.responsible_parties]
    assert ("author", "Alice Auteur") in roles
    assert any(p.role == "editor" and "Bernard" in p.name for p in data.responsible_parties)
    editor = next(p for p in data.responsible_parties if p.role == "editor")
    assert editor.orcid == "https://orcid.org/0000-0000-0000-0000"
    assert editor.role_attribute == "scientifique"
    resp_stmts = [p for p in data.responsible_parties if p.role == "respStmt"]
    assert len(resp_stmts) == 2
    assert resp_stmts[0].resp_label == "Encodage TEI"
    assert resp_stmts[0].name == "Camille Encodeuse"
    assert any(p.role == "funder" for p in data.responsible_parties)

    assert data.edition.text == "Première édition électronique"
    assert data.edition.n == "1"
    assert data.extent == "12 lettres"

    pub = data.publication
    assert pub.publisher == "Presses universitaires d'exemple"
    assert pub.pub_place == "Rouen"
    assert pub.date_when == "2026-11-21"
    assert pub.identifiers[0].type == "URI"
    assert pub.identifiers[0].value == "https://example.org/lettres-exemple"
    assert pub.availability_status == "free"
    assert pub.license_name == "CC BY 4.0"
    assert pub.license_spdx_id == "CC-BY-4.0"

    assert data.source.mode == "bibl"
    assert "Lettres d'exemple" in data.source.bibl_text

    assert "numérique" in data.encoding.project_desc
    assert data.encoding.editorial_decl
    # tagsDecl est lu comme texte libre (itertext de tout le sous-arbre) :
    # ici le texte de la <rendition> qu'il contient.
    assert "italic" in data.encoding.tags_decl

    assert any(lang.ident == "fr" for lang in data.profile.languages)
    assert "correspondance" in data.profile.keywords
    assert "XIXe siècle" in data.profile.keywords

    assert data.revisions.status == "draft"
    assert len(data.revisions.changes) == 1
    assert data.revisions.changes[0].when == "2026-11-21"


def test_managed_locations_cover_complete_header():
    text = COMPLETE_HEADER.read_text(encoding="utf-8")
    result = read_header(text)
    for key in (
        "titleStmt",
        "editionStmt",
        "extent",
        "publicationStmt",
        "sourceDesc",
        "encodingDesc",
        "profileDesc",
        "revisionDesc",
    ):
        assert key in result.locations
        location = result.locations[key]
        assert location.exists
        assert text[location.start : location.end].startswith(f"<{key}")


def test_tolerant_reading_of_incomplete_header_does_not_crash():
    text = INCOMPLETE_HEADER.read_text(encoding="utf-8")
    result = read_header(text)
    assert result.well_formed
    assert result.header_exists
    assert result.file_desc_exists

    data = result.data
    assert data.titles == []
    assert data.responsible_parties == []
    assert data.publication.publisher == ""
    assert data.source.bibl_text == ""
    assert data.encoding.project_desc == ""
    assert data.profile.languages == []
    assert data.revisions.changes == []

    # titleStmt existe (vide) : son emplacement doit être repéré pour
    # permettre l'écriture ultérieure d'un titre.
    assert result.locations["titleStmt"].exists
    # publicationStmt/sourceDesc n'existent pas : point d'insertion, pas de plage.
    assert not result.locations["publicationStmt"].exists
    assert not result.locations["sourceDesc"].exists
    assert not result.locations["encodingDesc"].exists


def test_unmanaged_elements_preserved_as_siblings_or_captured_as_extra_xml():
    """Un élément non géré peut survivre de deux façons, selon son
    emplacement dans l'arbre :

    - **sibling d'un sous-élément géré** (ex. `<seriesStmt>`, enfant
      direct de `<fileDesc>` au même niveau que `titleStmt`/`sourceDesc`) :
      il n'est jamais référencé par aucune plage gérée, donc jamais
      touché, quelle que soit l'opération.
    - **enfant direct d'un conteneur géré lui-même** (ex. un élément
      personnalisé dans `<encodingDesc>`, au même niveau que
      `projectDesc`) : capturé verbatim dans ``extra_xml`` pour être
      resplicé par `header_writer` si ce conteneur est un jour régénéré
      (voir `test_header_writer.py`), **et** laissé totalement intact si
      ce conteneur ne l'est pas (cas le plus fréquent testé ici).
    """
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <teiHeader>\n"
        "    <fileDesc>\n"
        "      <titleStmt><title>Titre</title></titleStmt>\n"
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
    assert result.well_formed

    series_stmt_start = text.index("<seriesStmt>")
    series_stmt_end = text.index("</seriesStmt>") + len("</seriesStmt>")

    for key in ("titleStmt", "publicationStmt", "sourceDesc"):
        location = result.locations[key]
        assert location.exists
        overlaps_series = location.start < series_stmt_end and location.end > series_stmt_start
        assert not overlaps_series, f"{key} recouvre seriesStmt (non géré)"

    # L'élément personnalisé dans encodingDesc est capturé verbatim.
    assert "<customInconnu" in result.extra_xml["encodingDesc"]
    assert "contenu personnalisé non géré" in result.extra_xml["encodingDesc"]


def test_read_header_on_malformed_document_is_safe():
    result = read_header("<TEI><teiHeader>")
    assert not result.well_formed
    assert result.data.titles == []
