"""Tests de la typographie française à la frappe (`tei_editor.tei.typography`)."""

from __future__ import annotations

from tei_editor.tei.typography import (
    NBSP,
    apply_french_typography,
    oe_ligature_replacement,
    typed_dash_replacement,
)


def test_apply_french_typography_convertit_les_guillemets_droits() -> None:
    resultat = apply_french_typography('Il dit "bonjour" fort.')
    assert resultat == f"Il dit «{NBSP}bonjour{NBSP}» fort."


def test_apply_french_typography_est_idempotente() -> None:
    once = apply_french_typography('Il dit "bonjour" ; il part !')
    twice = apply_french_typography(once)
    assert once == twice


def test_typed_dash_replacement_deux_puis_trois_tirets() -> None:
    assert typed_dash_replacement("mot--") == "–"
    assert typed_dash_replacement("mot–-") == "—"
    assert typed_dash_replacement("mot") is None


def test_oe_ligature_replacement() -> None:
    assert oe_ligature_replacement("coeur") == "cœur"
    assert oe_ligature_replacement("Oeuvre") == "Œuvre"
    assert oe_ligature_replacement("SOEUR") == "SŒUR"
    assert oe_ligature_replacement("autre") == "autre"
