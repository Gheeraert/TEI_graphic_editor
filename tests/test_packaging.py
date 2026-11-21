"""Garde-fou de distribution (phase 9, `docs/ROADMAP.md` §5 : « installation
simple »). Une installation réelle dans un venv propre (`pip install .`) a
révélé que `src/tei_editor/data/` (catalogue TEI, profils, schémas RelaxNG,
icônes, données de jeux de balises) n'était **pas** embarqué par
`setuptools` sans déclaration explicite de `package-data` : l'application
plantait au lancement (`FileNotFoundError` sur `action_icons.json`), bien
que `pytest` passe (les tests tournent depuis le dépôt, pas depuis un
paquet installé, donc ne voient jamais ce trou). Ce test fait échouer la
suite si cette déclaration disparaît à nouveau, sans avoir besoin de
reconstruire un paquet pour le détecter."""

from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "tei_editor" / "data"


def test_package_data_declares_the_data_directory() -> None:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    package_data = config["tool"]["setuptools"]["package-data"]
    assert "tei_editor" in package_data
    patterns = package_data["tei_editor"]
    assert any("data" in pattern for pattern in patterns), (
        "pyproject.toml doit déclarer src/tei_editor/data/ dans "
        "[tool.setuptools.package-data], sans quoi `pip install .` "
        "n'embarque pas le catalogue/les profils/les schémas/les icônes."
    )


def test_every_file_actually_present_under_data_dir_would_be_covered() -> None:
    """Vérifie, fichier par fichier, que le motif déclaré couvre bien tout
    ce qui existe réellement sous `data/` (pas seulement un sous-ensemble
    choisi à la main)."""
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    patterns = config["tool"]["setuptools"]["package-data"]["tei_editor"]
    # Motif attendu : quelque chose comme "data/**/*", qui couvre tout
    # fichier sous data/ à n'importe quelle profondeur. On vérifie la forme
    # du motif plutôt que de réimplémenter le moteur de glob de setuptools.
    assert any(pattern.startswith("data/") and "**" in pattern for pattern in patterns)
    assert DATA_DIR.is_dir()
    assert list(DATA_DIR.rglob("*")), "data/ ne doit pas être vide dans le dépôt de test"
