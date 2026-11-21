"""Logique pure des fichiers récents (ajout/dédoublonnage/nettoyage),
sans ``QSettings`` (voir ``tei_editor.prefs.settings``)."""

from __future__ import annotations

from pathlib import Path

from tei_editor.prefs.settings import add_recent_file, prune_missing_recent_files


def test_add_recent_file_puts_new_entry_first() -> None:
    result = add_recent_file(["a.xml", "b.xml"], "c.xml")
    assert result[0] == str(Path("c.xml"))


def test_add_recent_file_deduplicates_existing_entry() -> None:
    result = add_recent_file(["a.xml", "b.xml"], "a.xml")
    assert result == [str(Path("a.xml")), str(Path("b.xml"))]


def test_add_recent_file_truncates_to_max_items() -> None:
    existing = [f"{i}.xml" for i in range(10)]
    result = add_recent_file(existing, "new.xml", max_items=10)
    assert len(result) == 10
    assert result[0] == str(Path("new.xml"))
    assert str(Path("9.xml")) not in result  # le plus ancien est tombé


def test_prune_missing_recent_files_keeps_only_existing(tmp_path: Path) -> None:
    existing_file = tmp_path / "exists.xml"
    existing_file.write_text("<TEI/>", encoding="utf-8")
    missing_file = tmp_path / "gone.xml"

    result = prune_missing_recent_files([str(existing_file), str(missing_file)])

    assert result == [str(existing_file)]
