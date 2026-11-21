"""Tests de la validation RelaxNG/Schematron du profil Commons Publishing
(`tei_editor.tei.commons_publishing`)."""

from __future__ import annotations

from tei_editor.tei.commons_publishing import validate_commons_publishing_bytes

VALID_DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Titre de test</title>
        <author>Auteur de test</author>
      </titleStmt>
      <publicationStmt>
        <publisher>Éditeur de test</publisher>
        <date when="2026-01-01">2026-01-01</date>
        <availability>
          <licence target="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</licence>
        </availability>
      </publicationStmt>
      <sourceDesc>
        <p>Source de test</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div>
        <head>Titre de section</head>
        <p>Un paragraphe de contenu.</p>
      </div>
    </body>
  </text>
</TEI>
"""

INVALID_DOCUMENT = b"<TEI><ceciNestPasDuTei/></TEI>"


def test_validate_commons_publishing_bytes_document_mal_forme() -> None:
    result = validate_commons_publishing_bytes(b"<TEI><non ferme></TEI>")
    assert result.valid is False
    assert result.issues


def test_validate_commons_publishing_bytes_document_invalide_au_schema() -> None:
    result = validate_commons_publishing_bytes(INVALID_DOCUMENT)
    assert result.valid is False
    assert result.issues


def test_validate_commons_publishing_bytes_document_simple_valide() -> None:
    result = validate_commons_publishing_bytes(VALID_DOCUMENT.encode("utf-8"))
    assert result.valid is True
    assert result.issues == ()
