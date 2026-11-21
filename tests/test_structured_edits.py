"""Tests des opérations d'édition structurée (phase 5). Pour chaque
opération : (a) résultat textuel exact sur un cas simple, (b) le texte
hors de la zone touchée est identique avant/après, (c) un seul
« Annuler » restaure exactement le texte d'origine (critère
d'acceptation central de `docs/ROADMAP.md` §5)."""

from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from tei_editor.editor.current_element import element_spans, locate_current_element
from tei_editor.editor.structured_edits import (
    apply_edits_to_text,
    apply_edits_with_cursor,
    can_merge_paragraphs,
    can_split_paragraph,
    generate_unique_xml_id,
    plan_insert_element,
    plan_merge_paragraphs,
    plan_remove_attribute,
    plan_rename,
    plan_set_attribute,
    plan_set_xml_id,
    plan_split_paragraph,
    plan_unwrap,
    plan_wrap_selection,
    unaffected_text_outside,
)
from tei_editor.tei.xml_safety import parse_xml_safely


def _assert_single_undo_restores(qapp, original_text: str, edits) -> str:
    """Applique ``edits`` via un ``QPlainTextEdit`` réel (offscreen),
    vérifie qu'un seul ``undo()`` restaure le texte d'origine, et
    renvoie le texte obtenu après l'opération (avant annulation)."""
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


# -- 2. Envelopper la sélection ----------------------------------------------


def test_wrap_selection_result_texte_exact() -> None:
    text = "<p>Bonjour le monde</p>"
    start = text.index("le")
    end = start + len("le monde")
    edits = plan_wrap_selection(start, end, "hi")
    result = apply_edits_to_text(text, edits)
    assert result == "<p>Bonjour <hi>le monde</hi></p>"


def test_wrap_selection_ne_touche_rien_hors_zone() -> None:
    text = "<p>Bonjour le monde, vraiment</p>"
    start = text.index("le")
    end = start + len("le monde")
    edits = plan_wrap_selection(start, end, "hi")
    before, after = unaffected_text_outside(text, edits)
    result = apply_edits_to_text(text, edits)
    assert result.startswith(before)
    assert result.endswith(after)
    assert before == text[:start]
    assert after == text[end:]


def test_wrap_selection_un_seul_undo(qapp) -> None:
    text = "<p>Bonjour le monde</p>"
    start = text.index("le")
    end = start + len("le monde")
    edits = plan_wrap_selection(start, end, "hi")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<p>Bonjour <hi>le monde</hi></p>"


# -- 3. Insertion avec fermeture automatique ---------------------------------


def test_insert_element_non_autofermant_place_curseur_entre_les_balises() -> None:
    text = "<p></p>"
    offset = text.index("</p>")
    edits, new_cursor = plan_insert_element(offset, "hi", self_closing=False)
    result = apply_edits_to_text(text, edits)
    assert result == "<p><hi></hi></p>"
    assert result[new_cursor - 4 : new_cursor] == "<hi>"[-4:] or True
    assert result[:new_cursor].endswith("<hi>")
    assert result[new_cursor:].startswith("</hi>")


def test_insert_element_autofermant() -> None:
    text = "<p></p>"
    offset = text.index("</p>")
    edits, new_cursor = plan_insert_element(offset, "lb", self_closing=True)
    result = apply_edits_to_text(text, edits)
    assert result == "<p><lb/></p>"
    assert result[:new_cursor].endswith("<lb/>")


def test_insert_element_un_seul_undo(qapp) -> None:
    text = "<p></p>"
    offset = text.index("</p>")
    edits, _ = plan_insert_element(offset, "hi", self_closing=False)
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<p><hi></hi></p>"


# -- 4. Dégrouper (unwrap) ----------------------------------------------------


def _span_for(text: str, tag: str):
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    element = next(el for el in root.iter() if el.tag == tag)
    return spans[id(element)]


def test_unwrap_resultat_texte_exact() -> None:
    text = "<div><hi>contenu</hi> suite</div>"
    span = _span_for(text, "hi")
    edits = plan_unwrap(span)
    result = apply_edits_to_text(text, edits)
    assert result == "<div>contenu suite</div>"


def test_unwrap_ne_touche_rien_hors_zone() -> None:
    text = "<div><hi>contenu</hi> suite</div>"
    span = _span_for(text, "hi")
    edits = plan_unwrap(span)
    before, after = unaffected_text_outside(text, edits)
    assert before == "<div>"
    assert after == " suite</div>"


def test_unwrap_element_autofermant_renvoie_none() -> None:
    text = "<div><lb/></div>"
    span = _span_for(text, "lb")
    assert plan_unwrap(span) is None


def test_unwrap_un_seul_undo(qapp) -> None:
    text = "<div><hi>contenu</hi> suite</div>"
    span = _span_for(text, "hi")
    edits = plan_unwrap(span)
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<div>contenu suite</div>"


# -- 5. Renommer la balise ----------------------------------------------------


def test_rename_conserve_les_attributs() -> None:
    text = '<p rend="italique">texte</p>'
    span = _span_for(text, "p")
    edits = plan_rename(text, span, "ab")
    result = apply_edits_to_text(text, edits)
    assert result == '<ab rend="italique">texte</ab>'


def test_rename_ne_touche_rien_hors_zone() -> None:
    text = '<div><p rend="italique">texte</p> suite</div>'
    span = _span_for(text, "p")
    edits = plan_rename(text, span, "ab")
    before, after = unaffected_text_outside(text, edits)
    assert before.startswith("<div>")
    assert after.startswith(" suite")


def test_rename_un_seul_undo(qapp) -> None:
    text = '<p rend="italique">texte</p>'
    span = _span_for(text, "p")
    edits = plan_rename(text, span, "ab")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == '<ab rend="italique">texte</ab>'


# -- 6. Scinder / fusionner --------------------------------------------------


def test_split_paragraph_resultat_texte_exact() -> None:
    text = "<div><p>Phrase un. Phrase deux.</p></div>"
    span = _span_for(text, "p")
    offset = text.index(" Phrase deux")
    assert can_split_paragraph(span, offset)
    edits = plan_split_paragraph(offset, "p")
    result = apply_edits_to_text(text, edits)
    assert result == "<div><p>Phrase un.</p><p> Phrase deux.</p></div>"


def test_split_paragraph_un_seul_undo(qapp) -> None:
    text = "<div><p>Phrase un. Phrase deux.</p></div>"
    offset = text.index(" Phrase deux")
    edits = plan_split_paragraph(offset, "p")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<div><p>Phrase un.</p><p> Phrase deux.</p></div>"


def test_merge_paragraphs_resultat_texte_exact() -> None:
    text = "<div><p>Un.</p><p>Deux.</p></div>"
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    first, second = (el for el in root.iter() if el.tag == "p")
    first_span, second_span = spans[id(first)], spans[id(second)]
    assert can_merge_paragraphs(first_span, "p", "p")
    edits = plan_merge_paragraphs(first_span, second_span)
    result = apply_edits_to_text(text, edits)
    assert result == "<div><p>Un.Deux.</p></div>"


def test_merge_paragraphs_ne_touche_rien_hors_zone() -> None:
    text = "<div><p>Un.</p><p>Deux.</p></div>"
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    first, second = (el for el in root.iter() if el.tag == "p")
    first_span, second_span = spans[id(first)], spans[id(second)]
    edits = plan_merge_paragraphs(first_span, second_span)
    before, after = unaffected_text_outside(text, edits)
    assert before == "<div><p>Un."
    assert after == "Deux.</p></div>"


def test_merge_paragraphs_un_seul_undo(qapp) -> None:
    text = "<div><p>Un.</p><p>Deux.</p></div>"
    root = parse_xml_safely(text)
    spans = element_spans(root, text)
    first, second = (el for el in root.iter() if el.tag == "p")
    edits = plan_merge_paragraphs(spans[id(first)], spans[id(second)])
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == "<div><p>Un.Deux.</p></div>"


# -- 7. Attributs --------------------------------------------------------------


def test_set_attribute_existant_remplace_uniquement_la_valeur() -> None:
    text = '<p rend="italique" n="1">texte</p>'
    span = _span_for(text, "p")
    edits = plan_set_attribute(text, span, "rend", "gras")
    result = apply_edits_to_text(text, edits)
    assert result == '<p rend="gras" n="1">texte</p>'


def test_set_attribute_absent_est_ajoute() -> None:
    text = "<p>texte</p>"
    span = _span_for(text, "p")
    edits = plan_set_attribute(text, span, "rend", "gras")
    result = apply_edits_to_text(text, edits)
    assert result == '<p rend="gras">texte</p>'


def test_set_attribute_ne_touche_rien_hors_balise_ouvrante() -> None:
    text = '<div><p rend="italique">texte</p> suite</div>'
    span = _span_for(text, "p")
    edits = plan_set_attribute(text, span, "rend", "gras")
    before, after = unaffected_text_outside(text, edits)
    assert after.startswith(">texte</p> suite</div>")


def test_set_attribute_un_seul_undo(qapp) -> None:
    text = '<p rend="italique">texte</p>'
    span = _span_for(text, "p")
    edits = plan_set_attribute(text, span, "rend", "gras")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == '<p rend="gras">texte</p>'


def test_remove_attribute() -> None:
    text = '<p rend="italique" n="1">texte</p>'
    span = _span_for(text, "p")
    edits = plan_remove_attribute(text, span, "rend")
    result = apply_edits_to_text(text, edits)
    assert result == '<p n="1">texte</p>'


def test_remove_attribute_absent_ne_fait_rien() -> None:
    text = "<p>texte</p>"
    span = _span_for(text, "p")
    assert plan_remove_attribute(text, span, "rend") == []


def test_remove_attribute_un_seul_undo(qapp) -> None:
    text = '<p rend="italique" n="1">texte</p>'
    span = _span_for(text, "p")
    edits = plan_remove_attribute(text, span, "rend")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == '<p n="1">texte</p>'


# -- 8. Génération de xml:id --------------------------------------------------


def test_generate_unique_xml_id_simple() -> None:
    assert generate_unique_xml_id("p", set()) == "p-1"


def test_generate_unique_xml_id_evite_les_existants() -> None:
    existing = {"p-1", "p-2", "p-3"}
    assert generate_unique_xml_id("p", existing) == "p-4"


def test_generate_unique_xml_id_trous_dans_la_numerotation() -> None:
    existing = {"p-1", "p-3"}
    # p-2 est libre : la génération doit le trouver (pas seulement
    # incrémenter après le plus grand numéro existant).
    assert generate_unique_xml_id("p", existing) == "p-2"


def test_plan_set_xml_id_resultat_texte_exact() -> None:
    text = "<p>texte</p>"
    span = _span_for(text, "p")
    edits = plan_set_xml_id(text, span, "p-1")
    result = apply_edits_to_text(text, edits)
    assert result == '<p xml:id="p-1">texte</p>'


def test_plan_set_xml_id_un_seul_undo(qapp) -> None:
    text = "<p>texte</p>"
    span = _span_for(text, "p")
    edits = plan_set_xml_id(text, span, "p-1")
    edited = _assert_single_undo_restores(qapp, text, edits)
    assert edited == '<p xml:id="p-1">texte</p>'
