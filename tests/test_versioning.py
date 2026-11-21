"""Tests du cycle archivage/liste/purge (`tei_editor.content.versioning`)."""

from __future__ import annotations

from pathlib import Path

from tei_editor.content.versioning import (
    archive_previous_version,
    list_versions,
    purge_versions,
    versions_to_purge,
)


def test_cycle_archive_liste_purge(tmp_path: Path) -> None:
    document = tmp_path / "pièce.xml"
    document.write_text("version 1", encoding="utf-8")

    first = archive_previous_version(document)
    assert first.archived_path is not None
    assert first.archived_path.read_text(encoding="utf-8") == "version 1"
    assert first.versions == ((1, first.archived_path),)
    assert first.should_offer_purge is False

    document.write_text("version 2", encoding="utf-8")
    second = archive_previous_version(document)
    assert second.versions[-1][0] == 2

    versions = list_versions(document)
    assert [number for number, _path in versions] == [1, 2]

    a_purger = versions_to_purge(versions, keep=1)
    assert [number for number, _path in a_purger] == [1]

    purge_versions(a_purger)
    restantes = list_versions(document)
    assert [number for number, _path in restantes] == [2]


def test_archive_previous_version_sans_fichier_existant(tmp_path: Path) -> None:
    document = tmp_path / "absent.xml"
    result = archive_previous_version(document)
    assert result.archived_path is None
    assert result.versions == ()
    assert result.should_offer_purge is False


def test_versions_to_purge_sans_depassement_ne_renvoie_rien() -> None:
    versions = [(1, Path("a")), (2, Path("b"))]
    assert versions_to_purge(versions, keep=20) == []
