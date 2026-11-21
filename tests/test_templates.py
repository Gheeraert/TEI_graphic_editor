"""Les 4 modèles de « Nouveau » (phase 6) sont chacun valides contre le
schéma RelaxNG unique `tei_all` (ADR-0007), conformément au critère
d'acceptation de `docs/ROADMAP.md` §5."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from tei_editor.tei.templates import TEMPLATES, template_text
from tei_editor.tei.xml_safety import safe_xml_parser

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "tei_editor"
    / "data"
    / "schemas"
    / "tei_all"
    / "tei_all.rng"
)


def test_four_templates_are_declared():
    ids = {t.template_id for t in TEMPLATES}
    assert ids == {"minimal", "edition_critique", "theatre", "correspondance"}


def test_each_template_is_well_formed_and_relaxng_valid():
    schema = etree.RelaxNG(etree.parse(str(SCHEMA_PATH)))
    for template in TEMPLATES:
        root = etree.fromstring(template.text.encode("utf-8"), parser=safe_xml_parser())
        assert schema.validate(root.getroottree()), (template.template_id, schema.error_log)


def test_template_text_falls_back_to_minimal_for_unknown_id():
    assert template_text("inconnu") == template_text("minimal")
