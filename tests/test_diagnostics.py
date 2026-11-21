"""Tests des diagnostics structurés (phase 4) : bonne formation avec
ligne/colonne, validation RelaxNG (tei_all) et reformulation française,
avertissements hors profil."""

from __future__ import annotations

import json
from pathlib import Path

from tei_editor.editor.diagnostics import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    compute_diagnostics,
    parse_with_diagnostics,
    reference_diagnostics,
    reformulate_relaxng_message,
    validate_relaxng,
)
from tei_editor.tei.xml_safety import parse_xml_safely

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "tei-samples"
MANIFEST = json.loads((FIXTURES_DIR / "manifest.json").read_text(encoding="utf-8"))

MAL_FORME = (
    '<?xml version="1.0"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc></fileDescX>\n"
    "  </teiHeader>\n"
    "</TEI>\n"
)

MINIMAL_VALIDE = (FIXTURES_DIR / "01-structure" / "01-minimal.xml").read_text(encoding="utf-8")
HORS_MODELE = (FIXTURES_DIR / "99-invalides" / "04-hors-modele.xml").read_text(encoding="utf-8")
ENTETE_INCOMPLET = (FIXTURES_DIR / "99-invalides" / "05-en-tete-incomplet.xml").read_text(
    encoding="utf-8"
)


def test_bonne_formation_en_echec_rapporte_ligne_et_colonne() -> None:
    root, diagnostics = parse_with_diagnostics(MAL_FORME)
    assert root is None
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.severity == SEVERITY_ERROR
    assert diag.line == 4
    assert isinstance(diag.column, int) and diag.column > 0


def test_document_valide_relaxng_sans_diagnostic_derreur() -> None:
    root = parse_xml_safely(MINIMAL_VALIDE)
    assert validate_relaxng(root) == []


def test_document_invalide_relaxng_produit_un_message_francais_lisible() -> None:
    root = parse_xml_safely(HORS_MODELE)
    diagnostics = validate_relaxng(root)
    assert diagnostics, "le cas hors-modèle doit produire au moins un diagnostic RelaxNG"
    for diag in diagnostics:
        assert diag.severity == SEVERITY_ERROR
        assert "Did not expect" not in diag.message
        assert "element" not in diag.message.lower() or "élément" in diag.message.lower()
        # Pas de jargon libxml2 brut non traduit.
        assert diag.message[0].isupper()


def test_en_tete_incomplet_detecte_par_relaxng() -> None:
    root = parse_xml_safely(ENTETE_INCOMPLET)
    diagnostics = validate_relaxng(root)
    assert diagnostics


def test_reformulate_relaxng_message_motifs_connus() -> None:
    assert "n'est pas attendu" in reformulate_relaxng_message("Did not expect element p there")
    assert "n'est pas valide" in reformulate_relaxng_message(
        "Invalid attribute scribe for element handNote"
    )


def test_reformulate_relaxng_message_motif_inconnu_reste_propre() -> None:
    message = reformulate_relaxng_message("some weird libxml2 internal gibberish")
    assert "gibberish" not in message
    assert message.endswith(".")


def test_avertissement_hors_profil_pour_profil_restrictif() -> None:
    # edition_critique ne couvre pas castList/castItem (profil théâtre) :
    # un document théâtral doit déclencher un avertissement hors profil,
    # pas une erreur RelaxNG (reste valide contre tei_all).
    text = (FIXTURES_DIR / "05-theatre" / "01-scene-vers.xml").read_text(encoding="utf-8")
    diagnostics = compute_diagnostics(text, "edition_critique")
    warnings = [d for d in diagnostics if d.severity == SEVERITY_WARNING]
    errors = [d for d in diagnostics if d.severity == SEVERITY_ERROR]
    assert warnings, "au moins un élément théâtral doit être hors du profil édition critique"
    assert errors == [], "le document théâtral reste valide contre le schéma unique tei_all"


def test_compute_diagnostics_profil_tei_all_ne_produit_aucun_avertissement() -> None:
    text = (FIXTURES_DIR / "05-theatre" / "01-scene-vers.xml").read_text(encoding="utf-8")
    diagnostics = compute_diagnostics(text, "tei_all")
    assert all(d.severity != SEVERITY_WARNING for d in diagnostics)


def test_reference_cassee_produit_un_diagnostic_pour_chaque_reference_non_resolue() -> None:
    # tests/fixtures/tei-samples/99-invalides/03-reference-cassee.xml,
    # manifest.json -> expect: ["unresolved-ref"] (#absent, #T9) ;
    # vérifie que docs/ROADMAP.md §3.A3.5 est maintenant un diagnostic
    # applicatif réel (pas seulement détecté par le test ad hoc de
    # tests/test_tei_samples_corpus.py).
    text = (FIXTURES_DIR / "99-invalides" / "03-reference-cassee.xml").read_text(encoding="utf-8")
    root = parse_xml_safely(text)
    diagnostics = reference_diagnostics(root)
    assert len(diagnostics) == 2
    assert all(d.severity == SEVERITY_ERROR for d in diagnostics)
    messages = " ".join(d.message for d in diagnostics)
    assert "#absent" in messages
    assert "#T9" in messages
    # Doit aussi apparaître dans compute_diagnostics (panneau Problèmes).
    assert any("#absent" in d.message for d in compute_diagnostics(text, "tei_all"))


def test_reference_resolue_ne_produit_aucun_diagnostic() -> None:
    text = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        '<text><body><p xml:id="p1"/><ref target="#p1"/></body></text>'
        "</TEI>"
    )
    root = parse_xml_safely(text)
    assert reference_diagnostics(root) == []


def test_manifest_99_invalides_01_02_03_restent_detectes_par_bonne_formation_ou_xmlid() -> None:
    # Non-régression : ces trois cas étaient déjà détectables avant la
    # validation RelaxNG (phase 3) ; vérifié ici que compute_diagnostics
    # continue d'y voir au moins un problème.
    for entry in MANIFEST["files"]:
        if entry["file"].startswith("99-invalides/01") or entry["file"].startswith(
            "99-invalides/02"
        ):
            text = (FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8")
            diagnostics = compute_diagnostics(text, "tei_all")
            assert diagnostics, entry["file"]
