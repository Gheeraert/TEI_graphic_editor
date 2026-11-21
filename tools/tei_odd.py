"""Fonctions d'extraction du catalogue TEI P5 depuis le fichier ODD officiel
``p5subset.xml``.

Ce module ne fait qu'une chose : lire le fichier XML source (téléchargé par
``tools/build_catalog.py``) et le transformer en structures Python simples
(``dict``/``list``) directement sérialisables en JSON. Il n'accède jamais au
réseau lui-même : le téléchargement et le cache sont gérés par l'appelant.

Limites documentées (voir aussi ``docs/REGLES_ENCODAGE.md``) :

- Les listes d'enfants/parents approximatifs (``children_approx`` /
  ``parents_approx``) sont construites en parcourant le modèle de contenu
  compilé (``<content>``) et en résolvant les références de classe
  (``classRef``) vers les éléments qui en sont membres, directement ou par
  héritage de classe (``memberOf``). C'est une approximation utile pour une
  palette de balises ; ce n'est **pas** un moteur de grammaire RelaxNG et ne
  doit jamais servir à valider un document.
- Les attributs resolus pour un élément combinent ses attributs propres
  (``attList`` déclaré directement dans l'``elementSpec``) et ceux des
  classes d'attributs (``att.*``) dont il hérite, transitivement, via les
  relations ``memberOf`` entre classes. Chaque attribut résolu porte un champ
  ``source`` indiquant s'il vient de l'élément lui-même ou d'une classe
  d'attributs nommée.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}

# Langues préférées pour les gloses/descriptions, dans l'ordre de préférence.
LANG_PREFERENCE = ("fr", "en")

# Tags du modèle de contenu compilé qui référencent effectivement d'autres
# noeuds de la grammaire (classes, éléments ou macros de données).
_REF_TAGS = {"classRef", "elementRef", "macroRef", "dataRef"}


def q(tag: str) -> str:
    """Qualifie un nom de balise local avec le namespace TEI."""

    return f"{{{TEI_NS}}}{tag}"


def _local(tag: str) -> str:
    return etree.QName(tag).localname


def load_tree(path: str) -> etree._ElementTree:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    return etree.parse(path, parser)


def _best_text(nodes: Iterable[etree._Element]) -> str | None:
    """Choisit le meilleur texte parmi une liste de ``<gloss>``/``<desc>``.

    Préfère le français, puis l'anglais ; à égalité de langue, préfère la
    version la plus récente (``@versionDate``) pour un résultat déterministe.
    """

    by_lang: dict[str, list[tuple[str, str]]] = {}
    for node in nodes:
        lang = node.get("{http://www.w3.org/XML/1998/namespace}lang")
        if not lang:
            continue
        text = "".join(node.itertext()).strip()
        if not text:
            continue
        version = node.get("versionDate") or ""
        by_lang.setdefault(lang, []).append((version, text))

    for lang in LANG_PREFERENCE:
        candidates = by_lang.get(lang)
        if candidates:
            candidates.sort(key=lambda pair: pair[0])
            return candidates[-1][1]
    return None


def extract_gloss_desc(spec: etree._Element) -> tuple[str | None, str | None]:
    glosses = spec.findall(q("gloss"))
    descs = spec.findall(q("desc"))
    return _best_text(glosses), _best_text(descs)


def extract_classes(spec: etree._Element) -> list[str]:
    classes_el = spec.find(q("classes"))
    if classes_el is None:
        return []
    return [m.get("key") for m in classes_el.findall(q("memberOf")) if m.get("key")]


def extract_val_list(att_def: etree._Element) -> tuple[str | None, list[dict]]:
    val_list = att_def.find(q("valList"))
    if val_list is None:
        return None, []
    val_type = val_list.get("type")
    values = []
    for item in val_list.findall(q("valItem")):
        gloss, desc = extract_gloss_desc(item)
        values.append({"ident": item.get("ident"), "gloss": gloss, "desc": desc})
    return val_type, values


def extract_datatype(att_def: etree._Element) -> str | None:
    dt = att_def.find(q("datatype"))
    if dt is None:
        return None
    ref = dt.find(q("dataRef"))
    if ref is not None and ref.get("key"):
        return ref.get("key")
    macro_ref = dt.find(q("macroRef"))
    if macro_ref is not None and macro_ref.get("key"):
        return macro_ref.get("key")
    text = "".join(dt.itertext()).strip()
    return text or None


def parse_att_def(att_def: etree._Element, source: str) -> dict:
    gloss, desc = extract_gloss_desc(att_def)
    val_type, values = extract_val_list(att_def)
    return {
        "ident": att_def.get("ident"),
        "usage": att_def.get("usage", "opt"),
        "datatype": extract_datatype(att_def),
        "gloss": gloss,
        "desc": desc,
        "closed_values": values if val_type == "closed" else [],
        "values_type": val_type,
        "values": values,
        "source": source,
    }


def parse_att_list(spec: etree._Element, source: str) -> list[dict]:
    att_list = spec.find(q("attList"))
    if att_list is None:
        return []
    return [parse_att_def(a, source) for a in att_list.findall(q("attDef"))]


def extract_examples(spec: etree._Element) -> list[dict]:
    examples = []
    for ex in spec.findall(q("exemplum")):
        lang = ex.get("{http://www.w3.org/XML/1998/namespace}lang")
        eg = ex.find("{http://www.tei-c.org/ns/Examples}egXML")
        if eg is None:
            continue
        xml_text = etree.tostring(eg, encoding="unicode", pretty_print=True).strip()
        examples.append({"lang": lang, "xml": xml_text})
    return examples


def collect_content_refs(spec: etree._Element) -> list[tuple[str, str]]:
    """Parcourt ``<content>`` et renvoie les paires ``(type_de_ref, clé)``.

    ``type_de_ref`` est l'un de ``classRef``, ``elementRef``, ``macroRef``,
    ``dataRef`` (noms de balises du modèle de contenu compilé TEI, pas des
    noms RelaxNG). Voir la docstring du module pour les limites de cette
    approximation.
    """

    content = spec.find(q("content"))
    if content is None:
        return []
    refs: list[tuple[str, str]] = []
    for node in content.iter():
        if not isinstance(node.tag, str):
            continue  # ignore les commentaires et instructions de traitement
        local = _local(node.tag)
        if local in _REF_TAGS:
            key = node.get("key")
            if key:
                refs.append((local, key))
    return refs


@dataclass
class ElementSpec:
    ident: str
    module: str | None
    gloss: str | None
    desc: str | None
    classes: list[str] = field(default_factory=list)
    own_attributes: list[dict] = field(default_factory=list)
    content_refs: list[tuple[str, str]] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)


@dataclass
class ClassSpec:
    ident: str
    type_: str | None
    module: str | None
    gloss: str | None
    desc: str | None
    classes: list[str] = field(default_factory=list)
    own_attributes: list[dict] = field(default_factory=list)


def parse_element_specs(root: etree._Element) -> dict[str, ElementSpec]:
    elements: dict[str, ElementSpec] = {}
    for spec in root.iter(q("elementSpec")):
        ident = spec.get("ident")
        if not ident:
            continue
        gloss, desc = extract_gloss_desc(spec)
        elements[ident] = ElementSpec(
            ident=ident,
            module=spec.get("module"),
            gloss=gloss,
            desc=desc,
            classes=extract_classes(spec),
            own_attributes=parse_att_list(spec, source="own"),
            content_refs=collect_content_refs(spec),
            examples=extract_examples(spec),
        )
    return elements


def parse_class_specs(root: etree._Element) -> dict[str, ClassSpec]:
    classes: dict[str, ClassSpec] = {}
    for spec in root.iter(q("classSpec")):
        ident = spec.get("ident")
        if not ident:
            continue
        gloss, desc = extract_gloss_desc(spec)
        classes[ident] = ClassSpec(
            ident=ident,
            type_=spec.get("type"),
            module=spec.get("module"),
            gloss=gloss,
            desc=desc,
            classes=extract_classes(spec),
            own_attributes=parse_att_list(spec, source=ident),
        )
    return classes


def build_memberof_graph(classes: dict[str, ClassSpec]) -> dict[str, set[str]]:
    """Graphe ``classe -> ensemble de classes dont elle est directement membre``."""

    graph: dict[str, set[str]] = {}
    for ident, spec in classes.items():
        graph[ident] = set(spec.classes)
    return graph


def ancestors_closure(start: Iterable[str], graph: dict[str, set[str]]) -> set[str]:
    """BFS vers le haut : classes incluses, directement ou transitivement.

    Utilisé pour résoudre les attributs hérités : si un élément est membre de
    la classe A et que A est elle-même ``memberOf`` B, l'élément hérite aussi
    des attributs déclarés sur B.
    """

    seen: set[str] = set(start)
    frontier = list(start)
    while frontier:
        node = frontier.pop()
        for parent in graph.get(node, ()):
            if parent not in seen:
                seen.add(parent)
                frontier.append(parent)
    return seen


def build_reverse_graph(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {}
    for child, parents in graph.items():
        for parent in parents:
            reverse.setdefault(parent, set()).add(child)
    return reverse


def descendants_closure(key: str, reverse_graph: dict[str, set[str]]) -> set[str]:
    """BFS vers le bas : classes qui sont (transitivement) ``memberOf`` ``key``.

    Utilisé pour résoudre les enfants approximatifs : si le modèle de contenu
    référence la classe X, tout élément membre d'une sous-classe de X est un
    enfant possible.
    """

    seen: set[str] = {key}
    frontier = [key]
    while frontier:
        node = frontier.pop()
        for child in reverse_graph.get(node, ()):
            if child not in seen:
                seen.add(child)
                frontier.append(child)
    return seen
