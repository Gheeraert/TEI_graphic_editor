#!/usr/bin/env python3
"""Télécharge et met en cache le jeu d'icônes SVG Lucide (licence ISC,
voir ``docs/DECISIONS.md`` ADR-0010) utilisé par les ``QAction`` de
l'interface (phase 8, ``docs/ROADMAP.md`` §5).

Même patron que ``tools/fetch_schema.py``/``tools/build_catalog.py`` :
cache local ``.cache/tei/icons/`` (non versionné), résultat committé
dans ``src/tei_editor/data/icons/``. Rien dans l'application elle-même
n'accède au réseau (``CLAUDE.md``) : seul ce script le fait.

Usage ::

    .venv/Scripts/python.exe tools/fetch_icons.py
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache" / "tei" / "icons"
DEST_DIR = ROOT / "src" / "tei_editor" / "data" / "icons"
LICENSE_URL = "https://raw.githubusercontent.com/lucide-icons/lucide/main/LICENSE"
ICON_URL_TEMPLATE = "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg"

# Correspondance action -> icône Lucide (docs/ROADMAP.md §5, phase 8).
# Certains noms suggérés par la roadmap n'existent plus/pas dans le jeu
# Lucide actuel : substitutions documentées ci-dessous et dans
# PROVENANCE.json (champ "substitutions").
ACTION_ICONS: dict[str, str] = {
    "new": "file-plus",
    "open_": "folder-open",
    "save": "save",
    "save_as": "save-all",
    "export": "download",
    "quit_": "log-out",
    "undo": "undo-2",
    "redo": "redo-2",
    "cut": "scissors",
    "copy": "copy",
    "paste": "clipboard-paste",
    "find_replace": "search",
    "goto_line": "move-right",
    "tags.wrap_selection": "square-code",
    "tags.unwrap": "unlink",
    "tags.rename": "pencil",
    "tags.split_paragraph": "split",
    "tags.merge_paragraph": "merge",
    "tags.generate_xml_id": "hash",
    "snippets.group_as_choice": "shuffle",
    "snippets.insert_cast_list": "users",
    "snippets.mark_shared_verse": "columns-2",
    "snippets.insert_apparatus": "layers",
    "docks.outline": "list-tree",
    "docks.inspector": "sliders-horizontal",
    "docks.problems": "triangle-exclamation-point",
    "docks.palette": "palette",
    "zoom_in": "zoom-in",
    "zoom_out": "zoom-out",
    "zoom_reset": "scan",
    "themes.clair": "sun",
    "themes.sombre": "moon",
    "validate": "circle-check-big",
    "header_wizard": "book-open",
    "preferences": "settings",
    "about": "info",
}

# Nom de la roadmap -> nom réellement récupéré, quand différent
# (icône absente du jeu Lucide actuel sous ce nom exact).
SUBSTITUTIONS: dict[str, dict[str, str]] = {
    "tags.generate_xml_id": {
        "nom_suggere": "fingerprint",
        "nom_retenu": "hash",
        "raison": "« fingerprint » n'existe pas dans le jeu Lucide actuel ; "
        "« hash » était la seconde option proposée par la roadmap.",
    },
    "snippets.mark_shared_verse": {
        "nom_suggere": "split-square-horizontal",
        "nom_retenu": "columns-2",
        "raison": "« split-square-horizontal » n'existe pas dans le jeu Lucide "
        "actuel ; « columns-2 » était la seconde option proposée par la roadmap.",
    },
    "docks.problems": {
        "nom_suggere": "triangle-alert",
        "nom_retenu": "triangle-exclamation-point",
        "raison": "« triangle-alert » (et « alert-triangle ») n'existent plus "
        "dans le jeu Lucide actuel ; « triangle-exclamation-point » est le "
        "triangle d'avertissement équivalent dans la version courante.",
    },
    "validate": {
        "nom_suggere": "check-circle-2",
        "nom_retenu": "circle-check-big",
        "raison": "« check-circle-2 »/« check-circle » n'existent plus sous ce "
        "nom ; « circle-check-big » est l'équivalent actuel (coche dans un "
        "cercle, variante épaisse).",
    },
}


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 (outil, pas l'appli)
        return response.read()


def fetch(*, force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    license_cache = CACHE_DIR / "LICENSE"
    if force or not license_cache.exists():
        license_cache.write_bytes(_download(LICENSE_URL))

    icon_names = sorted(set(ACTION_ICONS.values()))
    for name in icon_names:
        cache_path = CACHE_DIR / f"{name}.svg"
        if force or not cache_path.exists():
            url = ICON_URL_TEMPLATE.format(name=name)
            cache_path.write_bytes(_download(url))


def install() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    icon_names = sorted(set(ACTION_ICONS.values()))
    for name in icon_names:
        cache_path = CACHE_DIR / f"{name}.svg"
        (DEST_DIR / f"{name}.svg").write_bytes(cache_path.read_bytes())

    (DEST_DIR / "LICENSE").write_bytes((CACHE_DIR / "LICENSE").read_bytes())

    (DEST_DIR / "action_icons.json").write_text(
        json.dumps(ACTION_ICONS, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance = {
        "icon_set": "Lucide",
        "license": "ISC (voir LICENSE ; certaines icônes dérivées du projet "
        "Feather portent en plus une notice MIT, listée nommément dans ce "
        "même fichier LICENSE)",
        "source_repository": "https://github.com/lucide-icons/lucide",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "icons": [
            {
                "lucide_name": name,
                "source_url": ICON_URL_TEMPLATE.format(name=name),
            }
            for name in icon_names
        ],
        "substitutions": SUBSTITUTIONS,
        "notes": (
            "Chaque action de l'interface (tei_editor.actions) est associée à "
            "une icône Lucide via action_icons.json, pas codée en dur dans un "
            "widget (CLAUDE.md : données externalisées). Les SVG utilisent "
            "stroke=\"currentColor\" : tei_editor.ui.icons substitue cette "
            "chaîne par la couleur de premier plan du thème actif, en mémoire, "
            "au chargement (voir ADR phase 8)."
        ),
    }
    (DEST_DIR / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    fetch()
    install()
    icon_names = sorted(set(ACTION_ICONS.values()))
    print(f"{len(icon_names)} icônes installées dans {DEST_DIR}")


if __name__ == "__main__":
    main()
