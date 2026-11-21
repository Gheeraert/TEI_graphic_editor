"""Tests Qt (hors écran) du dock « Plan »."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from tei_editor.editor.outline import build_outline
from tei_editor.editor.outline_panel import OutlinePanel
from tei_editor.tei.xml_safety import parse_xml_safely

DOC = (
    "<TEI>\n"
    "  <teiHeader/>\n"
    "  <text>\n"
    "    <body>\n"
    "      <div>\n"
    "        <p>Paragraphe.</p>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_outline_panel_construit_un_item_par_noeud(qapp: QApplication) -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    panel = OutlinePanel()
    panel.set_outline(outline)
    assert panel.topLevelItemCount() == 1
    tei_item = panel.topLevelItem(0)
    assert tei_item.childCount() == 2  # teiHeader, text


def test_outline_panel_clic_emet_jump_requested(qapp: QApplication) -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    panel = OutlinePanel()
    panel.set_outline(outline)
    received = []
    panel.jump_requested.connect(received.append)
    tei_item = panel.topLevelItem(0)
    panel._on_item_activated(tei_item)
    assert received == [1]


def test_outline_panel_select_line_selectionne_le_noeud_le_plus_proche(qapp: QApplication) -> None:
    root = parse_xml_safely(DOC)
    outline = build_outline(root)
    panel = OutlinePanel()
    panel.set_outline(outline)
    # Ligne du <p> (non structurant, absent du plan) : doit sélectionner
    # son plus proche ancêtre structurant, <div>.
    panel.select_line(6)
    current = panel.currentItem()
    assert current is not None
    assert current.text(0) == "div"
