"""Cas limites et branches non couverts de :mod:`tei_editor.editor.diagnostics`
(phase 9, `docs/ROADMAP.md` §5 : couverture ciblée). Complète
`tests/test_diagnostics.py` sans dupliquer ses scénarios."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

import tei_editor.editor.diagnostics as diagnostics_mod
from tei_editor.editor.diagnostics import (
    SEVERITY_ERROR,
    _load_schema,
    parse_with_diagnostics,
    profile_warnings,
    reference_diagnostics,
    reformulate_relaxng_message,
    validate_relaxng,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "tei-samples"
MINIMAL_VALIDE = (FIXTURES_DIR / "01-structure" / "01-minimal.xml").read_text(encoding="utf-8")


def test_doctype_est_refuse_par_parse_with_diagnostics() -> None:
    text = (
        '<?xml version="1.0"?>\n'
        "<!DOCTYPE TEI>\n"
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader/><text><body><p>x</p></body></text></TEI>\n"
    )
    root, diagnostics = parse_with_diagnostics(text)
    assert root is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == SEVERITY_ERROR
    assert "DOCTYPE" in diagnostics[0].message


def test_load_schema_absent_degrade_la_validation_sans_planter(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(diagnostics_mod, "_schema_cache", None)
    monkeypatch.setattr(diagnostics_mod, "SCHEMA_PATH", tmp_path / "absent.rng")
    try:
        assert _load_schema() is None
        root = etree.fromstring(MINIMAL_VALIDE.encode("utf-8"))
        assert validate_relaxng(root) == []
    finally:
        monkeypatch.setattr(diagnostics_mod, "_schema_cache", None)


def test_reformulate_relaxng_message_motifs_restants() -> None:
    assert "ne sont pas valides" in reformulate_relaxng_message(
        "Element handNote failed to validate attributes"
    )
    assert "ne correspond pas au modèle attendu" in reformulate_relaxng_message(
        "Element div failed to validate content"
    )
    message_attendu = reformulate_relaxng_message("Expecting element head, got p")
    assert "Élément attendu" in message_attendu
    assert "élément trouvé" in message_attendu
    message_manque_nomme = reformulate_relaxng_message("Expecting an element title, got nothing")
    assert "il manque un élément obligatoire" in message_manque_nomme.lower()
    message_manque_anonyme = reformulate_relaxng_message("Expecting an element , got nothing")
    assert "modèle de contenu incomplet" in message_manque_anonyme
    assert "ne respectent pas l'ordre" in reformulate_relaxng_message("Invalid sequence in interleave")


def test_profile_warnings_profil_inconnu_renvoie_liste_vide() -> None:
    root = etree.fromstring(MINIMAL_VALIDE.encode("utf-8"))
    assert profile_warnings(root, "profil-qui-n-existe-pas") == []


def test_profile_warnings_ignore_les_commentaires() -> None:
    text = (
        '<?xml version="1.0"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><!-- un commentaire -->'
        "<teiHeader/><text><body><p>x</p></body></text></TEI>\n"
    )
    root = etree.fromstring(text.encode("utf-8"))
    # Ne doit pas lever même si des nœuds commentaires sont présents parmi
    # les enfants itérés (`not isinstance(element.tag, str)`).
    profile_warnings(root, "edition_textes")


def test_reference_diagnostics_ignore_les_commentaires() -> None:
    text = (
        '<?xml version="1.0"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><!-- un commentaire -->'
        "<teiHeader/><text><body><p>x</p></body></text></TEI>\n"
    )
    root = etree.fromstring(text.encode("utf-8"))
    assert reference_diagnostics(root) == []
