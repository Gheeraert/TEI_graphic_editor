"""Diagnostics structurés pour la phase 4 (`docs/ROADMAP.md` §5) : bonne
formation avec ligne/colonne précises, validation RelaxNG contre le
schéma unique `tei_all` (voir `docs/DECISIONS.md`, ADR « schéma unique +
double couche d'avertissement »), messages RelaxNG reformulés en
français lisible, et avertissements « hors profil » (liste blanche du
profil actif, non bloquants).

Module testable sans Qt (`CLAUDE.md`) : branché par `main_window.py` sur
le timer de re-parsing différé existant (``_update_structural_info``).
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from lxml import etree

from tei_editor.tei.xml_safety import UnsafeXmlError, UnsafeXmlSyntaxError, safe_xml_parser

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEMA_PATH = DATA_DIR / "schemas" / "tei_all" / "tei_all.rng"
CATALOG_PATH = DATA_DIR / "tei_catalog.json"

SEVERITY_ERROR = "erreur"
SEVERITY_WARNING = "avertissement"

_TEI_NS = "http://www.tei-c.org/ns/1.0"


@dataclass(frozen=True)
class Diagnostic:
    """Un problème signalé sur le document courant.

    ``column`` est ``None`` quand l'information n'est pas disponible
    (cas fréquent des erreurs RelaxNG côté libxml2 — voir
    :func:`validate_relaxng`) : on ne l'invente jamais. ``xpath`` est
    ``None`` quand on ne construit pas un chemin exploitable pour ce
    diagnostic (ex. document mal formé : il n'y a pas d'arbre).
    """

    severity: str
    line: int
    column: int | None
    message: str
    xpath: str | None = None


# -- Bonne formation ----------------------------------------------------------


def parse_with_diagnostics(text: str) -> tuple[etree._Element | None, list[Diagnostic]]:
    """Analyse ``text`` avec la même politique durcie que
    :func:`tei_editor.tei.xml_safety.parse_xml_safely`, sans perdre la
    position de l'erreur. Renvoie ``(racine, [])`` si bien formé, ou
    ``(None, [diagnostic])`` sinon (un seul diagnostic : libxml2 arrête
    l'analyse à la première erreur de bonne formation).
    """
    data = text.encode("utf-8")
    try:
        root = etree.fromstring(data, parser=safe_xml_parser())
    except etree.XMLSyntaxError as exc:
        line = exc.lineno or 1
        column = exc.offset or 1
        message = f"Document XML mal formé : {exc.msg if hasattr(exc, 'msg') else exc}"
        return None, [Diagnostic(SEVERITY_ERROR, line, column, message, xpath=None)]
    if root.getroottree().docinfo.doctype:
        return None, [
            Diagnostic(
                SEVERITY_ERROR,
                1,
                1,
                "Les déclarations DOCTYPE/DTD ne sont pas autorisées dans ce document TEI.",
                xpath=None,
            )
        ]
    return root, []


# -- Schéma RelaxNG (tei_all, schéma unique faisant autorité) ----------------

_schema_lock = threading.Lock()
_schema_cache: etree.RelaxNG | None = None


def _load_schema() -> etree.RelaxNG | None:
    """Compile et met en cache le schéma `tei_all` en mémoire (une seule
    fois, jamais recompilé à chaque frappe). Renvoie ``None`` si le
    schéma n'est pas installé (ne doit pas arriver en usage normal : il
    est committé dans le dépôt par `tools/fetch_schema.py` — un ``None``
    dégraderait juste la validation RelaxNG, pas la bonne formation).
    """
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    with _schema_lock:
        if _schema_cache is None:
            if not SCHEMA_PATH.is_file():
                return None
            schema_doc = etree.parse(str(SCHEMA_PATH))
            _schema_cache = etree.RelaxNG(schema_doc)
    return _schema_cache


def _local_name(tag: str) -> str:
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag if isinstance(tag, str) else ""


# -- Catalogue (gloses françaises) --------------------------------------------


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {"elements": {}}


def _element_gloss(ident: str) -> str:
    elements = _load_catalog().get("elements", {})
    entry = elements.get(ident)
    gloss = entry.get("gloss") if entry else None
    return f"{gloss} ({ident})" if gloss else ident


def _attribute_gloss(ident: str) -> str:
    elements = _load_catalog().get("elements", {})
    for entry in elements.values():
        for attr in entry.get("attributes", []):
            if attr.get("ident") == ident and attr.get("gloss"):
                return f"{attr['gloss']} (@{ident})"
    return f"@{ident}"


# -- Reformulation française des messages RelaxNG (libxml2) ------------------

_PATTERNS: list[tuple[re.Pattern, "callable"]] = []


def _pattern(regex: str):
    compiled = re.compile(regex)

    def register(func):
        _PATTERNS.append((compiled, func))
        return func

    return register


@_pattern(r"^Did not expect element (\S+) there$")
def _msg_unexpected_element(match: re.Match) -> str:
    return (
        f"L'élément {_element_gloss(match.group(1))} n'est pas attendu à cet "
        "endroit du document (il ne correspond pas au modèle de contenu de "
        "son élément parent)."
    )


@_pattern(r"^Invalid attribute (\S+) for element (\S+)$")
def _msg_invalid_attribute(match: re.Match) -> str:
    attr, elem = match.group(1), match.group(2)
    return (
        f"L'attribut {_attribute_gloss(attr)} n'est pas valide pour "
        f"l'élément {_element_gloss(elem)}."
    )


@_pattern(r"^Element (\S+) failed to validate attributes$")
def _msg_failed_attributes(match: re.Match) -> str:
    return f"Les attributs de l'élément {_element_gloss(match.group(1))} ne sont pas valides."


@_pattern(r"^Element (\S+) failed to validate content$")
def _msg_failed_content(match: re.Match) -> str:
    return (
        f"Le contenu de l'élément {_element_gloss(match.group(1))} ne "
        "correspond pas au modèle attendu (éléments manquants, en trop, ou "
        "mal ordonnés)."
    )


@_pattern(r"^Expecting element (\S+), got (\S+)$")
def _msg_expecting_element(match: re.Match) -> str:
    attendu, trouve = match.group(1), match.group(2)
    return (
        f"Élément attendu à cet endroit : {_element_gloss(attendu)} ; "
        f"élément trouvé : {_element_gloss(trouve)}."
    )


@_pattern(r"^Expecting an element (\S*), got nothing$")
def _msg_expecting_nothing(match: re.Match) -> str:
    nom = match.group(1)
    if nom:
        return f"Il manque un élément obligatoire ({_element_gloss(nom)}) à cet endroit."
    return "Il manque un élément obligatoire à cet endroit (modèle de contenu incomplet)."


@_pattern(r"^Invalid sequence in interleave$")
def _msg_invalid_sequence(match: re.Match) -> str:
    return "Les éléments à cet endroit ne respectent pas l'ordre ou la combinaison attendus."


def reformulate_relaxng_message(raw_message: str) -> str:
    """Traduit un message technique RelaxNG/libxml2 en une phrase
    française lisible, en utilisant les gloses du catalogue TEI
    (`tei_catalog.json`) quand c'est pertinent. Ne renvoie jamais le
    texte brut non traduit : si aucun motif connu ne correspond, un
    message générique et propre est utilisé à la place.
    """
    message = raw_message.strip()
    for pattern, handler in _PATTERNS:
        match = pattern.match(message)
        if match:
            return handler(match)
    return (
        "Erreur de validation du schéma TEI à cet endroit : le document ne "
        "respecte pas le modèle de contenu attendu."
    )


def validate_relaxng(root: etree._Element) -> list[Diagnostic]:
    """Valide ``root`` contre le schéma unique `tei_all` et renvoie les
    diagnostics (sévérité « erreur »), message reformulé en français.

    La colonne est quasi systématiquement absente côté libxml2/RelaxNG
    (limite documentée ici et dans `docs/DECISIONS.md`) : ``column`` est
    toujours ``None`` pour ces diagnostics plutôt qu'une valeur inventée.
    """
    schema = _load_schema()
    if schema is None:
        return []
    tree = root.getroottree()
    if schema.validate(tree):
        return []
    diagnostics: list[Diagnostic] = []
    for entry in schema.error_log:
        diagnostics.append(
            Diagnostic(
                severity=SEVERITY_ERROR,
                line=entry.line or 1,
                column=None,
                message=reformulate_relaxng_message(entry.message),
                xpath=None,
            )
        )
    return diagnostics


# -- Avertissements « hors profil » (liste blanche, non bloquant) -----------


@lru_cache(maxsize=8)
def _profile_whitelist(profile_id: str) -> frozenset[str] | None:
    path = DATA_DIR / "profiles" / f"{profile_id}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    elements: set[str] = set()
    for group in data.get("groups", []):
        elements.update(group.get("elements", []))
    return frozenset(elements)


def profile_warnings(root: etree._Element, profile_id: str) -> list[Diagnostic]:
    """Avertissements « hors profil » (non bloquants, sévérité distincte
    des erreurs RelaxNG/bonne-formation) : un élément du document qui
    n'appartient pas à la liste blanche du profil actif. Le schéma
    `tei_all` reste la seule grammaire de validation (voir ADR dédié de
    `docs/DECISIONS.md`) ; ``tei_all`` lui-même n'a pas de liste blanche
    restrictive, donc ne produit jamais ces avertissements.
    """
    whitelist = _profile_whitelist(profile_id)
    if whitelist is None:
        return []
    diagnostics: list[Diagnostic] = []
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue  # commentaires, PI
        name = _local_name(element.tag)
        if name in whitelist:
            continue
        diagnostics.append(
            Diagnostic(
                severity=SEVERITY_WARNING,
                line=element.sourceline or 1,
                column=None,
                message=(
                    f"Élément hors profil : {_element_gloss(name)} n'appartient pas à "
                    "la liste blanche du profil actif (reste valide pour tei_all)."
                ),
                xpath=None,
            )
        )
    return diagnostics


# -- Agrégation ----------------------------------------------------------------


def compute_diagnostics(text: str, profile_id: str | None = None) -> list[Diagnostic]:
    """Calcule tous les diagnostics pour ``text`` : bonne formation (toujours),
    puis, si bien formé, validation RelaxNG + avertissements hors profil.
    """
    root, diagnostics = parse_with_diagnostics(text)
    if root is None:
        return diagnostics
    diagnostics.extend(validate_relaxng(root))
    if profile_id:
        diagnostics.extend(profile_warnings(root, profile_id))
    diagnostics.sort(key=lambda d: (d.line, 0 if d.severity == SEVERITY_ERROR else 1))
    return diagnostics
