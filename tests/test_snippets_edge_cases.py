"""Cas limites et branches d'erreur de :mod:`tei_editor.editor.snippets`
non couverts par `tests/test_snippets.py` (phase 9)."""

from __future__ import annotations

import pytest

from tei_editor.editor.current_element import ElementSpan
from tei_editor.editor.snippets import (
    load_choice_pairs,
    plan_group_as_choice,
    plan_insert_apparatus,
    plan_mark_shared_verse,
)


def test_load_choice_pairs_fichier_absent_renvoie_liste_vide(monkeypatch, tmp_path) -> None:
    load_choice_pairs.cache_clear()
    monkeypatch.setattr(
        "tei_editor.editor.snippets.CHOICE_PAIRS_PATH", tmp_path / "absent.json"
    )
    try:
        assert load_choice_pairs() == []
    finally:
        load_choice_pairs.cache_clear()


def test_group_as_choice_echange_bornes_inversees() -> None:
    edits_normal, pos_normal = plan_group_as_choice(2, 6, "orig", "reg")
    edits_inverses, pos_inverse = plan_group_as_choice(6, 2, "orig", "reg")
    assert edits_inverses == edits_normal
    assert pos_inverse == pos_normal


def test_insert_apparatus_echange_bornes_inversees() -> None:
    edits_normal, pos_normal = plan_insert_apparatus(3, 9, 1)
    edits_inverses, pos_inverse = plan_insert_apparatus(9, 3, 1)
    assert edits_inverses == edits_normal
    assert pos_inverse == pos_normal


def test_mark_shared_verse_rejette_un_l_autofermant() -> None:
    span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=4,
        self_closing=True,
    )
    # content_start == content_end == start_tag_end pour un élément
    # auto-fermant : il faut passer split_offset=4 pour satisfaire le
    # premier contrôle (position à l'intérieur du contenu) et atteindre
    # la vérification spécifique « pas de balise fermante ».
    with pytest.raises(ValueError, match="balise fermante"):
        plan_mark_shared_verse("<l/>", span, 4, 10, "12")
