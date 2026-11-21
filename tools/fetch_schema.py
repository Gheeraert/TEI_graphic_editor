#!/usr/bin/env python3
"""Télécharge et met en cache le schéma RelaxNG ``tei_all`` officiel pour la
version TEI P5 épinglée en phase 1 (4.12.0, voir ``docs/DECISIONS.md``
ADR-0003 et ADR-0007), puis le copie dans
``src/tei_editor/data/schemas/tei_all/`` avec un fichier de provenance.

Ce script est le seul point d'accès réseau de ce projet pour cette
ressource (comme ``tools/build_catalog.py`` pour le catalogue) : rien dans
l'application elle-même n'accède au réseau (``CLAUDE.md``).

Usage ::

    .venv/Scripts/python.exe tools/fetch_schema.py

Reproductible : à cache inchangé (``.cache/tei/tei_all.rng``), ne refait pas
la requête réseau.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TEI_VERSION = "4.12.0"
SOURCE_URL = (
    f"https://www.tei-c.org/Vault/P5/{TEI_VERSION}/xml/tei/custom/schema/relaxng/tei_all.rng"
)

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / ".cache" / "tei" / "tei_all.rng"
DEST_DIR = ROOT / "src" / "tei_editor" / "data" / "schemas" / "tei_all"
DEST_SCHEMA = DEST_DIR / "tei_all.rng"
DEST_PROVENANCE = DEST_DIR / "PROVENANCE.json"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 (outil, pas l'appli)
        data = response.read()
    dest.write_bytes(data)


def fetch(*, force: bool = False) -> Path:
    if force or not CACHE_PATH.exists():
        _download(SOURCE_URL, CACHE_PATH)
    return CACHE_PATH


def install(cache_path: Path) -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    data = cache_path.read_bytes()
    DEST_SCHEMA.write_bytes(data)
    provenance = {
        "schema": "tei_all.rng (RelaxNG, grammaire TEI complète)",
        "tei_version": f"P5 {TEI_VERSION}",
        "source_url": SOURCE_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "notes": (
            "Schéma précompilé officiel du consortium TEI pour la version "
            "P5 4.12.0, epinglée en phase 1 (voir docs/DECISIONS.md "
            "ADR-0003) et confirmée fonctionnelle (compilation lxml.etree.RelaxNG "
            "réussie, validation vérifiée sur tests/fixtures/tei-samples/). "
            "Remplace le tei_all.rng de 2009 présent dans le dépôt GitHub "
            "TEIC/TEI, signalé obsolète par "
            "tests/fixtures/tei-samples/README.md. Un seul schéma fait "
            "autorité pour tous les profils (docs/DECISIONS.md, nouvel ADR "
            "de la phase 4) : le profil actif ne restreint jamais la "
            "grammaire RelaxNG, seulement la liste blanche de la future "
            "palette de balises."
        ),
    }
    DEST_PROVENANCE.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    cache_path = fetch()
    install(cache_path)
    print(f"Schéma installé : {DEST_SCHEMA} ({DEST_SCHEMA.stat().st_size} octets)")


if __name__ == "__main__":
    main()
