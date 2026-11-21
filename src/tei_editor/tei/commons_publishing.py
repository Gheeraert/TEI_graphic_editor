# Repris de C:\merope src/bloggen/tei/commons_publishing.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30), adapté :
# `_SCHEMA_PATH` pointe désormais vers
# `tei_editor/data/schemas/commons-publishing/` (voir ADR-0004) au lieu
# des ressources de `bloggen` ; aucun autre changement de comportement.
"""Validation du TEI contre le schéma RelaxNG TEI Commons Publishing et
ses règles Schematron embarquées.

Le schéma lui-même (``data/schemas/commons-publishing/``) est un fichier
tiers, copié avec sa licence et sa provenance d'origine (voir
``LICENSE.txt``/``PROVENANCE.json`` à côté). Ce module de validation,
lui, est repris de Mérope (lxml RelaxNG, compilé une fois, sans réseau
ni résolution de DTD — conforme à la règle « pas d'accès réseau »
de `CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from lxml import etree, isoschematron

# Résolu par rapport à ce fichier, pas au répertoire de travail courant,
# pour fonctionner de la même façon en installation éditable ou normale.
_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "schemas"
    / "commons-publishing"
    / "commons-publishing.rng"
)


@dataclass(slots=True, frozen=True)
class CommonsPublishingIssue:
    message: str
    line: int | None = None
    column: int | None = None

    def __str__(self) -> str:
        if self.line and self.column:
            location = f"{self.line}:{self.column}"
        elif self.line:
            location = f"ligne {self.line}"
        else:
            location = "?"
        return f"{location}: {self.message}"


@dataclass(slots=True, frozen=True)
class CommonsPublishingValidationResult:
    valid: bool
    issues: tuple[CommonsPublishingIssue, ...]


def _xml_parser() -> etree.XMLParser:
    """Analyseur sans accès réseau, DTD externe ni résolution d'entités."""
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, recover=False)


@lru_cache(maxsize=1)
def _commons_publishing_schema() -> etree.RelaxNG:
    """Charge et compile le RNG embarqué une seule fois par processus,
    quel que soit le répertoire de travail courant."""
    schema_root = etree.fromstring(_SCHEMA_PATH.read_bytes(), parser=_xml_parser())
    return etree.RelaxNG(schema_root)


def _issue_from_error(error: etree._LogEntry) -> CommonsPublishingIssue:
    return CommonsPublishingIssue(message=error.message, line=error.line or None, column=error.column or None)


# Deux des 9 règles Schematron embarquées dans le RNG utilisent un
# opérateur de comparaison propre à XPath 2.0 (`gt`, `eq`) que le moteur
# XSLT 1.0 de libxslt (sur lequel lxml.isoschematron compile) refuse à la
# compilation. Les deux occurrences ici sont des comparaisons de scalaires
# singletons (`string-length(...) gt 0`, `@type eq 'deprecationInfo'`),
# pour lesquelles l'opérateur XPath 1.0 est exactement équivalent, pas
# seulement une approximation.
_XPATH2_COMPARISON_OPERATOR_RE = re.compile(r"(?<=[\s(])(gt|lt|ge|le|eq|ne)(?=[\s)])")
_XPATH1_COMPARISON_OPERATORS = {"gt": ">", "lt": "<", "ge": ">=", "le": "<=", "eq": "=", "ne": "!="}
_SVRL_NS = "http://purl.oclc.org/dsdl/svrl"


def _rewrite_xpath2_comparison_operators(schematron_root: etree._Element) -> None:
    for element in schematron_root.iter():
        for attribute in ("context", "test", "select"):
            value = element.get(attribute)
            if value is None:
                continue
            padded = f" {value} "
            rewritten = _XPATH2_COMPARISON_OPERATOR_RE.sub(
                lambda match: _XPATH1_COMPARISON_OPERATORS[match.group(1)], padded
            ).strip()
            if rewritten != value:
                element.set(attribute, rewritten)


@lru_cache(maxsize=1)
def _commons_publishing_schematron() -> isoschematron.Schematron:
    """Extrait et compile les assertions Schematron embarquées dans le RNG,
    une seule fois par processus. ASSERTS_AND_REPORTS pour qu'un
    <sch:report> (se déclenche quand son test est vrai, polarité opposée
    à <sch:assert>) soit lui aussi détecté, pas seulement les échecs
    d'assertion directs."""
    schema_root = etree.fromstring(_SCHEMA_PATH.read_bytes(), parser=_xml_parser())
    extracted = isoschematron.extract_rng(schema_root)
    _rewrite_xpath2_comparison_operators(extracted)
    return isoschematron.Schematron(
        extracted, error_finder=isoschematron.Schematron.ASSERTS_AND_REPORTS, store_report=True
    )


def _issues_from_svrl(report: etree._Element) -> tuple[CommonsPublishingIssue, ...]:
    """Les échecs Schematron portent une localisation XPath, pas une
    ligne/colonne — repliée dans le texte du message plutôt que dans les
    champs ligne/colonne de CommonsPublishingIssue (des notions
    RelaxNG/syntaxe XML)."""
    issues = []
    for node in report.iter(f"{{{_SVRL_NS}}}failed-assert", f"{{{_SVRL_NS}}}successful-report"):
        text_element = node.find(f"{{{_SVRL_NS}}}text")
        raw_message = (text_element.text or "").strip() if text_element is not None else ""
        message = re.sub(r"\s+", " ", raw_message) or "(règle Schematron sans message)"
        if node.get("role") == "nonfatal":
            message = f"[avertissement] {message}"
        location = node.get("location")
        if location:
            message = f"{message} [{location}]"
        issues.append(CommonsPublishingIssue(message=message))
    return tuple(issues)


def validate_commons_publishing_bytes(data: bytes) -> CommonsPublishingValidationResult:
    """Valide des octets XML TEI contre le schéma Commons Publishing
    embarqué (grammaire RelaxNG et assertions Schematron). Une erreur de
    syntaxe XML est rapportée de la même façon qu'une violation de
    schéma plutôt que levée."""
    try:
        document = etree.fromstring(data, parser=_xml_parser())
    except etree.XMLSyntaxError as error:
        issues = tuple(_issue_from_error(item) for item in error.error_log)
        return CommonsPublishingValidationResult(valid=False, issues=issues)

    schema = _commons_publishing_schema()
    relaxng_issues = (
        () if schema.validate(document) else tuple(_issue_from_error(item) for item in schema.error_log)
    )

    schematron = _commons_publishing_schematron()
    schematron_issues = () if schematron.validate(document) else _issues_from_svrl(schematron.validation_report)

    issues = relaxng_issues + schematron_issues
    return CommonsPublishingValidationResult(valid=not issues, issues=issues)


def validate_commons_publishing_file(path: str | Path) -> CommonsPublishingValidationResult:
    return validate_commons_publishing_bytes(Path(path).read_bytes())
