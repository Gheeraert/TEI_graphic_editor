"""Tests de la résolution de licences (`tei_editor.tei.licenses`)."""

from __future__ import annotations

from tei_editor.tei.licenses import SPDX_LICENSES, resolve_license


def test_la_liste_de_licences_nest_pas_vide_et_porte_nom_et_url() -> None:
    assert SPDX_LICENSES
    for spdx_id, (name, url) in SPDX_LICENSES.items():
        assert spdx_id
        assert name
        assert url.startswith("https://")


def test_resolve_license_avec_identifiant_spdx_connu_ecrase_le_texte_libre() -> None:
    resolved = resolve_license(spdx_id="CC-BY-4.0", name="Autre nom", url="https://exemple.invalid")
    assert resolved.name == "CC BY 4.0"
    assert resolved.url == "https://creativecommons.org/licenses/by/4.0/"


def test_resolve_license_sans_identifiant_connu_retombe_sur_le_texte_libre() -> None:
    resolved = resolve_license(spdx_id=None, name="Licence maison", url="https://exemple.invalid")
    assert resolved.name == "Licence maison"
    assert resolved.url == "https://exemple.invalid"


def test_resolve_license_sans_rien_renvoie_des_champs_vides() -> None:
    resolved = resolve_license(spdx_id=None, name=None, url=None)
    assert resolved.name is None
    assert resolved.url is None
