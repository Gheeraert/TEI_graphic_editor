"""Chargement minimal des profils TEI générés en phase 1
(``src/tei_editor/data/profiles/*.json``) : juste assez pour peupler le
sous-menu « Profil actif » (phase 3). Le contenu détaillé d'un profil
(groupes de balises...) n'est consommé qu'à partir de la phase 5/7 — le
catalogue fait foi, pas une liste codée en dur (``CLAUDE.md``).
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROFILES_DIR = DATA_DIR / "profiles"

#: Ordre d'affichage privilégié (ADR-0005) ; tout profil supplémentaire
#: trouvé sur disque est ajouté ensuite, trié par identifiant.
_PREFERRED_ORDER = ("tei_all", "edition_textes", "theatre", "edition_critique")


def list_profiles(profiles_dir: Path | None = None) -> list[tuple[str, str]]:
    """Renvoie la liste ``(id, label)`` des profils disponibles sur disque."""
    directory = profiles_dir or PROFILES_DIR
    found: dict[str, str] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        profile_id = data.get("id", path.stem)
        found[profile_id] = data.get("label", profile_id)

    ordered_ids = [pid for pid in _PREFERRED_ORDER if pid in found]
    ordered_ids += sorted(pid for pid in found if pid not in _PREFERRED_ORDER)
    return [(pid, found[pid]) for pid in ordered_ids]
