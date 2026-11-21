"""Accès partagé au catalogue TEI (`data/tei_catalog.json`, phase 1) et
aux profils (listes blanches, `data/profiles/*.json`, phase 1).

Extrait de `editor/diagnostics.py` (phase 4) pour être réutilisé par la
palette contextuelle et l'inspecteur d'attributs (phase 5,
`docs/ROADMAP.md` §5) sans dupliquer le chargement du catalogue. Module
testable sans Qt (`CLAUDE.md`) : aucune dépendance PySide6 ici.

Rappel ADR-0003/ADR-0007 : ce module ne fait que **suggérer** (palette,
inspecteur) ; la validation réelle reste le schéma RelaxNG unique
(`editor/diagnostics.py`). ``children_approx`` est une approximation qui
**peut être vide** pour un élément dont le modèle de contenu référence
des classes non résolues (ex. ``p``) : :func:`suggested_elements` prévoit
un repli documenté pour ce cas.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATALOG_PATH = DATA_DIR / "tei_catalog.json"
PROFILES_DIR = DATA_DIR / "profiles"

#: Éléments habituellement encodés sans contenu (balise auto-fermante),
#: utilisés par l'insertion avec fermeture automatique (phase 5, point
#: 3). **Liste statique et documentée, pas une conséquence fiable du
#: catalogue** : ``children_approx`` n'est pas un indicateur sûr de
#: vacuité (ex. ``gap`` référence formellement ``certainty``/``desc``
#: dans son modèle de contenu, ADR-0003, bien qu'il soit presque toujours
#: encodé vide en pratique). Un choix simple et assumé, pas prétendu
#: exhaustif (`docs/ROADMAP.md` §5.3) : plutôt que de dériver cette
#: propriété d'un champ absent du catalogue, on l'énumère à la main pour
#: les cas usuels les plus sûrs.
TYPICALLY_EMPTY_ELEMENTS = frozenset(
    {
        "lb",
        "pb",
        "cb",
        "gap",
        "anchor",
        "milestone",
        "graphic",
        "space",
    }
)


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Charge et met en cache `tei_catalog.json`. Renvoie une structure
    vide (sans lever) si le fichier est absent — dégrade juste les
    gloses/suggestions, jamais la validation RelaxNG qui n'en dépend
    pas."""
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {"elements": {}}


def element_entry(ident: str) -> dict | None:
    """Renvoie l'entrée brute du catalogue pour l'élément ``ident``, ou
    ``None`` si inconnu."""
    return load_catalog().get("elements", {}).get(ident)


def element_gloss(ident: str) -> str:
    """Glose française (si connue) suivie de l'identifiant technique,
    pour affichage dans les messages/menus."""
    entry = element_entry(ident)
    gloss = entry.get("gloss") if entry else None
    return f"{gloss} ({ident})" if gloss else ident


def attribute_gloss(ident: str) -> str:
    """Glose française (si connue) d'un attribut, cherché par identifiant
    dans n'importe quel élément du catalogue qui le porte."""
    for entry in load_catalog().get("elements", {}).values():
        for attr in entry.get("attributes", []):
            if attr.get("ident") == ident and attr.get("gloss"):
                return f"{attr['gloss']} (@{ident})"
    return f"@{ident}"

def children_of(element_name: str) -> list[str]:
    """``children_approx`` du catalogue pour ``element_name`` (liste
    triée), ou liste vide si l'élément est inconnu ou si le catalogue ne
    documente aucun enfant approximatif pour lui (ADR-0003 : peut
    arriver même pour un élément réel, ex. ``p``)."""
    entry = element_entry(element_name)
    if not entry:
        return []
    return sorted(entry.get("children_approx", []) or [])


def attributes_of(element_name: str) -> list[dict]:
    """Liste brute ``attributes`` du catalogue pour ``element_name``
    (chaque entrée : ``ident``, ``usage``, ``datatype``, ``gloss``,
    ``desc``, ``closed_values``, ``values_type``, ``values``,
    ``source``)."""
    entry = element_entry(element_name)
    if not entry:
        return []
    return list(entry.get("attributes", []))


def is_typically_empty(ident: str) -> bool:
    """``True`` si ``ident`` fait partie de la petite liste documentée
    d'éléments habituellement encodés sans contenu
    (:data:`TYPICALLY_EMPTY_ELEMENTS`)."""
    return ident in TYPICALLY_EMPTY_ELEMENTS


@lru_cache(maxsize=8)
def profile_whitelist(profile_id: str) -> frozenset[str] | None:
    """Liste blanche (noms d'éléments) d'un profil, aplatie depuis ses
    ``groups[].elements``. ``None`` si le profil est introuvable/invalide
    (différent d'une liste blanche vide : un appelant doit alors traiter
    le profil comme "sans restriction connue", pas comme "profil vide")."""
    path = PROFILES_DIR / f"{profile_id}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    elements: set[str] = set()
    for group in data.get("groups", []):
        elements.update(group.get("elements", []))
    return frozenset(elements)


@lru_cache(maxsize=8)
def profile_groups(profile_id: str) -> list[dict]:
    """Groupes bruts (``id``, ``label``, ``elements``) d'un profil, dans
    l'ordre du fichier JSON — utilisé par la palette contextuelle pour
    regrouper ses suggestions sans recoder de listes de balises
    (`CLAUDE.md`). Liste vide si le profil est introuvable."""
    path = PROFILES_DIR / f"{profile_id}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    return list(data.get("groups", []))


def all_catalog_elements() -> frozenset[str]:
    """Tous les identifiants d'éléments connus du catalogue."""
    return frozenset(load_catalog().get("elements", {}).keys())


def suggested_elements(current_element_name: str | None, profile_id: str) -> list[str]:
    """Éléments suggérés par la palette contextuelle pour une position de
    curseur donnée (phase 5, point 1) : intersection entre
    ``children_approx`` de l'élément courant et la liste blanche du
    profil actif.

    **Repli documenté** : si ``children_approx`` de l'élément courant est
    vide (ADR-0003 : approximation, peut être vide même pour un élément
    qui accepte réellement du contenu, ex. ``p``), ou si l'élément
    courant est inconnu, on propose à la place tous les éléments du
    profil actif (ou tout le catalogue si le profil est introuvable) :
    une liste vide ne serait d'aucune utilité dans la palette, et rester
    permissif (pas bloquant) est le principe explicite de cette phase.
    """
    whitelist = profile_whitelist(profile_id)
    if whitelist is None:
        whitelist = all_catalog_elements()
    if current_element_name is None:
        return sorted(whitelist)
    children = children_of(current_element_name)
    if not children:
        return sorted(whitelist)
    restricted = set(children) & whitelist
    if not restricted:
        # L'intersection est vide (élément hors profil, ou profil très
        # restrictif) : repli identique, permissif plutôt que bloquant.
        return sorted(whitelist)
    return sorted(restricted)
