#!/usr/bin/env python3
"""Génère le catalogue des balises TEI P5 et les profils de balisage.

Ce script lit le fichier ODD officiel ``p5subset.xml`` publié par le
consortium TEI (voir ``SOURCE_URL`` ci-dessous), le met en cache localement
(``.cache/tei/``, non versionné — voir ``.gitignore``) puis produit :

- ``src/tei_editor/data/tei_catalog.json`` : le catalogue complet des
  éléments TEI P5 (module, classes, attributs résolus, enfants/parents
  approximatifs, glose/description en français si disponible sinon en
  anglais, exemples) ;
- ``src/tei_editor/data/profiles/*.json`` : des listes blanches d'éléments
  groupés logiquement, destinées à une future palette de balises.

Usage ::

    .venv/Scripts/python.exe tools/build_catalog.py

Le script est reproductible : à cache inchangé, il produit toujours le même
JSON. Aucune partie de l'application elle-même n'accède au réseau — seul ce
script, exécuté une fois par un développeur pour régénérer les données, le
fait (voir ``CLAUDE.md``, « Pas d'accès réseau dans l'application »).

Limites connues (voir aussi les docstrings de ``tools/tei_odd.py`` et
``docs/REGLES_ENCODAGE.md``) :

- Les enfants/parents « approximatifs » sont dérivés du modèle de contenu
  compilé par résolution des classes (``classRef``) ; ce n'est pas un moteur
  de grammaire RelaxNG et ne doit jamais être utilisé pour valider un
  document (voir ADR-0003 dans ``docs/DECISIONS.md``).
- Les attributs résolus combinent les attributs propres de l'élément et ceux
  hérités par les classes d'attributs (``att.*``), via la fermeture
  transitive des relations ``memberOf`` entre classes. C'est plus complet
  qu'une résolution « élément seul », mais reste une approximation du modèle
  ODD réel (pas de gestion des contraintes de combinaison de classes,
  ``<constraintSpec>`` ignorées).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tei_odd import (  # noqa: E402
    ancestors_closure,
    build_memberof_graph,
    build_reverse_graph,
    descendants_closure,
    load_tree,
    parse_class_specs,
    parse_element_specs,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".cache" / "tei"
DATA_DIR = REPO_ROOT / "src" / "tei_editor" / "data"
PROFILES_DIR = DATA_DIR / "profiles"

TEI_VERSION = "4.12.0"
SOURCE_URL = f"https://www.tei-c.org/Vault/P5/{TEI_VERSION}/xml/tei/odd/p5subset.xml"
CACHE_FILE = CACHE_DIR / f"p5subset-{TEI_VERSION}.xml"


def fetch_source(*, force: bool = False) -> Path:
    """Télécharge ``p5subset.xml`` dans le cache local si nécessaire.

    Le cache n'est jamais recréé si le fichier existe déjà, sauf
    ``force=True`` : c'est ce qui rend le script reproductible sans
    re-téléchargement à chaque exécution.
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_FILE.exists() and not force:
        print(f"[cache] {CACHE_FILE} déjà présent, pas de téléchargement.")
        return CACHE_FILE

    print(f"[téléchargement] {SOURCE_URL}")
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "tei-editor-build-catalog/0.1"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    CACHE_FILE.write_bytes(data)
    print(f"[cache] écrit {CACHE_FILE} ({len(data)} octets)")
    return CACHE_FILE


def resolve_attributes(
    ident: str,
    element_classes: list[str],
    own_attributes: list[dict],
    classes_by_ident: dict,
    memberof_graph: dict[str, set[str]],
) -> list[dict]:
    """Combine les attributs propres et ceux hérités des classes d'attributs."""

    effective_classes = ancestors_closure(element_classes, memberof_graph)
    resolved = list(own_attributes)
    seen_idents = {a["ident"] for a in resolved}
    # Ordre déterministe : on trie les classes par nom avant d'y puiser les
    # attributs, pour que deux exécutions produisent le même JSON.
    for class_ident in sorted(effective_classes):
        class_spec = classes_by_ident.get(class_ident)
        if class_spec is None or class_spec.type_ != "atts":
            continue
        for att in class_spec.own_attributes:
            # Un même attribut (ex. @type) peut être redéclaré par plusieurs
            # classes ou par l'élément lui-même : l'élément et la première
            # classe rencontrée (ordre alphabétique) gagnent.
            if att["ident"] in seen_idents:
                continue
            resolved.append(att)
            seen_idents.add(att["ident"])
    return resolved


def resolve_children(
    content_refs: list[tuple[str, str]],
    elements: dict,
    class_members: dict[str, set[str]],
    reverse_graph: dict[str, set[str]],
) -> set[str]:
    """Résout les références du modèle de contenu en noms d'éléments approximatifs."""

    children: set[str] = set()
    for ref_type, key in content_refs:
        if ref_type == "elementRef":
            if key in elements:
                children.add(key)
        elif ref_type == "classRef":
            for class_ident in descendants_closure(key, reverse_graph):
                children.update(class_members.get(class_ident, ()))
        # macroRef / dataRef : macros de données (teidata.*), pas des
        # éléments ; volontairement ignorées pour les enfants approximatifs.
    return children


def build_catalog() -> dict:
    cache_path = fetch_source()
    tree = load_tree(str(cache_path))
    root = tree.getroot()

    elements = parse_element_specs(root)
    classes = parse_class_specs(root)
    memberof_graph = build_memberof_graph(classes)
    reverse_graph = build_reverse_graph(memberof_graph)

    # classe -> éléments qui en sont directement membres (déclaration propre,
    # sans remonter la hiérarchie de classes).
    class_members: dict[str, set[str]] = {}
    for ident, spec in elements.items():
        for class_ident in spec.classes:
            class_members.setdefault(class_ident, set()).add(ident)

    catalog_elements: dict[str, dict] = {}
    for ident, spec in sorted(elements.items()):
        attributes = resolve_attributes(
            ident, spec.classes, spec.own_attributes, classes, memberof_graph
        )
        children = resolve_children(spec.content_refs, elements, class_members, reverse_graph)
        catalog_elements[ident] = {
            "ident": ident,
            "module": spec.module,
            "classes": sorted(spec.classes),
            "gloss": spec.gloss,
            "desc": spec.desc,
            "attributes": sorted(attributes, key=lambda a: a["ident"]),
            "children_approx": sorted(children - {ident}),
            "parents_approx": [],  # rempli ci-dessous, par inversion
            "examples": spec.examples,
        }

    # Parents approximatifs = inversion de la relation "enfant approximatif".
    for ident, entry in catalog_elements.items():
        for child in entry["children_approx"]:
            if child in catalog_elements:
                catalog_elements[child]["parents_approx"].append(ident)
    for entry in catalog_elements.values():
        entry["parents_approx"] = sorted(set(entry["parents_approx"]))

    catalog_classes: dict[str, dict] = {}
    for ident, spec in sorted(classes.items()):
        catalog_classes[ident] = {
            "ident": ident,
            "type": spec.type_,
            "module": spec.module,
            "classes": sorted(spec.classes),
            "gloss": spec.gloss,
            "desc": spec.desc,
            "attributes": sorted(spec.own_attributes, key=lambda a: a["ident"]),
        }

    return {
        "tei_version": TEI_VERSION,
        "source_url": SOURCE_URL,
        "generated_by": "tools/build_catalog.py",
        "notes": (
            "Catalogue généré automatiquement depuis le fichier ODD officiel "
            "p5subset.xml du consortium TEI. Les champs children_approx et "
            "parents_approx sont des approximations tirées du modèle de "
            "contenu compilé (résolution des classRef), destinées à "
            "suggérer des balises dans une palette : elles ne remplacent "
            "pas une validation RelaxNG (voir docs/DECISIONS.md, "
            "ADR-0003). Les attributs résolus incluent les attributs "
            "propres de l'élément et ceux hérités par les classes "
            "d'attributs (att.*), via la fermeture transitive des "
            "relations memberOf."
        ),
        "element_count": len(catalog_elements),
        "class_count": len(catalog_classes),
        "elements": catalog_elements,
        "classes": catalog_classes,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(f"[écrit] {path}")


def main() -> None:
    catalog = build_catalog()
    write_json(DATA_DIR / "tei_catalog.json", catalog)

    from build_profiles import build_all_profiles  # noqa: E402 (import tardif volontaire)

    all_idents = set(catalog["elements"])
    for profile in build_all_profiles(all_idents):
        write_json(PROFILES_DIR / f"{profile['id']}.json", profile)

    print(
        f"Terminé : {catalog['element_count']} éléments, "
        f"{catalog['class_count']} classes, "
        f"{len(all_idents)} éléments catalogués."
    )


if __name__ == "__main__":
    main()
