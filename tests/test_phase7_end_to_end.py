"""Test de bout en bout de la phase 7 (`docs/ROADMAP.md` §5, phase 7) :
« un acte de théâtre et une page d'édition critique saisis avec les
seuls outils graphiques, valides ».

Conformément à la consigne de cette phase, ce module construit les deux
documents **en n'appelant que les fonctions publiques** des opérations
génériques de la phase 5 (`editor.structured_edits`) et des commandes
composites de cette phase (`editor.snippets`) — jamais en écrivant du
XML à la main. Les seules exceptions sont : le modèle minimal de départ
(`NEW_DOCUMENT_TEMPLATE`, déjà la base de « Nouveau » depuis la phase 3)
et l'insertion de texte brut (taper du texte dans un élément vide n'est
pas une opération structurée — c'est la saisie de base, toujours
disponible, pas une fonctionnalité de cette phase).

Chaque document obtenu est ensuite validé contre le schéma RelaxNG
unique `tei_all` (`editor.diagnostics.validate_relaxng`, ADR-0007) :
le critère d'acceptation est zéro diagnostic d'erreur."""

from __future__ import annotations

from lxml import etree

from tei_editor.editor.current_element import locate_current_element, local_name
from tei_editor.editor.diagnostics import validate_relaxng
from tei_editor.editor.snippets import (
    plan_group_as_choice,
    plan_insert_apparatus,
    plan_insert_cast_list,
    plan_mark_shared_verse,
)
from tei_editor.editor.structured_edits import (
    apply_edits_to_text,
    plan_insert_element,
    plan_set_attribute,
    plan_unwrap,
)
from tei_editor.editor.text_editor import NEW_DOCUMENT_TEMPLATE


# -- Petites aides de test (pas de production) --------------------------------
#
# Reproduisent, sans Qt, ce que fait un vrai curseur Qt entre deux
# commandes structurées : suivre le déplacement d'une position de
# référence quand une édition antérieure change la longueur du texte.
# `editor.snippet_commands_mixin`/`editor.tag_commands_mixin` font
# l'équivalent avec un `QTextCursor` réel ; ici on le fait à la main pour
# rester testable sans interface graphique (`CLAUDE.md`).


def _apply_and_track(text: str, edits: list, cursor: int) -> tuple[str, int]:
    delta = 0
    for edit in edits:
        if edit.start <= cursor:
            delta += len(edit.replacement) - (edit.end - edit.start)
    return apply_edits_to_text(text, edits), cursor + delta


def _insert_text(text: str, offset: int, snippet: str) -> tuple[str, int]:
    return text[:offset] + snippet + text[offset:], offset + len(snippet)


def _insert_element(text: str, offset: int, name: str, attrs: dict | None = None):
    edits, cursor = plan_insert_element(offset, name, self_closing=False)
    text = apply_edits_to_text(text, edits)
    located = locate_current_element(text, cursor)
    assert located is not None and local_name(located.element.tag) == name
    for attr_name, value in (attrs or {}).items():
        attr_edits = plan_set_attribute(text, located.span, attr_name, value)
        text, cursor = _apply_and_track(text, attr_edits, cursor)
        located = locate_current_element(text, cursor)
    return text, cursor, located


def _assert_valid_tei_all(text: str) -> None:
    root = etree.fromstring(text.encode("utf-8"))
    diagnostics = validate_relaxng(root)
    assert diagnostics == [], f"Document non valide RelaxNG (tei_all) : {diagnostics}"


# -- 1. Un acte de théâtre : distribution, répliques, vers partagé -----------


def test_acte_de_theatre_construit_avec_les_outils_graphiques_est_valide() -> None:
    text = NEW_DOCUMENT_TEMPLATE

    # Dégroupe le <p> placeholder du corps (opération générique phase 5).
    p_offset = text.index("<p></p>")
    located = locate_current_element(text, p_offset + len("<p>"))
    assert located is not None and local_name(located.element.tag) == "p"
    text = apply_edits_to_text(text, plan_unwrap(located.span))

    # <front><castList>...</castList></front> : liste de personnages
    # (commande composite phase 7), <front> frère de <body> sous <text>.
    body_open = text.index("<body>")
    text, cursor, _located = _insert_element(text, body_open, "front")
    edits, cursor = plan_insert_cast_list(cursor, 2)
    text = apply_edits_to_text(text, edits)
    text, cursor = _insert_text(text, cursor, "Le Roi")
    second_role_open = text.index("<role>", cursor) + len("<role>")
    text, _cursor = _insert_text(text, second_role_open, "La Reine")

    # <div type="act"><div type="scene"> (opérations génériques phase 5).
    offset = text.index("<body>") + len("<body>")
    text, cursor, act_located = _insert_element(text, offset, "div", {"type": "act", "n": "1"})
    offset = act_located.span.content_start
    text, cursor, scene_located = _insert_element(text, offset, "div", {"type": "scene", "n": "1"})
    offset = scene_located.span.content_start

    # Première réplique : speaker + un vers.
    text, sp1_cursor, _sp1_located = _insert_element(text, offset, "sp")
    text, cursor, _speaker1_located = _insert_element(text, sp1_cursor, "speaker")
    text, cursor = _insert_text(text, cursor, "LE ROI.")
    speaker1_located = locate_current_element(text, cursor)
    text, cursor, l1_located = _insert_element(
        text, speaker1_located.span.end_tag_end, "l", {"n": "1"}
    )
    text, cursor = _insert_text(text, l1_located.span.content_start, "Allons, partons sur")

    # Seconde réplique : speaker seul pour l'instant.
    sp1_end = text.index("</sp>", cursor) + len("</sp>")
    text, sp2_cursor, _sp2_located = _insert_element(text, sp1_end, "sp")
    text, cursor, _speaker2_located = _insert_element(text, sp2_cursor, "speaker")
    text, cursor = _insert_text(text, cursor, "LA REINE.")
    speaker2_located = locate_current_element(text, cursor)

    # « Marquer un vers partagé » (commande composite phase 7) : scinde le
    # vers n°1 entre les deux répliques, @part="I"/"F", même @n.
    l1_open = text.index('<l n="1">')
    l1_located = locate_current_element(text, l1_open + len('<l n="1">') + 1)
    assert local_name(l1_located.element.tag) == "l"
    split_offset = text.index("sur", l1_located.span.content_start) + len("sur")
    insert_offset = speaker2_located.span.end_tag_end
    edits = plan_mark_shared_verse(text, l1_located.span, split_offset, insert_offset, "1")
    text = apply_edits_to_text(text, edits)

    assert '<l n="1" part="I">Allons, partons sur</l>' in text
    assert '<l n="1" part="F">' in text

    # Un second vers dans la réplique de la Reine, avec une leçon
    # d'apparat (commande composite phase 7).
    speaker2_again = locate_current_element(text, text.index("LA REINE.") + 1)
    sp2_element = speaker2_again.element.getparent()
    assert local_name(sp2_element.tag) == "sp"
    sp2_span = speaker2_again.span_of(sp2_element)
    text, cursor, l2_located = _insert_element(text, sp2_span.end_tag_start, "l", {"n": "2"})
    selection = "le trône"
    text, _cursor = _insert_text(text, l2_located.span.content_start, selection)
    sel_start = l2_located.span.content_start
    sel_end = sel_start + len(selection)
    edits, _cursor_pos = plan_insert_apparatus(sel_start, sel_end, 1)
    text = apply_edits_to_text(text, edits)

    assert "<app><lem>le trône</lem><rdg></rdg></app>" in text
    _assert_valid_tei_all(text)


# -- 2. Une page d'édition critique : listWit + plusieurs app/lem/rdg -------


def test_page_edition_critique_construite_avec_les_outils_graphiques_est_valide() -> None:
    text = NEW_DOCUMENT_TEMPLATE

    # Dégroupe le <p> placeholder de sourceDesc, insère <listWit> avec deux
    # témoins (opérations génériques phase 5 : dégrouper, insérer,
    # attribut xml:id).
    source_p_offset = text.index("<p>", text.index("<sourceDesc>"))
    located = locate_current_element(text, source_p_offset + len("<p>"))
    assert located is not None and local_name(located.element.tag) == "p"
    text = apply_edits_to_text(text, plan_unwrap(located.span))

    source_desc_open = text.index("<sourceDesc>") + len("<sourceDesc>")
    text, cursor, _listwit_located = _insert_element(text, source_desc_open, "listWit")
    for xml_id, label in (("A", "Témoin A (1670)"), ("B", "Témoin B (1676)")):
        text, cursor, witness_located = _insert_element(text, cursor, "witness", {"xml:id": xml_id})
        text, cursor = _insert_text(text, witness_located.span.content_start, label)
        witness_located = locate_current_element(text, cursor)
        cursor = witness_located.span.end_tag_end
    # Le texte résiduel du <p> dégroupé (hors balises) n'est plus utile une
    # fois remplacé par la liste de témoins structurée : le retirer est une
    # édition de texte ordinaire (pas une opération structurée).
    listwit_end = text.index("</listWit>") + len("</listWit>")
    source_desc_close = text.index("</sourceDesc>")
    text = text[:listwit_end] + text[source_desc_close:]

    # Premier <p> du corps : une leçon d'apparat (commande composite).
    body_p_offset = text.index("<p></p>", text.index("<body>"))
    located = locate_current_element(text, body_p_offset + len("<p>"))
    assert local_name(located.element.tag) == "p"
    text, _cursor = _insert_text(text, located.span.content_start, "Il vit paraistre le jour.")
    located = locate_current_element(text, located.span.content_start + 1)
    selection = "paraistre"
    sel_start = text.index(selection, located.span.content_start)
    sel_end = sel_start + len(selection)
    edits, cursor_pos = plan_insert_apparatus(sel_start, sel_end, 1)
    text = apply_edits_to_text(text, edits)

    # @wit sur lem/rdg via l'inspecteur d'attributs (opération générique).
    rdg_located = locate_current_element(text, cursor_pos)
    assert local_name(rdg_located.element.tag) == "rdg"
    text = apply_edits_to_text(text, plan_set_attribute(text, rdg_located.span, "wit", "#B"))
    lem_offset = text.index("<lem>") + len("<lem>")
    lem_located = locate_current_element(text, lem_offset + 1)
    assert local_name(lem_located.element.tag) == "lem"
    text = apply_edits_to_text(text, plan_set_attribute(text, lem_located.span, "wit", "#A"))

    assert '<lem wit="#A">paraistre</lem><rdg wit="#B"></rdg>' in text

    # Second <p> du corps : normalisation via « Grouper en choix… »
    # (commande composite, paire sic/corr).
    body_p1_close = text.index("</p>", text.index("<body>"))
    offset = body_p1_close + len("</p>")
    text, cursor, _p2_located = _insert_element(text, offset, "p")
    text, cursor = _insert_text(text, cursor, "Il voit le jour clairement.")
    sel2_start = text.index("voit")
    sel2_end = sel2_start + len("voit")
    edits, cursor_pos2 = plan_group_as_choice(sel2_start, sel2_end, "sic", "corr")
    text = apply_edits_to_text(text, edits)
    text, _cursor = _insert_text(text, cursor_pos2, "voit")

    assert "<choice><sic>voit</sic><corr>voit</corr></choice>" in text
    _assert_valid_tei_all(text)
