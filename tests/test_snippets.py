"""Tests des commandes composites de la phase 7 (`docs/ROADMAP.md` §5) :
« Grouper en choix… », « Insérer une liste de personnages… »,
« Marquer un vers partagé », « Insérer une leçon (app/lem/rdg)… ».

Même rigueur que `tests/test_structured_edits.py` (phase 5) : pour
chaque opération, (a) résultat textuel exact sur un cas simple, (b) le
texte hors de la zone touchée est identique avant/après (quand
pertinent), (c) un seul « Annuler » restaure exactement le texte
d'origine."""

from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from tei_editor.editor.current_element import element_spans, parse_xml_safely
from tei_editor.editor.snippets import (
    load_choice_pairs,
    plan_group_as_choice,
    plan_insert_apparatus,
    plan_insert_cast_list,
    plan_mark_shared_verse,
)
from tei_editor.editor.structured_edits import apply_edits_to_text, apply_edits_with_cursor, unaffected_text_outside


def _assert_single_undo_restores(qapp, original_text: str, edits) -> str:
    editor = QPlainTextEdit()
    editor.setPlainText(original_text)
    editor.document().setModified(False)
    cursor = editor.textCursor()
    apply_edits_with_cursor(cursor, edits)
    edited_text = editor.toPlainText()
    assert editor.document().isUndoAvailable()
    editor.undo()
    assert editor.toPlainText() == original_text
    return edited_text


def _span_for(text: str, tag: str):
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    element = next(el for el in root.iter() if el.tag == tag)
    return spans[id(element)]


# -- 0. Données : paires choice ------------------------------------------------


def test_load_choice_pairs_contient_les_trois_paires_de_la_roadmap() -> None:
    pairs = load_choice_pairs()
    ids = {pair["id"] for pair in pairs}
    assert {"orig_reg", "sic_corr", "abbr_expan"} <= ids
    for pair in pairs:
        assert pair["first"]
        assert pair["second"]
        assert pair["label"]


# -- 1. Grouper en choix -------------------------------------------------------


def test_group_as_choice_resultat_texte_exact() -> None:
    text = "<p>ung</p>"
    start = text.index("ung")
    end = start + len("ung")
    edits, cursor = plan_group_as_choice(start, end, "orig", "reg")
    result = apply_edits_to_text(text, edits)
    assert result == "<p><choice><orig>ung</orig><reg></reg></choice></p>"
    assert result[:cursor].endswith("<reg>")
    assert result[cursor:].startswith("</reg>")


def test_group_as_choice_ne_touche_rien_hors_zone() -> None:
    text = "<p>avant ung après</p>"
    start = text.index("ung")
    end = start + len("ung")
    edits, _cursor = plan_group_as_choice(start, end, "sic", "corr")
    before, after = unaffected_text_outside(text, edits)
    result = apply_edits_to_text(text, edits)
    assert result.startswith(before)
    assert result.endswith(after)
    assert before == text[:start]
    assert after == text[end:]


def test_group_as_choice_un_seul_undo(qapp) -> None:
    text = "<p>ung</p>"
    start = text.index("ung")
    end = start + len("ung")
    edits, _cursor = plan_group_as_choice(start, end, "orig", "reg")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<p><choice><orig>ung</orig><reg></reg></choice></p>"


# -- 2. Insérer une liste de personnages ---------------------------------------


def test_insert_cast_list_resultat_texte_exact() -> None:
    text = "<front></front>"
    offset = text.index("</front>")
    edits, cursor = plan_insert_cast_list(offset, 2)
    result = apply_edits_to_text(text, edits)
    assert result == (
        "<front><castList><castItem><role></role></castItem>"
        "<castItem><role></role></castItem></castList></front>"
    )
    assert result[:cursor].endswith("<role>")
    assert result[cursor:].startswith("</role>")


def test_insert_cast_list_au_moins_un_role() -> None:
    text = "<front></front>"
    offset = text.index("</front>")
    edits, _cursor = plan_insert_cast_list(offset, 0)
    result = apply_edits_to_text(text, edits)
    assert result.count("<castItem>") == 1


def test_insert_cast_list_un_seul_undo(qapp) -> None:
    text = "<front></front>"
    offset = text.index("</front>")
    edits, _cursor = plan_insert_cast_list(offset, 3)
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited.count("<castItem>") == 3


# -- 3. Marquer un vers partagé ------------------------------------------------

_SHARED_VERSE_TEXT = (
    '<div><sp><speaker>A</speaker><l n="1">Hello world</l></sp>'
    "<sp><speaker>B</speaker></sp></div>"
)


def _shared_verse_offsets(text: str):
    l_span = _span_for(text, "l")
    speaker_b_span = None
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    sp_elements = [el for el in root.iter() if el.tag == "sp"]
    second_sp = sp_elements[1]
    for child in second_sp:
        if child.tag == "speaker":
            speaker_b_span = spans[id(child)]
            break
    split_offset = text.index("world")
    insert_offset = speaker_b_span.end_tag_end
    return l_span, split_offset, insert_offset


def test_mark_shared_verse_resultat_texte_exact() -> None:
    text = _SHARED_VERSE_TEXT
    l_span, split_offset, insert_offset = _shared_verse_offsets(text)
    edits = plan_mark_shared_verse(text, l_span, split_offset, insert_offset, "1")
    result = apply_edits_to_text(text, edits)
    assert result == (
        '<div><sp><speaker>A</speaker><l n="1" part="I">Hello </l></sp>'
        '<sp><speaker>B</speaker><l n="1" part="F">world</l></sp></div>'
    )


def test_mark_shared_verse_rejette_une_position_hors_contenu() -> None:
    text = _SHARED_VERSE_TEXT
    l_span, _split_offset, insert_offset = _shared_verse_offsets(text)
    try:
        plan_mark_shared_verse(text, l_span, l_span.start_tag_start, insert_offset, "1")
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError attendue pour une position hors du contenu du <l>")


def test_mark_shared_verse_un_seul_undo(qapp) -> None:
    text = _SHARED_VERSE_TEXT
    l_span, split_offset, insert_offset = _shared_verse_offsets(text)
    edits = plan_mark_shared_verse(text, l_span, split_offset, insert_offset, "1")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert 'part="I"' in edited and 'part="F"' in edited


# -- 4. Insérer une leçon (app/lem/rdg) ----------------------------------------


def test_insert_apparatus_resultat_texte_exact() -> None:
    text = "<p>bonjour</p>"
    start = text.index("bonjour")
    end = start + len("bonjour")
    edits, cursor = plan_insert_apparatus(start, end, 2)
    result = apply_edits_to_text(text, edits)
    assert result == "<p><app><lem>bonjour</lem><rdg></rdg><rdg></rdg></app></p>"
    assert result[:cursor].endswith("<rdg>")
    assert result[cursor:].startswith("</rdg>")


def test_insert_apparatus_ne_touche_rien_hors_zone() -> None:
    text = "<p>avant bonjour après</p>"
    start = text.index("bonjour")
    end = start + len("bonjour")
    edits, _cursor = plan_insert_apparatus(start, end, 1)
    before, after = unaffected_text_outside(text, edits)
    result = apply_edits_to_text(text, edits)
    assert result.startswith(before)
    assert result.endswith(after)
    assert before == text[:start]
    assert after == text[end:]


def test_insert_apparatus_un_seul_undo(qapp) -> None:
    text = "<p>bonjour</p>"
    start = text.index("bonjour")
    end = start + len("bonjour")
    edits, _cursor = plan_insert_apparatus(start, end, 2)
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<p><app><lem>bonjour</lem><rdg></rdg><rdg></rdg></app></p>"
