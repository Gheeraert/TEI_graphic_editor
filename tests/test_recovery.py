"""Cycle complet autosave/restauration (tei_editor.recovery), sans Qt sauf
pour la détection du dossier par défaut (non testée ici)."""

from __future__ import annotations

from pathlib import Path

from tei_editor.recovery import (
    RecoveryState,
    clear_recovery,
    list_orphan_recoveries,
    load_recovery,
    recovery_key,
    save_recovery,
)


def test_recovery_key_is_stable_and_distinct_from_untitled() -> None:
    assert recovery_key(None) == "untitled"
    assert recovery_key("a.xml") == recovery_key("a.xml")
    assert recovery_key("a.xml") != recovery_key("b.xml")
    assert recovery_key("a.xml") != "untitled"


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    state = RecoveryState(
        file_path=str(tmp_path / "doc.xml"),
        cursor_position=42,
        text="<TEI><p>brouillon</p></TEI>",
        saved_at="2026-11-21T00:00:00+00:00",
    )
    save_recovery(tmp_path, state)

    loaded = load_recovery(tmp_path, state.file_path)
    assert loaded == state


def test_load_recovery_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_recovery(tmp_path, "nothing-here.xml") is None


def test_clear_recovery_removes_draft(tmp_path: Path) -> None:
    state = RecoveryState(file_path="a.xml", cursor_position=0, text="<TEI/>", saved_at="t")
    save_recovery(tmp_path, state)
    assert load_recovery(tmp_path, "a.xml") is not None

    clear_recovery(tmp_path, "a.xml")
    assert load_recovery(tmp_path, "a.xml") is None


def test_clear_recovery_on_missing_draft_is_a_no_op(tmp_path: Path) -> None:
    clear_recovery(tmp_path, "never-saved.xml")  # ne doit pas lever


def test_list_orphan_recoveries_lists_untitled_and_named_drafts(tmp_path: Path) -> None:
    save_recovery(tmp_path, RecoveryState(None, 0, "<TEI/>", "t1"))
    save_recovery(tmp_path, RecoveryState("named.xml", 3, "<TEI><a/></TEI>", "t2"))

    states = list_orphan_recoveries(tmp_path)
    assert len(states) == 2
    file_paths = {state.file_path for state in states}
    assert file_paths == {None, "named.xml"}


def test_list_orphan_recoveries_on_missing_directory_is_empty(tmp_path: Path) -> None:
    assert list_orphan_recoveries(tmp_path / "does-not-exist") == []
