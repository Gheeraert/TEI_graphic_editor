"""Vérifie l'intégrité du corpus de démonstration/test fourni par l'utilisateur
(tests/fixtures/tei-samples/, cf. son README.md) et sert de première trace
de non-régression (phase 9) sur de vrais documents TEI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "tei-samples"
TEI_NS = "{http://www.tei-c.org/ns/1.0}"


def _load_manifest() -> dict:
    with (FIXTURES_DIR / "manifest.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _local_names(root) -> set[str]:
    return {el.tag.removeprefix(TEI_NS) for el in root.iter() if isinstance(el.tag, str)}


def test_manifest_references_existing_files() -> None:
    manifest = _load_manifest()
    assert manifest["files"], "le manifeste ne doit pas être vide"
    for entry in manifest["files"]:
        assert (FIXTURES_DIR / entry["file"]).is_file(), entry["file"]


@pytest.mark.parametrize(
    "entry",
    [entry for entry in _load_manifest()["files"] if not entry.get("expect")],
    ids=lambda entry: entry["file"],
)
def test_valid_sample_parses_and_contains_expected_elements(entry: dict) -> None:
    text = (FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8")
    root = parse_xml_safely(text)
    names = _local_names(root)
    missing = set(entry["elements"]) - names
    assert not missing, f"{entry['file']} : éléments attendus absents {missing}"


def test_not_wellformed_sample_is_rejected() -> None:
    entry = next(
        e for e in _load_manifest()["files"] if e.get("expect") == ["not-wellformed"]
    )
    text = (FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8")
    with pytest.raises(UnsafeXmlError):
        parse_xml_safely(text)


def test_duplicate_id_sample_is_rejected_at_parse_time() -> None:
    # libxml2 traite `xml:id` comme un attribut ID et refuse la double
    # déclaration dès l'analyse (XMLSyntaxError) : pas besoin d'un
    # contrôleur d'unicité séparé pour ce cas, parse_xml_safely suffit déjà.
    entry = next(
        e for e in _load_manifest()["files"] if e.get("expect") == ["duplicate-id"]
    )
    text = (FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8")
    with pytest.raises(UnsafeXmlError):
        parse_xml_safely(text)


def test_unresolved_reference_sample_actually_dangles() -> None:
    entry = next(
        e for e in _load_manifest()["files"] if e.get("expect") == ["unresolved-ref"]
    )
    text = (FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8")
    root = parse_xml_safely(text)
    xml_id_attr = "{http://www.w3.org/XML/1998/namespace}id"
    known_ids = {el.get(xml_id_attr) for el in root.iter() if el.get(xml_id_attr)}
    targets = {
        value.lstrip("#")
        for el in root.iter()
        for attr in ("ref", "target", "wit", "corresp")
        for value in (el.get(attr) or "",)
        if value.startswith("#")
    }
    assert targets - known_ids, "le fichier devait contenir une référence #id cassée"
