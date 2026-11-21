"""Commandes composites de la phase 7 (`docs/ROADMAP.md` §5, phase 7) :
« Grouper en choix… », « Insérer une liste de personnages… », « Marquer
un vers partagé », « Insérer une leçon (app/lem/rdg)… ».

Même esprit que `editor/structured_edits.py` (phase 5, ADR-0008) : chaque
opération est une fonction de planification pure (``plan_*``), testable
sans Qt, qui renvoie une liste de :class:`tei_editor.editor.structured_edits.TextEdit`
(plus, pour les insertions, la position de curseur souhaitée après
l'opération). L'exécution reste celle de la phase 5
(:func:`tei_editor.editor.structured_edits.apply_edits_with_cursor`) : un
seul bloc d'annulation natif par opération, pas un second mécanisme.

Les paires ``choice`` (``orig``/``reg``, ``sic``/``corr``,
``abbr``/``expan``) sont lues depuis
`data/snippets/choice_pairs.json`, pas codées en dur dans le widget
(``CLAUDE.md`` : « le catalogue fait foi, ne jamais coder de liste de
balises en dur » — ici une petite donnée JSON documentée, au même titre
que les profils, plutôt qu'une liste Python)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import quoteattr

from tei_editor.editor.current_element import ElementSpan
from tei_editor.editor.structured_edits import TextEdit, plan_set_attribute

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHOICE_PAIRS_PATH = DATA_DIR / "snippets" / "choice_pairs.json"


@lru_cache(maxsize=1)
def load_choice_pairs() -> list[dict]:
    """Charge les paires ``choice`` (``orig``/``reg``, ``sic``/``corr``,
    ``abbr``/``expan``) depuis `data/snippets/choice_pairs.json`. Renvoie
    une liste vide (sans lever) si le fichier est absent."""
    try:
        data = json.loads(CHOICE_PAIRS_PATH.read_text(encoding="utf-8"))
    except OSError:
        return []
    return list(data.get("pairs", []))


# -- 1. Grouper en choix ------------------------------------------------------


def plan_group_as_choice(
    selection_start: int, selection_end: int, first_name: str, second_name: str
) -> tuple[list[TextEdit], int]:
    """Enveloppe la sélection en ``<choice><first>sélection</first><second>
    </second></choice>``, sans toucher à un seul caractère de la sélection
    ni du reste du document (même garantie que
    :func:`tei_editor.editor.structured_edits.plan_wrap_selection`, étendue
    à l'idiome ``choice`` à deux enfants). Renvoie le plan d'édition et la
    position de curseur après l'opération, à l'intérieur du second
    élément (vide)."""
    if selection_start > selection_end:
        selection_start, selection_end = selection_end, selection_start
    open_choice = "<choice>"
    open_first = f"<{first_name}>"
    close_first = f"</{first_name}>"
    open_second = f"<{second_name}>"
    close_second = f"</{second_name}>"
    close_choice = "</choice>"
    edits = [
        TextEdit(selection_end, selection_end, close_first + open_second + close_second + close_choice),
        TextEdit(selection_start, selection_start, open_choice + open_first),
    ]
    selection_length = selection_end - selection_start
    cursor_position = (
        selection_start
        + len(open_choice)
        + len(open_first)
        + selection_length
        + len(close_first)
        + len(open_second)
    )
    return edits, cursor_position


# -- 2. Insérer une liste de personnages --------------------------------------


def plan_insert_cast_list(offset: int, role_count: int) -> tuple[list[TextEdit], int]:
    """Insère un squelette ``castList`` avec ``role_count`` ``castItem``/
    ``role`` à ``offset``. Renvoie le plan d'édition (une seule insertion
    ponctuelle) et la position de curseur après l'opération, à l'intérieur
    du premier ``role`` (vide)."""
    role_count = max(1, role_count)
    pieces: list[str] = ["<castList>"]
    first_role_content_offset: int | None = None
    for index in range(role_count):
        item_open = "<castItem><role>"
        if index == 0:
            first_role_content_offset = sum(len(p) for p in pieces) + len(item_open)
        pieces.append(item_open)
        pieces.append("</role></castItem>")
    pieces.append("</castList>")
    text = "".join(pieces)
    assert first_role_content_offset is not None
    return [TextEdit(offset, offset, text)], offset + first_role_content_offset


# -- 3. Marquer un vers partagé ------------------------------------------------


def plan_mark_shared_verse(
    text: str,
    l_span: ElementSpan,
    split_offset: int,
    insert_offset: int,
    n_value: str,
) -> list[TextEdit]:
    """Scinde un ``<l>`` existant (``l_span``) à ``split_offset`` (une
    position à l'intérieur de son contenu) entre deux répliques voisines :
    le fragment restant dans ``l_span`` reçoit ``@part="I"`` (initial) et
    ``@n=n_value`` ; un nouveau fragment ``<l part="F" n=n_value>`` portant
    le reste du texte est inséré à ``insert_offset`` (typiquement le début
    du contenu de la réplique suivante, ``<sp>``, calculé par l'appelant
    — ce module ne connaît pas la structure ``sp``/``speaker``, seulement
    des positions textuelles, conformément à ADR-0001).

    Convention reprise de l'attribut ``@part`` standard de TEI P5
    (``att.fragmentable``, valeurs ``I``/``M``/``F`` : partie initiale/
    médiane/finale d'un élément fragmenté) et du même ``@n`` porté par les
    deux fragments d'un même vers, telle qu'observée dans des éditions
    critiques de théâtre réelles (voir `docs/AUDIT_EKDOSIS.md`) — vérifiée
    ici contre le schéma `tei_all` (``l/@part`` fait bien partie de
    ``att.fragmentable``, cf. `tei_catalog.json`), pas copiée aveuglément.

    Réutilise :func:`tei_editor.editor.structured_edits.plan_set_attribute`
    (opération générique de la phase 5) pour les deux attributs plutôt que
    de réécrire la balise ouvrante à la main."""
    if not (l_span.content_start <= split_offset <= l_span.content_end):
        raise ValueError("split_offset doit être à l'intérieur du contenu du <l> à scinder")
    if l_span.end_tag_start is None or l_span.end_tag_end is None:
        raise ValueError("l_span doit avoir une balise fermante (pas auto-fermant)")

    remainder = text[split_offset : l_span.content_end]
    edits: list[TextEdit] = [TextEdit(split_offset, l_span.content_end, "")]
    edits.extend(plan_set_attribute(text, l_span, "part", "I"))
    edits.extend(plan_set_attribute(text, l_span, "n", n_value))
    new_fragment = f"<l n={quoteattr(n_value)} part=\"F\">{remainder}</l>"
    edits.append(TextEdit(insert_offset, insert_offset, new_fragment))
    return edits


# -- 4. Insérer une leçon (app/lem/rdg) ---------------------------------------


def plan_insert_apparatus(
    selection_start: int, selection_end: int, rdg_count: int
) -> tuple[list[TextEdit], int]:
    """Enveloppe la sélection (le texte de la leçon retenue) en
    ``<app><lem>sélection</lem><rdg></rdg>...<rdg></rdg></app>``, avec
    ``rdg_count`` leçons rejetées vides. L'attribut ``@wit`` (facultatif
    sur ``lem``/``rdg``, ``tei_catalog.json``) n'est pas pré-rempli ici :
    l'utilisateur le renseigne ensuite avec l'inspecteur d'attributs
    (opération générique de la phase 5), plutôt qu'une valeur fictive
    insérée par cette commande. Renvoie le plan d'édition et la position
    de curseur après l'opération, à l'intérieur du premier ``rdg``
    (vide)."""
    rdg_count = max(1, rdg_count)
    if selection_start > selection_end:
        selection_start, selection_end = selection_end, selection_start
    suffix_pieces: list[str] = ["</lem>"]
    first_rdg_content_offset: int | None = None
    for index in range(rdg_count):
        rdg_open = "<rdg>"
        if index == 0:
            first_rdg_content_offset = sum(len(p) for p in suffix_pieces) + len(rdg_open)
        suffix_pieces.append(rdg_open)
        suffix_pieces.append("</rdg>")
    suffix_pieces.append("</app>")
    suffix = "".join(suffix_pieces)
    edits = [
        TextEdit(selection_end, selection_end, suffix),
        TextEdit(selection_start, selection_start, "<app><lem>"),
    ]
    selection_length = selection_end - selection_start
    assert first_rdg_content_offset is not None
    cursor_position = (
        selection_start + len("<app><lem>") + selection_length + first_rdg_content_offset
    )
    return edits, cursor_position
