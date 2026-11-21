"""Plan structurel du document (dock « Plan », phase 4).

Construit, depuis l'arbre ``lxml`` déjà analysé, une hiérarchie réduite
aux niveaux structurants (voir :data:`STRUCTURAL_ELEMENTS`) plutôt que
chaque élément du document : un ``note`` ou un ``hi`` noyé dans un `p`
n'a pas sa place dans un plan de navigation. Module testable sans Qt
(`CLAUDE.md`) ; la couche Qt (``QTreeWidget``) vit dans
``editor/outline_panel.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

#: Éléments qui structurent la navigation dans un document TEI. Limité
#: volontairement (voir ``docs/ROADMAP.md`` §5, phase 4 : « plan
#: structurel... limité à quelques niveaux significatifs ») : la liste
#: blanche complète par profil reste celle du catalogue (phase 7), pas
#: celle-ci, qui ne sert qu'à la navigation.
STRUCTURAL_ELEMENTS = frozenset(
    {
        "TEI",
        "teiCorpus",
        "teiHeader",
        "fileDesc",
        "text",
        "front",
        "body",
        "back",
        "group",
        "div",
        "head",
        "titlePage",
        "sp",
        "lg",
        "castList",
        "table",
        "figure",
        "list",
    }
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[1] if "}" in tag else tag


@dataclass
class OutlineNode:
    """Un nœud du plan : un élément structurant, sa ligne (1-indexée,
    ``Element.sourceline``) et ses enfants structurants (récursivement).
    ``label`` est le nom affiché (``@type``/``@n`` ajoutés quand présents,
    pour distinguer plusieurs ``div`` par exemple)."""

    tag: str
    label: str
    line: int
    children: list["OutlineNode"] = field(default_factory=list)


def _label_for(element: etree._Element) -> str:
    name = _local_name(element.tag)
    details = []
    type_attr = element.get("type")
    if type_attr:
        details.append(type_attr)
    n_attr = element.get("n")
    if n_attr:
        details.append(f"n={n_attr}")
    if element.tag == "head" or name == "head":
        text = (element.text or "").strip()
        if text:
            details.append(f"« {text[:40]} »")
    if details:
        return f"{name} ({', '.join(details)})"
    return name


def _build_node(element: etree._Element) -> OutlineNode:
    node = OutlineNode(
        tag=_local_name(element.tag),
        label=_label_for(element),
        line=element.sourceline or 1,
    )
    for child in element:
        if not isinstance(child.tag, str):
            continue
        if _local_name(child.tag) in STRUCTURAL_ELEMENTS:
            node.children.append(_build_node(child))
        else:
            # Pas structurant lui-même : on continue de chercher des
            # descendants structurants plus bas (ex. un <head> n'a
            # normalement pas de <div> enfant, mais on reste robuste).
            node.children.extend(_descend_for_structural(child))
    return node


def _descend_for_structural(element: etree._Element) -> list[OutlineNode]:
    found: list[OutlineNode] = []
    for child in element:
        if not isinstance(child.tag, str):
            continue
        if _local_name(child.tag) in STRUCTURAL_ELEMENTS:
            found.append(_build_node(child))
        else:
            found.extend(_descend_for_structural(child))
    return found


def build_outline(root: etree._Element) -> OutlineNode | None:
    """Construit le plan depuis la racine ``root`` déjà analysée par
    lxml. Renvoie ``None`` seulement si ``root`` n'est pas structurant du
    tout (ne devrait pas arriver pour un document TEI, sa racine étant
    toujours ``TEI``/``teiCorpus``, mais reste défensif)."""
    if not isinstance(root.tag, str):
        return None
    return _build_node(root)
