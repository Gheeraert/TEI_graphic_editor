"""Tests sur ``tei_editor.ui.icons`` : la substitution ``currentColor``
-> couleur du thème (``docs/ROADMAP.md`` §5, phase 8). La partie pure
(substitution d'octets) est testée sans construire de ``QIcon`` réel ;
la construction effective d'un ``QIcon``/``QPixmap`` est testée à part,
avec Qt (``offscreen``)."""

from __future__ import annotations

from tei_editor.ui import icons
from tei_editor.ui.theme import THEME_IDS, foreground_color


def test_colored_svg_bytes_replaces_current_color() -> None:
    svg = icons.colored_svg_bytes("save", "#1f1e1b")
    assert b"currentColor" not in svg
    assert b"#1f1e1b" in svg


def test_colored_svg_bytes_for_action_uses_mapped_icon() -> None:
    svg = icons.colored_svg_bytes_for_action("save", "#f8f8f2")
    assert svg is not None
    assert b"#f8f8f2" in svg
    assert b"currentColor" not in svg


def test_colored_svg_bytes_for_unknown_action_is_none() -> None:
    assert icons.colored_svg_bytes_for_action("inconnue.action", "#000000") is None


def test_colored_svg_bytes_for_both_themes() -> None:
    for theme_id in THEME_IDS:
        color = foreground_color(theme_id)
        svg = icons.colored_svg_bytes_for_action("docks.outline", color)
        assert svg is not None
        assert color.encode("ascii") in svg
        assert b"currentColor" not in svg


def test_load_action_icon_builds_non_null_qicon(qapp) -> None:
    icon = icons.load_action_icon("save", "#1f1e1b")
    assert not icon.isNull()
    pixmap = icon.pixmap(icons.DEFAULT_ICON_SIZE, icons.DEFAULT_ICON_SIZE)
    assert not pixmap.isNull()


def test_load_action_icon_unknown_action_is_null_icon(qapp) -> None:
    icon = icons.load_action_icon("inconnue.action", "#1f1e1b")
    assert icon.isNull()


def test_apply_action_icons_sets_icon_on_actions(qapp) -> None:
    from tei_editor.actions import build_actions
    from PySide6.QtWidgets import QWidget

    parent = QWidget()
    actions = build_actions(parent, profile_ids_and_labels=[("tei_all", "TEI (tout)")])
    icons.apply_action_icons(actions, "#1f1e1b")
    assert not actions.save.icon().isNull()
    assert not actions.tags.wrap_selection.icon().isNull()
    assert not actions.docks.palette.icon().isNull()
