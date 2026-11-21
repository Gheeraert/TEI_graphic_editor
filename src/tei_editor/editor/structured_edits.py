"""Opérations d'édition structurée de la phase 5 (`docs/ROADMAP.md` §5) :
envelopper la sélection, insérer avec fermeture automatique, dégrouper,
renommer, scinder/fusionner un paragraphe, modifier un attribut,
générer un ``xml:id``.

Conformément à ADR-0001, aucune de ces opérations ne re-sérialise le
document : chacune calcule une petite liste de modifications
textuelles **ponctuelles** (:class:`TextEdit`, des plages
``[start, end)`` remplacées par du texte), appliquées ensuite par
:func:`apply_edits_with_cursor` entre ``QTextCursor.beginEditBlock()``/
``endEditBlock()`` sur le **même** curseur réutilisé pour toutes les
insertions/suppressions de l'opération — c'est le mécanisme standard Qt
qui fait que l'opération entière se défait en un seul « Annuler »
(suite logique d'ADR-0006 §undo, voir `docs/DECISIONS.md`/consigne de
cette phase ; pas un ``QUndoStack`` séparé, qui dupliquerait l'état déjà
porté par ``QTextDocument``).

La fonction de planification de chaque opération (``plan_*``) est pure
Python, testable sans Qt (`CLAUDE.md`) : elle prend le texte courant et
des positions/éléments, et renvoie une liste de :class:`TextEdit` (plus,
pour les insertions, la position de curseur souhaitée après
l'opération). :func:`apply_edits_to_text` permet de vérifier le résultat
textuel exact dans les tests sans passer par Qt du tout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.sax.saxutils import quoteattr

from tei_editor.editor.current_element import ElementSpan

_OPEN_TAG_NAME_RE = re.compile(r"^<([A-Za-z_][\w.:-]*)")
_CLOSE_TAG_NAME_RE = re.compile(r"^</\s*[A-Za-z_][\w.:-]*")


@dataclass(frozen=True)
class TextEdit:
    """Une modification textuelle ponctuelle : remplace ``text[start:end]``
    par ``replacement`` (``start == end`` pour une insertion pure)."""

    start: int
    end: int
    replacement: str


# -- Application (testable sans Qt, et réutilisée par l'exécuteur Qt) -------


def apply_edits_to_text(text: str, edits: list[TextEdit]) -> str:
    """Applique ``edits`` à ``text`` et renvoie le nouveau texte. Les
    plages ne doivent pas se recouvrir (chaque opération de cette phase
    ne produit que des points de modification disjoints). Utilisé par
    les tests pour vérifier le résultat sans Qt ; l'exécuteur Qt
    applique les mêmes plans sur un ``QTextCursor``."""
    for edit in edits:
        if edit.start > edit.end:
            raise ValueError(f"plage invalide : {edit}")
    ordered = sorted(edits, key=lambda e: e.start, reverse=True)
    result = text
    previous_start = len(text) + 1
    for edit in ordered:
        if edit.end > previous_start:
            raise ValueError(f"plages d'édition qui se recouvrent : {edit}")
        result = result[: edit.start] + edit.replacement + result[edit.end :]
        previous_start = edit.start
    return result


def unaffected_text_outside(text: str, edits: list[TextEdit]) -> tuple[str, str]:
    """Aide de test : renvoie ``(avant, après)`` = le texte situé
    strictement avant la plus petite borne touchée et strictement après
    la plus grande, pour vérifier qu'une opération ne modifie rien hors
    de sa zone visée (critère d'acceptation central de la phase)."""
    if not edits:
        return text, ""
    low = min(e.start for e in edits)
    high = max(e.end for e in edits)
    return text[:low], text[high:]


# -- 2. Envelopper la sélection ----------------------------------------------


def plan_wrap_selection(selection_start: int, selection_end: int, element_name: str) -> list[TextEdit]:
    """Insère ``<element_name>`` juste avant ``selection_start`` et
    ``</element_name>`` juste après ``selection_end``, sans toucher à un
    seul caractère de la sélection elle-même ni du reste du document."""
    if selection_start > selection_end:
        selection_start, selection_end = selection_end, selection_start
    return [
        TextEdit(selection_end, selection_end, f"</{element_name}>"),
        TextEdit(selection_start, selection_start, f"<{element_name}>"),
    ]


# -- 3. Insertion avec fermeture automatique ---------------------------------


def plan_insert_element(offset: int, element_name: str, *, self_closing: bool) -> tuple[list[TextEdit], int]:
    """Insère ``<element_name/>`` (élément typiquement vide) ou
    ``<element_name></element_name>`` à ``offset``. Renvoie le plan
    d'édition et la position de curseur après l'opération (entre les
    deux balises pour le cas non auto-fermant, après la balise pour le
    cas auto-fermant)."""
    if self_closing:
        text = f"<{element_name}/>"
        return [TextEdit(offset, offset, text)], offset + len(text)
    open_tag = f"<{element_name}>"
    close_tag = f"</{element_name}>"
    return [TextEdit(offset, offset, open_tag + close_tag)], offset + len(open_tag)


# -- 4. Dégrouper (unwrap) ----------------------------------------------------


def plan_unwrap(span: ElementSpan) -> list[TextEdit] | None:
    """Supprime la balise ouvrante et la balise fermante de l'élément,
    en laissant son contenu intact. ``None`` si l'élément est
    auto-fermant (pas de contenu, pas de balise fermante à retirer) :
    l'appelant doit alors désactiver l'action plutôt que d'échouer."""
    if span.end_tag_start is None or span.end_tag_end is None:
        return None
    return [
        TextEdit(span.end_tag_start, span.end_tag_end, ""),
        TextEdit(span.start_tag_start, span.start_tag_end, ""),
    ]


# -- 5. Renommer la balise ----------------------------------------------------


def plan_rename(text: str, span: ElementSpan, new_name: str) -> list[TextEdit]:
    """Remplace uniquement le nom de l'élément dans sa balise ouvrante
    (et sa balise fermante si elle existe), en conservant tel quel tout
    le reste de la balise ouvrante (attributs, espaces, ordre)."""
    open_text = text[span.start_tag_start : span.start_tag_end]
    match = _OPEN_TAG_NAME_RE.match(open_text)
    if not match:
        return []
    new_open = "<" + new_name + open_text[match.end() :]
    edits = [TextEdit(span.start_tag_start, span.start_tag_end, new_open)]
    if span.end_tag_start is not None and span.end_tag_end is not None:
        close_text = text[span.end_tag_start : span.end_tag_end]
        new_close = _CLOSE_TAG_NAME_RE.sub(f"</{new_name}", close_text, count=1)
        edits.append(TextEdit(span.end_tag_start, span.end_tag_end, new_close))
    return edits


# -- 6. Scinder / fusionner un paragraphe ------------------------------------


def can_split_paragraph(span: ElementSpan, offset: int) -> bool:
    """Le curseur doit être strictement à l'intérieur du contenu de
    l'élément (pas sur ses balises elles-mêmes), et l'élément doit avoir
    une balise fermante (pas auto-fermant)."""
    if span.end_tag_start is None:
        return False
    return span.content_start <= offset <= span.content_end


def plan_split_paragraph(offset: int, element_name: str = "p") -> list[TextEdit]:
    """Ferme l'élément courant à ``offset`` et en rouvre un nouveau juste
    après, pour le reste du contenu."""
    return [TextEdit(offset, offset, f"</{element_name}>" + f"<{element_name}>")]


def can_merge_paragraphs(first_span: ElementSpan, second_element_name: str, first_element_name: str) -> bool:
    return (
        first_span.end_tag_start is not None
        and first_element_name == second_element_name
    )


def plan_merge_paragraphs(first_span: ElementSpan, second_span: ElementSpan) -> list[TextEdit]:
    """Supprime la balise fermante du premier paragraphe et la balise
    ouvrante du second, pour n'en laisser qu'un. Ne touche à rien
    d'autre (pas même l'espace/le saut de ligne entre les deux balises,
    conservé tel quel dans le paragraphe fusionné)."""
    if first_span.end_tag_start is None or first_span.end_tag_end is None:
        raise ValueError("le premier paragraphe doit avoir une balise fermante")
    return [
        TextEdit(second_span.start_tag_start, second_span.start_tag_end, ""),
        TextEdit(first_span.end_tag_start, first_span.end_tag_end, ""),
    ]


# -- 7. Attributs (inspecteur) ------------------------------------------------


def _attribute_pattern(attr_name: str) -> re.Pattern:
    return re.compile(
        r"(?P<lead>\s+)" + re.escape(attr_name) + r'(?P<ns>\s*=\s*)(?P<quote>"[^"]*"|\'[^\']*\')',
        re.DOTALL,
    )


def plan_set_attribute(text: str, span: ElementSpan, attr_name: str, new_value: str) -> list[TextEdit]:
    """Réécrit uniquement la valeur de ``attr_name`` dans la balise
    ouvrante de ``span`` (l'ajoute si absent), sans toucher au reste de
    la balise ni du document."""
    open_text = text[span.start_tag_start : span.start_tag_end]
    match = _attribute_pattern(attr_name).search(open_text)
    quoted = quoteattr(new_value)
    if match:
        abs_start = span.start_tag_start + match.start("quote")
        abs_end = span.start_tag_start + match.end("quote")
        return [TextEdit(abs_start, abs_end, quoted)]
    insert_pos = span.start_tag_end - (2 if open_text.endswith("/>") else 1)
    return [TextEdit(insert_pos, insert_pos, f" {attr_name}={quoted}")]


def plan_remove_attribute(text: str, span: ElementSpan, attr_name: str) -> list[TextEdit]:
    """Retire ``attr_name`` (et l'espace qui le précède) de la balise
    ouvrante de ``span``. Liste vide si l'attribut est déjà absent."""
    open_text = text[span.start_tag_start : span.start_tag_end]
    match = _attribute_pattern(attr_name).search(open_text)
    if not match:
        return []
    abs_start = span.start_tag_start + match.start()
    abs_end = span.start_tag_start + match.end()
    return [TextEdit(abs_start, abs_end, "")]


# -- 8. Génération de xml:id --------------------------------------------------


def generate_unique_xml_id(element_name: str, existing_ids: set[str]) -> str:
    """Génère un ``xml:id`` basé sur ``element_name`` (``p-1``,
    ``div-3``...), garanti absent de ``existing_ids``."""
    index = 1
    while True:
        candidate = f"{element_name}-{index}"
        if candidate not in existing_ids:
            return candidate
        index += 1


def plan_set_xml_id(text: str, span: ElementSpan, xml_id: str) -> list[TextEdit]:
    """Insère ``xml:id="..."`` dans la balise ouvrante de ``span``. Ne
    vérifie pas l'absence préalable (fait par l'appelant/l'inspecteur,
    qui désactive l'action quand un ``xml:id`` existe déjà)."""
    return plan_set_attribute(text, span, "xml:id", xml_id)


# -- Exécution Qt (un seul bloc d'annulation) ---------------------------------


def apply_edits_with_cursor(cursor, edits: list[TextEdit], *, final_position: int | None = None) -> None:
    """Applique ``edits`` sur ``cursor`` (``QTextCursor``) entre
    ``beginEditBlock``/``endEditBlock`` : un seul pas d'annulation natif
    pour toute l'opération (suite logique d'ADR-0006 §undo — voir le
    docstring du module). Les plages sont appliquées de la plus grande
    position de départ à la plus petite, pour que les offsets déjà
    calculés des plages non encore traitées restent valides. ``cursor``
    est réutilisé tel quel pour toutes les insertions/suppressions."""
    from PySide6.QtGui import QTextCursor  # import tardif : module utilisable sans Qt pour les plans purs

    cursor.beginEditBlock()
    try:
        for edit in sorted(edits, key=lambda e: e.start, reverse=True):
            cursor.setPosition(edit.start)
            if edit.end > edit.start:
                cursor.setPosition(edit.end, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
            if edit.replacement:
                cursor.insertText(edit.replacement)
        if final_position is not None:
            cursor.setPosition(final_position)
    finally:
        cursor.endEditBlock()
