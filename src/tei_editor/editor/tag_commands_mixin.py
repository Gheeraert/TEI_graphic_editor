"""Commandes de la phase 5 (`docs/ROADMAP.md` §5) branchées sur
`MainWindow` : envelopper, insérer (palette), dégrouper, renommer,
scinder/fusionner, générer un ``xml:id``, modifier/retirer un attribut.

Extrait de ``main_window.py`` dans un mixin dédié pour respecter la
limite indicative de ``CLAUDE.md`` (« éviter les fichiers de plus de
~600 lignes ») : ``TagCommandsMixin`` suppose juste que la classe qui
l'utilise porte ``self.editor`` (``XmlTextEditor``), ``self.actions``
(``tei_editor.actions.Actions``) et ``self._update_structural_info()``
(``main_window.py``), exactement comme ``MainWindow``.
"""

from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QMessageBox

from tei_editor.editor.current_element import all_xml_ids, local_name, locate_current_element
from tei_editor.editor.structured_edits import (
    apply_edits_with_cursor,
    can_merge_paragraphs,
    can_split_paragraph,
    generate_unique_xml_id,
    plan_insert_element,
    plan_merge_paragraphs,
    plan_remove_attribute,
    plan_rename,
    plan_set_attribute,
    plan_set_xml_id,
    plan_split_paragraph,
    plan_unwrap,
    plan_wrap_selection,
)
from tei_editor.tei.catalog import is_typically_empty
from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

_XML_ID_ATTR = "{http://www.w3.org/XML/1998/namespace}id"


class TagCommandsMixin:
    """Mixin : toutes les méthodes supposent ``self.editor``/``self.actions``
    et ``self._update_structural_info()`` fournis par ``MainWindow``."""

    # -- Repérage / application communs --------------------------------
    def _current_text_and_location(self):
        text = self.editor.toPlainText()
        offset = self.editor.textCursor().position()
        return text, locate_current_element(text, offset)

    def _apply_structured_edit(self, edits: list, *, final_position: int | None = None) -> None:
        if not edits:
            return
        cursor = self.editor.textCursor()
        apply_edits_with_cursor(cursor, edits, final_position=final_position)
        self.editor.setTextCursor(cursor)
        self._update_structural_info()

    # -- 2/3. Envelopper / insérer (palette ou menu Balises) -------------
    def _wrap_selection_with(self, element_name: str) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return
        edits = plan_wrap_selection(cursor.selectionStart(), cursor.selectionEnd(), element_name)
        self._apply_structured_edit(edits)

    def _wrap_selection(self) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(
                self, "Envelopper la sélection", "Sélectionnez d'abord du texte dans l'éditeur."
            )
            return
        element_name, ok = QInputDialog.getText(
            self, "Envelopper la sélection", "Nom de l'élément TEI à insérer :"
        )
        if not ok or not element_name.strip():
            return
        self._wrap_selection_with(element_name.strip())

    def _on_palette_element_chosen(self, element_name: str) -> None:
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            self._wrap_selection_with(element_name)
            return
        self_closing = is_typically_empty(element_name)
        edits, new_position = plan_insert_element(cursor.position(), element_name, self_closing=self_closing)
        self._apply_structured_edit(edits, final_position=new_position)

    # -- 4. Dégrouper ------------------------------------------------------
    def _unwrap_current_element(self) -> None:
        _text, located = self._current_text_and_location()
        if located is None:
            return
        edits = plan_unwrap(located.span)
        if edits is None:
            return
        self._apply_structured_edit(edits)

    # -- 5. Renommer -------------------------------------------------------
    def _rename_current_element(self) -> None:
        text, located = self._current_text_and_location()
        if located is None:
            return
        old_name = local_name(located.element.tag)
        new_name, ok = QInputDialog.getText(
            self, "Renommer la balise", "Nouveau nom d'élément :", text=old_name
        )
        new_name = new_name.strip()
        if not ok or not new_name or new_name == old_name:
            return
        edits = plan_rename(text, located.span, new_name)
        self._apply_structured_edit(edits)

    # -- 6. Scinder / fusionner --------------------------------------------
    def _split_paragraph(self) -> None:
        _text, located = self._current_text_and_location()
        if located is None or local_name(located.element.tag) != "p":
            return
        offset = self.editor.textCursor().position()
        if not can_split_paragraph(located.span, offset):
            return
        edits = plan_split_paragraph(offset, "p")
        self._apply_structured_edit(edits)

    def _merge_paragraph(self) -> None:
        _text, located = self._current_text_and_location()
        if located is None or local_name(located.element.tag) != "p":
            return
        next_element = located.element.getnext()
        if next_element is None or local_name(next_element.tag) != "p":
            return
        next_span = located.span_of(next_element)
        if next_span is None or not can_merge_paragraphs(located.span, "p", "p"):
            return
        edits = plan_merge_paragraphs(located.span, next_span)
        self._apply_structured_edit(edits)

    # -- 7. Attributs (inspecteur) ------------------------------------------
    def _on_attribute_committed(self, attr_name: str, value: str) -> None:
        text, located = self._current_text_and_location()
        if located is None:
            return
        edits = plan_set_attribute(text, located.span, attr_name, value)
        self._apply_structured_edit(edits)

    def _on_attribute_removed(self, attr_name: str) -> None:
        text, located = self._current_text_and_location()
        if located is None:
            return
        edits = plan_remove_attribute(text, located.span, attr_name)
        self._apply_structured_edit(edits)

    # -- 8. Génération de xml:id --------------------------------------------
    def _on_generate_xml_id(self) -> None:
        text, located = self._current_text_and_location()
        if located is None:
            return
        try:
            root = parse_xml_safely(text)
        except UnsafeXmlError:
            return
        existing_ids = all_xml_ids(root)
        new_id = generate_unique_xml_id(local_name(located.element.tag), existing_ids)
        edits = plan_set_xml_id(text, located.span, new_id)
        self._apply_structured_edit(edits)

    # -- Activation/désactivation des actions --------------------------------
    def _update_tag_actions_enabled(self, located) -> None:
        tag_actions = self.actions.tags
        if located is None:
            tag_actions.unwrap.setEnabled(False)
            tag_actions.rename.setEnabled(False)
            tag_actions.split_paragraph.setEnabled(False)
            tag_actions.merge_paragraph.setEnabled(False)
            tag_actions.generate_xml_id.setEnabled(False)
            return
        span = located.span
        tag_actions.unwrap.setEnabled(span.end_tag_start is not None)
        tag_actions.rename.setEnabled(True)
        name = local_name(located.element.tag)
        offset = self.editor.textCursor().position()
        tag_actions.split_paragraph.setEnabled(name == "p" and can_split_paragraph(span, offset))
        next_element = located.element.getnext()
        next_span = located.span_of(next_element) if next_element is not None else None
        can_merge = (
            name == "p"
            and next_element is not None
            and local_name(next_element.tag) == "p"
            and next_span is not None
            and can_merge_paragraphs(span, "p", "p")
        )
        tag_actions.merge_paragraph.setEnabled(can_merge)
        has_xml_id = located.element.get(_XML_ID_ATTR) is not None
        tag_actions.generate_xml_id.setEnabled(not has_xml_id)
