"""XPath courant calculé depuis une position de curseur dans le texte XML.

Phase 4 (`docs/ROADMAP.md` §5) : remplace l'approximation par balayage
regex de la phase 3 (ADR-0006 §7) par un calcul basé sur l'arbre
``lxml`` réellement analysé — la structure (imbrication, index parmi les
frères de même nom) vient de l'arbre, pas d'une pile reconstruite à la
main.

**Limite assumée (documentée aussi dans `docs/DECISIONS.md`).**
``lxml`` n'expose que la ligne de *début* de balise ouvrante de chaque
élément (``Element.sourceline``), jamais sa colonne ni sa ligne de fin.
Cette ligne seule ne suffit pas à ordonner deux éléments présents sur la
même ligne (ex. ``<a/><a>texte</a>`` sur une seule ligne). On complète
donc avec un balayage très simple (pas de pile, pas de logique
d'imbrication — l'arbre lxml s'en charge) qui ne fait que repérer, dans
l'ordre du document, la position de chaque balise ouvrante/auto-fermante,
pour l'associer à l'élément lxml correspondant. L'heuristique retenue
pour « l'élément courant » : **le dernier élément, dans l'ordre du
document, dont la balise ouvrante commence avant ou à la position du
curseur**. Un curseur placé juste après la fermeture d'un élément mais
avant la fermeture de son parent sera donc rattaché à cet élément déjà
refermé plutôt qu'à son parent (lxml ne donne pas la ligne de fin pour
détecter ce cas) — approximation jugée acceptable pour un fil d'Ariane
informatif, pas pour une opération d'édition.
"""

from __future__ import annotations

import re

from lxml import etree

from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

#: Ne repère que la fin des balises ouvrantes/auto-fermantes (pas les
#: fermantes : la fermeture est gérée par la structure de l'arbre lxml,
#: pas par ce balayage). Ignore commentaires, instructions de traitement
#: et CDATA. Un curseur n'est considéré « dans » un élément qu'une fois
#: sa balise ouvrante entièrement refermée (après son ``>``), comme pour
#: l'ancien balayage de la phase 3.
_TAG_RE = re.compile(
    r"<!--.*?-->"
    r"|<\?.*?\?>"
    r"|<!\[CDATA\[.*?\]\]>"
    r"|</[^>]*>"
    r"|<(?P<open>[A-Za-z_][\w.:-]*)"
    r"(?:[^<>\"']|\"[^\"]*\"|'[^']*')*?"
    r"(?P<selfclose>/)?>",
    re.DOTALL,
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[1] if "}" in tag else tag


def _real_elements_in_document_order(root: etree._Element) -> list[etree._Element]:
    return [el for el in root.iter() if isinstance(el.tag, str)]


def _open_tag_end_offsets(text: str, count: int) -> list[tuple[int, bool]]:
    """Renvoie, pour les ``count`` premières balises ouvrantes/auto-
    fermantes du document, la position juste après leur ``>`` et si elles
    sont auto-fermantes — dans l'ordre du document, apparié 1 pour 1 avec
    :func:`_real_elements_in_document_order` (même ordre de parcours)."""
    offsets: list[tuple[int, bool]] = []
    for match in _TAG_RE.finditer(text):
        if match.group("open") is not None:
            offsets.append((match.end(), match.group("selfclose") is not None))
            if len(offsets) >= count:
                break
    return offsets


def _sibling_index(element: etree._Element) -> int:
    parent = element.getparent()
    if parent is None:
        return 1
    index = 1
    for sibling in parent:
        if sibling is element:
            return index
        if isinstance(sibling.tag, str) and sibling.tag == element.tag:
            index += 1
    return index


def _xpath_for_element(element: etree._Element) -> str:
    parts: list[str] = []
    node: etree._Element | None = element
    while node is not None and isinstance(node.tag, str):
        parts.append(f"{_local_name(node.tag)}[{_sibling_index(node)}]")
        node = node.getparent()
    return "/" + "/".join(reversed(parts))


def _root_closing_end(text: str, root: etree._Element) -> int:
    """Position juste après la dernière balise fermante correspondant au
    nom de la racine (approximation : s'il existe un élément homonyme
    imbriqué plus bas portant le même nom local que la racine, la toute
    dernière occurrence est prise — cas non rencontré en pratique, la
    racine ``TEI``/``teiCorpus`` n'étant jamais réutilisée comme nom
    d'élément imbriqué dans un document TEI valide)."""
    name = _local_name(root.tag)
    closing_re = re.compile(r"</(?:[\w.\-]+:)?" + re.escape(name) + r"\s*>")
    matches = list(closing_re.finditer(text))
    return matches[-1].end() if matches else len(text)


def _xpath_from_tree(root: etree._Element, text: str, offset: int) -> str:
    elements = _real_elements_in_document_order(root)
    if not elements:
        return "/"
    if offset > _root_closing_end(text, root):
        return "/"
    offsets = _open_tag_end_offsets(text, len(elements))
    current: etree._Element | None = None
    for element, (end, selfclose) in zip(elements, offsets):
        if selfclose:
            continue
        if end <= offset:
            current = element
        else:
            break
    if current is None:
        return "/"
    return _xpath_for_element(current)


def current_xpath(text: str, offset: int) -> str | None:
    """Renvoie l'XPath absolu de l'élément courant à ``offset`` dans
    ``text``, ou ``None`` si ``text`` est actuellement mal formé
    (l'appelant doit alors afficher un indicateur neutre).
    """
    try:
        root = parse_xml_safely(text)
    except UnsafeXmlError:
        return None
    offset = max(0, min(offset, len(text)))
    return _xpath_from_tree(root, text, offset)
