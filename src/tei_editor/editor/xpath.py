"""XPath courant calculé depuis une position de curseur dans le texte XML.

Phase 4 (`docs/ROADMAP.md` §5) : remplace l'approximation par balayage
regex de la phase 3 (ADR-0006 §7) par un calcul basé sur l'arbre
``lxml`` réellement analysé — la structure (imbrication, index parmi les
frères de même nom) vient de l'arbre, pas d'une pile reconstruite à la
main.

Phase 5 : le repérage de « l'élément courant » lui-même (balayage des
positions de balises, appariement 1 pour 1 avec l'arbre lxml) est
partagé avec les opérations d'édition structurée — voir
`editor/current_element.py`, qui porte maintenant cette logique. Ce
module ne garde que la construction du chemin XPath affiché dans la
barre d'état.

**Limite assumée (documentée aussi dans `docs/DECISIONS.md` et dans
`editor/current_element.py`).** ``lxml`` n'expose que la ligne de
*début* de balise ouvrante de chaque élément (``Element.sourceline``),
jamais sa colonne ni sa ligne de fin. L'heuristique retenue pour
« l'élément courant » : le dernier élément, dans l'ordre du document,
dont la balise ouvrante est entièrement refermée avant ou à la position
du curseur. Un curseur placé juste après la fermeture d'un élément mais
avant la fermeture de son parent sera donc rattaché à cet élément déjà
refermé plutôt qu'à son parent — approximation jugée acceptable pour un
fil d'Ariane informatif, pas pour une opération d'édition.
"""

from __future__ import annotations

from lxml import etree

from tei_editor.editor.current_element import local_name, locate_current_element


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
        parts.append(f"{local_name(node.tag)}[{_sibling_index(node)}]")
        node = node.getparent()
    return "/" + "/".join(reversed(parts))


def current_xpath(text: str, offset: int) -> str | None:
    """Renvoie l'XPath absolu de l'élément courant à ``offset`` dans
    ``text``, ou ``None`` si ``text`` est actuellement mal formé
    (l'appelant doit alors afficher un indicateur neutre).
    """
    located = locate_current_element(text, offset)
    if located is None:
        # Document mal formé (le distinguo avec "racine déjà refermée /
        # curseur avant tout élément", qui renvoie aussi None ici, était
        # déjà rendu par la chaîne "/" côté historique : on le reproduit
        # pour ne pas changer le contrat de `current_xpath`.
        try:
            from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

            parse_xml_safely(text)
        except UnsafeXmlError:
            return None
        return "/"
    return _xpath_for_element(located.element)
