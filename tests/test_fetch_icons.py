"""Tests sur le jeu d'icônes Lucide récupéré par ``tools/fetch_icons.py``
(``docs/ROADMAP.md`` §5, phase 8). Comme ``tests/test_tei_catalog.py``
pour le catalogue, ces tests portent sur les fichiers committés dans
``src/tei_editor/data/icons/`` (pas un nouveau téléchargement réseau à
chaque exécution de la suite)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "src" / "tei_editor" / "data" / "icons"

sys.path.insert(0, str(ROOT / "tools"))
import fetch_icons  # noqa: E402


def test_action_icons_json_matches_tool_mapping() -> None:
    data = json.loads((ICONS_DIR / "action_icons.json").read_text(encoding="utf-8"))
    assert data == fetch_icons.ACTION_ICONS


def test_every_mapped_icon_file_is_present_and_loadable() -> None:
    data = json.loads((ICONS_DIR / "action_icons.json").read_text(encoding="utf-8"))
    assert data, "la correspondance action -> icône ne doit pas être vide"
    for action_name, icon_name in data.items():
        svg_path = ICONS_DIR / f"{icon_name}.svg"
        assert svg_path.is_file(), f"icône manquante pour {action_name} : {icon_name}.svg"
        content = svg_path.read_bytes()
        assert b"<svg" in content
        assert b"currentColor" in content


def test_license_file_present_with_isc_and_mit_notices() -> None:
    license_text = (ICONS_DIR / "LICENSE").read_text(encoding="utf-8")
    assert "ISC License" in license_text
    assert "MIT License" in license_text


def test_provenance_lists_every_icon_and_substitutions() -> None:
    provenance = json.loads((ICONS_DIR / "PROVENANCE.json").read_text(encoding="utf-8"))
    assert provenance["icon_set"] == "Lucide"
    icon_names = {entry["lucide_name"] for entry in provenance["icons"]}
    assert icon_names == set(fetch_icons.ACTION_ICONS.values())
    for entry in provenance["icons"]:
        assert entry["source_url"].startswith(
            "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/"
        )
    # Les substitutions documentées doivent correspondre à des actions
    # réellement mappées.
    for action_name in provenance["substitutions"]:
        assert action_name in fetch_icons.ACTION_ICONS
