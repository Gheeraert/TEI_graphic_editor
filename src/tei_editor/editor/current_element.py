"""Repérage de l'élément XML courant à une position de curseur, avec les
bornes textuelles exactes de ses balises ouvrante/fermante.

Phase 5 (`docs/ROADMAP.md` §5) : les opérations d'édition structurée
(envelopper, dégrouper, renommer, scinder/fusionner, inspecteur,
génération de ``xml:id``) ont besoin de savoir sur quel élément elles
agissent. Ce module généralise, pour cet usage, le **même** principe de
repérage par positions déjà utilisé par `editor/xpath.py` (ADR-0007
§3) : un seul balayage du texte, les balises ouvrantes/auto-fermantes
appariées 1 pour 1, dans l'ordre du document, aux éléments réels de
l'arbre ``lxml`` — pas un second algorithme. `xpath.py` délègue
maintenant à :func:`element_spans`/:func:`locate_current_element` pour
calculer l'élément courant et ne garde que la construction du chemin
XPath lui-même.

**Limite assumée (héritée de ADR-0007 §3, documentée ici aussi).** Un
curseur placé après la fermeture d'un élément mais avant celle de son
parent (ex. juste après ``</p>`` et avant ``</div>``) reste rattaché à
ce ``p`` déjà refermé : ``lxml`` ne donne que la ligne de *début* de
chaque élément, pas sa fin, donc rien ne permet de détecter ce retour
au parent sans réanalyser tout le flux de balises (ce que ce module
fait déjà, mais l'heuristique de « l'élément courant » reste la même
que pour le fil d'Ariane, par cohérence). Acceptable pour un indicateur
informatif ; à garder en tête pour une opération d'édition déclenchée
juste après une fermeture.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import etree

from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

#: Repère toutes les balises (ouvrantes/auto-fermantes/fermantes) ainsi
#: que les commentaires/PI/CDATA (ignorés pour l'appariement, mais il
#: faut les reconnaître pour ne pas les confondre avec une balise).
_TAG_RE = re.compile(
    r"<!--.*?-->"
    r"|<\?.*?\?>"
    r"|<!\[CDATA\[.*?\]\]>"
    r"|(?P<close></[^>]*>)"
    r"|<(?P<open>[A-Za-z_][\w.:-]*)"
    r"(?:[^<>\"']|\"[^\"]*\"|'[^']*')*?"
    r"(?P<selfclose>/)?>",
    re.DOTALL,
)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[1] if isinstance(tag, str) and "}" in tag else (tag or "")


def real_elements_in_document_order(root: etree._Element) -> list[etree._Element]:
    return [el for el in root.iter() if isinstance(el.tag, str)]


_XML_ID_ATTR = "{http://www.w3.org/XML/1998/namespace}id"


def all_xml_ids(root: etree._Element) -> set[str]:
    """Tous les ``xml:id`` déjà présents dans ``root`` (génération d'un
    nouvel identifiant garanti unique, phase 5 point 8)."""
    return {el.get(_XML_ID_ATTR) for el in root.iter() if el.get(_XML_ID_ATTR)}


@dataclass
class ElementSpan:
    """Bornes textuelles exactes d'un élément dans le texte source.

    ``end_tag_start``/``end_tag_end`` sont ``None`` pour un élément
    auto-fermant (pas de balise fermante, pas de contenu possible)."""

    element: etree._Element
    start_tag_start: int
    start_tag_end: int
    self_closing: bool
    end_tag_start: int | None = None
    end_tag_end: int | None = None

    @property
    def content_start(self) -> int:
        return self.start_tag_end

    @property
    def content_end(self) -> int:
        return self.end_tag_start if self.end_tag_start is not None else self.start_tag_end


def element_spans(root: etree._Element, text: str) -> dict[int, ElementSpan]:
    """Calcule les :class:`ElementSpan` de tous les éléments réels de
    ``root``, à partir d'un seul balayage de ``text``. Clef : ``id()``
    de l'élément lxml (stable pendant la durée de vie de l'arbre)."""
    elements_iter = iter(real_elements_in_document_order(root))
    spans: dict[int, ElementSpan] = {}
    stack: list[ElementSpan] = []
    for match in _TAG_RE.finditer(text):
        if match.group("open") is not None:
            try:
                element = next(elements_iter)
            except StopIteration:
                continue
            span = ElementSpan(
                element=element,
                start_tag_start=match.start(),
                start_tag_end=match.end(),
                self_closing=match.group("selfclose") is not None,
            )
            spans[id(element)] = span
            if not span.self_closing:
                stack.append(span)
        elif match.group("close") is not None:
            if stack:
                span = stack.pop()
                span.end_tag_start = match.start()
                span.end_tag_end = match.end()
        # commentaires/PI/CDATA : ignorés.
    return spans


@dataclass
class CurrentElement:
    """Élément courant repéré à une position de curseur, avec la carte
    complète des bornes de tous les éléments du document (pour accéder
    aux bornes d'un parent/frère sans refaire le balayage)."""

    element: etree._Element
    span: ElementSpan
    spans: dict[int, ElementSpan]

    def span_of(self, other: etree._Element | None) -> ElementSpan | None:
        if other is None:
            return None
        return self.spans.get(id(other))


def locate_current_element(text: str, offset: int) -> CurrentElement | None:
    """Repère l'élément courant à ``offset`` dans ``text`` : le dernier
    élément, dans l'ordre du document, dont la balise ouvrante est
    entièrement refermée avant ou à ``offset`` (même heuristique que
    `editor/xpath.py`, ADR-0007 §3). Renvoie ``None`` si le document est
    mal formé, ou si ``offset`` est avant le premier élément (pas
    d'élément courant, seulement la racine absente)."""
    try:
        root = parse_xml_safely(text)
    except UnsafeXmlError:
        return None
    offset = max(0, min(offset, len(text)))
    spans = element_spans(root, text)
    elements = real_elements_in_document_order(root)
    if not elements:
        return None
    root_span = spans.get(id(elements[0]))
    if root_span is not None and root_span.end_tag_end is not None and offset > root_span.end_tag_end:
        # Curseur après la fermeture de la racine : plus aucun élément
        # courant (même convention que l'ancien `xpath.py`, phase 3/4).
        return None
    current: etree._Element | None = None
    for element in elements:
        span = spans.get(id(element))
        if span is None or span.self_closing:
            continue
        if span.start_tag_end <= offset:
            current = element
        else:
            break
    if current is None:
        return None
    return CurrentElement(element=current, span=spans[id(current)], spans=spans)
