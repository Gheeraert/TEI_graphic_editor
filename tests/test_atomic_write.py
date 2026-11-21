"""Tests de l'écriture atomique (`tei_editor.content.atomic_write`)."""

from __future__ import annotations

from pathlib import Path

from tei_editor.content.atomic_write import atomic_write_text


def test_atomic_write_text_ecrit_le_contenu_et_ne_laisse_aucun_temporaire(tmp_path: Path) -> None:
    cible = tmp_path / "document.xml"
    atomic_write_text(cible, "<TEI/>")

    assert cible.read_text(encoding="utf-8") == "<TEI/>"
    fichiers_restants = {chemin.name for chemin in tmp_path.iterdir()}
    assert fichiers_restants == {"document.xml"}


def test_atomic_write_text_remplace_un_fichier_existant_sans_laisser_de_temporaire(
    tmp_path: Path,
) -> None:
    cible = tmp_path / "document.xml"
    cible.write_text("ancien contenu", encoding="utf-8")

    atomic_write_text(cible, "nouveau contenu")

    assert cible.read_text(encoding="utf-8") == "nouveau contenu"
    fichiers_restants = {chemin.name for chemin in tmp_path.iterdir()}
    assert fichiers_restants == {"document.xml"}
