"""Cas limites et branches d'erreur de :mod:`tei_editor.editor.structured_edits`
non couverts par `tests/test_structured_edits.py` (phase 9, `docs/ROADMAP.md`
§5 : couverture ciblée des modules d'opérations d'édition)."""

from __future__ import annotations

import pytest

from tei_editor.editor.current_element import ElementSpan
from tei_editor.editor.structured_edits import (
    TextEdit,
    apply_edits_to_text,
    can_merge_paragraphs,
    can_split_paragraph,
    plan_merge_paragraphs,
    plan_rename,
    plan_wrap_selection,
    unaffected_text_outside,
)


def test_apply_edits_to_text_rejette_une_plage_invalide() -> None:
    with pytest.raises(ValueError):
        apply_edits_to_text("abcdef", [TextEdit(4, 2, "x")])


def test_apply_edits_to_text_rejette_des_plages_qui_se_recouvrent() -> None:
    with pytest.raises(ValueError):
        apply_edits_to_text("abcdef", [TextEdit(0, 3, "x"), TextEdit(2, 4, "y")])


def test_unaffected_text_outside_sans_edition_renvoie_tout_le_texte_avant() -> None:
    before, after = unaffected_text_outside("abcdef", [])
    assert before == "abcdef"
    assert after == ""


def test_wrap_selection_echange_bornes_inversees() -> None:
    # selection_start > selection_end : l'opération doit les permuter
    # plutôt que produire un résultat incohérent.
    edits_normal = plan_wrap_selection(2, 5, "hi")
    edits_inverses = plan_wrap_selection(5, 2, "hi")
    assert edits_inverses == edits_normal


def test_plan_rename_sans_correspondance_renvoie_liste_vide() -> None:
    # Balise ouvrante dont le texte ne correspond pas au motif de nom
    # d'élément attendu (cas défensif, ne devrait pas arriver en usage
    # normal puisque `span` provient toujours d'un élément réel).
    span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=3,
        self_closing=False,
    )
    assert plan_rename("???", span, "p") == []


def test_can_split_paragraph_faux_pour_un_element_autofermant() -> None:
    span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=5,
        self_closing=True,
    )
    assert can_split_paragraph(span, 3) is False


def test_can_merge_paragraphs_faux_si_noms_differents() -> None:
    first_span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=3,
        self_closing=False,
        end_tag_start=10,
        end_tag_end=14,
    )
    assert can_merge_paragraphs(first_span, "ab", "p") is False


def test_plan_merge_paragraphs_rejette_un_premier_paragraphe_autofermant() -> None:
    first_span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=5,
        self_closing=True,
    )
    second_span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=10,
        start_tag_end=13,
        self_closing=False,
        end_tag_start=20,
        end_tag_end=24,
    )
    with pytest.raises(ValueError):
        plan_merge_paragraphs(first_span, second_span)
