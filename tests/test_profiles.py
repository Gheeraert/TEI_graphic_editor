"""Vérifie le critère « profils personnalisables » de la phase 7
(`docs/ROADMAP.md` §5) : déposer un nouveau fichier JSON dans
``data/profiles/`` (sans toucher au code) doit suffire à le faire
apparaître dans ``list_profiles()``, donc dans le sous-menu « Profil
actif » (déjà dynamique depuis la phase 3). Voir aussi ``docs/PROFILS.md``.
"""

from __future__ import annotations

import json

from tei_editor.tei.profiles import list_profiles


def test_list_profiles_couvre_les_quatre_profils_fournis() -> None:
    ids = [profile_id for profile_id, _label in list_profiles()]
    for expected in ("tei_all", "edition_textes", "theatre", "edition_critique"):
        assert expected in ids


def test_list_profiles_detecte_un_nouveau_profil_depose_sur_disque(tmp_path) -> None:
    (tmp_path / "mon_profil.json").write_text(
        json.dumps(
            {
                "id": "mon_profil",
                "label": "Mon profil",
                "groups": [{"id": "structure", "label": "Structure", "elements": ["div", "p"]}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    profiles = list_profiles(tmp_path)
    assert ("mon_profil", "Mon profil") in profiles


def test_list_profiles_ignore_un_fichier_json_invalide(tmp_path) -> None:
    (tmp_path / "casse.json").write_text("{ pas du json valide", encoding="utf-8")
    (tmp_path / "valide.json").write_text(
        json.dumps({"id": "valide", "label": "Valide", "groups": []}), encoding="utf-8"
    )
    profiles = list_profiles(tmp_path)
    ids = [profile_id for profile_id, _label in profiles]
    assert ids == ["valide"]
