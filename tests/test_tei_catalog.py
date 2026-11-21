"""Tests sur le catalogue TEI généré (``tools/build_catalog.py``).

Ces tests ne nécessitent pas Qt : ils portent uniquement sur les fichiers
JSON produits dans ``src/tei_editor/data/``. Conformément au critère
d'acceptation de la phase 1 de ``docs/ROADMAP.md`` (« tests sur 10 éléments
clés »), on vérifie ici le catalogue complet, un échantillon représentatif
d'éléments, et la cohérence des quatre profils avec le catalogue.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "tei_editor" / "data"
PROFILES_DIR = DATA_DIR / "profiles"

PROFILE_NAMES = ["tei_all", "edition_textes", "theatre", "edition_critique"]

# Éléments clés devant impérativement figurer dans le catalogue (voir
# docs/ROADMAP.md §3.A2 : en-tête, structure, phrase, apparat critique).
KEY_ELEMENTS = [
    "TEI",
    "teiHeader",
    "text",
    "body",
    "p",
    "persName",
    "app",
    "lem",
    "rdg",
    "div",
    "sp",
]


@pytest.fixture(scope="module")
def catalog() -> dict:
    path = DATA_DIR / "tei_catalog.json"
    assert path.exists(), f"Catalogue absent : {path}. Lancer tools/build_catalog.py."
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def profiles() -> dict[str, dict]:
    result = {}
    for name in PROFILE_NAMES:
        path = PROFILES_DIR / f"{name}.json"
        assert path.exists(), f"Profil absent : {path}."
        with path.open(encoding="utf-8") as fh:
            result[name] = json.load(fh)
    return result


def test_catalog_has_plausible_element_count(catalog: dict) -> None:
    # Le nombre exact d'éléments varie d'une version TEI P5 à l'autre ; on
    # vérifie seulement un ordre de grandeur plausible (TEI P5 en déclare
    # plusieurs centaines).
    assert catalog["element_count"] > 500
    assert len(catalog["elements"]) == catalog["element_count"]


def test_catalog_metadata(catalog: dict) -> None:
    assert catalog["tei_version"]
    assert catalog["source_url"].startswith("https://www.tei-c.org/Vault/P5/")
    assert catalog["tei_version"] in catalog["source_url"]


@pytest.mark.parametrize("ident", KEY_ELEMENTS)
def test_key_elements_exist(catalog: dict, ident: str) -> None:
    assert ident in catalog["elements"], f"Élément clé manquant : {ident}"


def test_div_approx_children_include_head_and_p(catalog: dict) -> None:
    children = set(catalog["elements"]["div"]["children_approx"])
    assert "head" in children
    assert "p" in children


def test_sp_approx_children_include_speaker(catalog: dict) -> None:
    children = set(catalog["elements"]["sp"]["children_approx"])
    assert "speaker" in children


def test_parents_approx_is_inverse_of_children_approx(catalog: dict) -> None:
    els = catalog["elements"]
    # div est un parent approximatif de head (puisque head est un enfant
    # approximatif de div) : vérifie que l'inversion a bien été calculée.
    assert "div" in els["head"]["parents_approx"]
    assert "div" in els["p"]["parents_approx"]


def test_global_attributes_are_not_lost(catalog: dict) -> None:
    # xml:id et xml:lang sont déclarés sur la classe d'attributs att.global,
    # pas directement sur chaque elementSpec : on vérifie qu'ils survivent
    # à la résolution, à la fois au niveau de la classe...
    att_global = catalog["classes"]["att.global"]
    att_global_idents = {a["ident"] for a in att_global["attributes"]}
    assert "xml:id" in att_global_idents
    assert "xml:lang" in att_global_idents

    # ... et au niveau d'un élément concret qui est membre (direct ou
    # transitif) de att.global, p ex. <p> ou <div>.
    for ident in ("p", "div"):
        resolved_idents = {a["ident"] for a in catalog["elements"][ident]["attributes"]}
        assert "xml:id" in resolved_idents, f"xml:id perdu pour <{ident}>"
        assert "xml:lang" in resolved_idents, f"xml:lang perdu pour <{ident}>"


def test_closed_value_lists_are_captured(catalog: dict) -> None:
    # @status sur <availability> a une liste fermée de valeurs (free,
    # restricted, unknown...) : vérifie que ce type d'information n'est pas
    # perdu lors de l'extraction des attributs.
    availability = catalog["elements"]["availability"]
    status_attr = next(
        (a for a in availability["attributes"] if a["ident"] == "status"), None
    )
    assert status_attr is not None
    assert status_attr["closed_values"], "Les valeurs fermées de @status n'ont pas été capturées"
    value_idents = {v["ident"] for v in status_attr["closed_values"]}
    assert "free" in value_idents


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_profile_parses_and_has_groups(profiles: dict[str, dict], name: str) -> None:
    profile = profiles[name]
    assert profile["id"] == name
    assert profile["label"]
    assert profile["groups"], f"Le profil {name} ne contient aucun groupe"


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_profile_elements_exist_in_catalog(
    catalog: dict, profiles: dict[str, dict], name: str
) -> None:
    catalog_idents = set(catalog["elements"])
    profile = profiles[name]
    listed = {ident for group in profile["groups"] for ident in group["elements"]}
    unknown = listed - catalog_idents
    assert not unknown, f"Le profil {name} référence des éléments absents du catalogue : {unknown}"
    assert listed, f"Le profil {name} ne liste aucun élément"


def test_tei_all_profile_covers_the_whole_catalog(
    catalog: dict, profiles: dict[str, dict]
) -> None:
    catalog_idents = set(catalog["elements"])
    profile = profiles["tei_all"]
    listed = {ident for group in profile["groups"] for ident in group["elements"]}
    assert listed == catalog_idents


def test_specialised_profiles_are_proper_subsets(
    catalog: dict, profiles: dict[str, dict]
) -> None:
    catalog_idents = set(catalog["elements"])
    for name in ("edition_textes", "theatre", "edition_critique"):
        listed = {ident for group in profiles[name]["groups"] for ident in group["elements"]}
        assert listed < catalog_idents
        assert len(listed) > 20


def test_theatre_profile_contains_stage_elements(profiles: dict[str, dict]) -> None:
    listed = {ident for group in profiles["theatre"]["groups"] for ident in group["elements"]}
    for ident in ("sp", "speaker", "stage", "castList"):
        assert ident in listed


def test_edition_critique_profile_contains_apparatus_elements(
    profiles: dict[str, dict]
) -> None:
    listed = {
        ident for group in profiles["edition_critique"]["groups"] for ident in group["elements"]
    }
    for ident in ("app", "lem", "rdg", "witness"):
        assert ident in listed
