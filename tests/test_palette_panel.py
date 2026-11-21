"""Tests du dock Palette (phase 5) : filtrage par contexte (catalogue +
profil), repli quand ``children_approx`` est vide."""

from __future__ import annotations

from tei_editor.editor.palette_panel import PalettePanel
from tei_editor.tei.catalog import suggested_elements


def test_suggested_elements_intersecte_enfants_et_profil() -> None:
    # div accepte head/p (entre autres) ; edition_textes les contient.
    suggestions = suggested_elements("div", "edition_textes")
    assert "p" in suggestions
    assert "head" in suggestions


def test_suggested_elements_repli_quand_children_approx_vide() -> None:
    # `p` a un children_approx vide dans le catalogue (ADR-0003) : le
    # repli doit proposer tout le profil actif plutôt qu'une liste vide.
    suggestions = suggested_elements("p", "edition_textes")
    assert suggestions, "le repli doit proposer des éléments, pas une liste vide"
    assert "hi" in suggestions  # élément phrastique du profil edition_textes


def test_suggested_elements_profil_introuvable_replie_sur_tout_le_catalogue() -> None:
    suggestions = suggested_elements("div", "profil-inexistant")
    assert suggestions
    assert "p" in suggestions


def test_palette_panel_reconstruit_les_groupes(qapp) -> None:
    panel = PalettePanel()
    panel.set_context("div", "edition_textes")
    assert panel.tree.topLevelItemCount() > 0
    # Au moins un groupe contient l'élément p, marqué suggéré (gras).
    found = False
    for i in range(panel.tree.topLevelItemCount()):
        group_item = panel.tree.topLevelItem(i)
        for j in range(group_item.childCount()):
            child = group_item.child(j)
            if child.data(0, 256) == "p":  # Qt.ItemDataRole.UserRole == 256
                found = True
                assert child.font(0).bold()
    assert found


def test_palette_panel_filtre_par_recherche(qapp) -> None:
    panel = PalettePanel()
    panel.set_context(None, "edition_textes")
    panel.search_edit.setText("castitem-ne-matche-rien-xyz")
    visible_groups = sum(
        1
        for i in range(panel.tree.topLevelItemCount())
        if not panel.tree.topLevelItem(i).isHidden()
    )
    assert visible_groups == 0
    panel.search_edit.setText("p")
    visible_groups_after = sum(
        1
        for i in range(panel.tree.topLevelItemCount())
        if not panel.tree.topLevelItem(i).isHidden()
    )
    assert visible_groups_after > 0


def test_palette_panel_double_clic_emet_element_chosen(qapp) -> None:
    panel = PalettePanel()
    panel.set_context("div", "edition_textes")
    received = []
    panel.element_chosen.connect(received.append)
    # Cherche l'item "p" dans l'arbre et simule son activation.
    target = None
    for i in range(panel.tree.topLevelItemCount()):
        group_item = panel.tree.topLevelItem(i)
        for j in range(group_item.childCount()):
            child = group_item.child(j)
            if child.data(0, 256) == "p":
                target = child
    assert target is not None
    panel._on_item_activated(target)
    assert received == ["p"]
