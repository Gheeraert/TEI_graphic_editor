"""Commandes composites de la phase 7 (`docs/ROADMAP.md` §5, phase 7)
branchées sur `MainWindow` : grouper en choix, insérer une liste de
personnages, marquer un vers partagé, insérer une leçon (app/lem/rdg).

Mixin séparé de `editor/tag_commands_mixin.py` (phase 5) pour rester sous
la limite indicative de ``CLAUDE.md`` (« éviter les fichiers de plus de
~600 lignes ») : ``SnippetCommandsMixin`` suppose comme lui que la classe
qui l'utilise porte ``self.editor`` (``XmlTextEditor``), ``self.actions``
(``tei_editor.actions.Actions``) et ``self._apply_structured_edit``/
``self._current_text_and_location`` (déjà fournis par
``TagCommandsMixin``, phase 5, dont celui-ci dépend)."""

from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QMessageBox

from tei_editor.editor.current_element import local_name
from tei_editor.editor.snippets import (
    load_choice_pairs,
    plan_group_as_choice,
    plan_insert_apparatus,
    plan_insert_cast_list,
    plan_mark_shared_verse,
)


class SnippetCommandsMixin:
    """Mixin : toutes les méthodes supposent ``self.editor``/``self.actions``
    et les aides de ``TagCommandsMixin`` fournis par ``MainWindow``."""

    # -- 1. Grouper en choix -------------------------------------------------
    def _group_as_choice(self) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(
                self,
                "Grouper en choix…",
                "Sélectionnez d'abord le texte de la leçon retenue (premier élément de la paire).",
            )
            return
        pairs = load_choice_pairs()
        if not pairs:
            QMessageBox.warning(
                self, "Grouper en choix…", "Aucune paire choice disponible (data/snippets/choice_pairs.json)."
            )
            return
        labels = [pair["label"] for pair in pairs]
        label, ok = QInputDialog.getItem(self, "Grouper en choix…", "Paire à utiliser :", labels, 0, False)
        if not ok:
            return
        pair = next(p for p in pairs if p["label"] == label)
        edits, cursor_position = plan_group_as_choice(
            cursor.selectionStart(), cursor.selectionEnd(), pair["first"], pair["second"]
        )
        self._apply_structured_edit(edits, final_position=cursor_position)

    # -- 2. Insérer une liste de personnages ---------------------------------
    def _insert_cast_list(self) -> None:
        role_count, ok = QInputDialog.getInt(
            self, "Insérer une liste de personnages…", "Nombre de personnages :", 2, 1, 50
        )
        if not ok:
            return
        offset = self.editor.textCursor().position()
        edits, cursor_position = plan_insert_cast_list(offset, role_count)
        self._apply_structured_edit(edits, final_position=cursor_position)

    # -- 3. Marquer un vers partagé -------------------------------------------
    def _mark_shared_verse(self) -> None:
        text, located = self._current_text_and_location()
        if located is None or local_name(located.element.tag) != "l":
            QMessageBox.information(
                self, "Marquer un vers partagé", "Placez le curseur dans un vers (<l>) à scinder entre deux répliques."
            )
            return
        l_span = located.span
        offset = self.editor.textCursor().position()
        if l_span.end_tag_start is None or not (l_span.content_start < offset < l_span.content_end):
            QMessageBox.information(
                self,
                "Marquer un vers partagé",
                "Placez le curseur à l'intérieur du texte du vers, au point de partage entre les deux répliques.",
            )
            return
        sp_element = located.element.getparent()
        while sp_element is not None and local_name(sp_element.tag) != "sp":
            sp_element = sp_element.getparent()
        if sp_element is None:
            QMessageBox.information(
                self, "Marquer un vers partagé", "Ce vers n'appartient à aucune réplique (<sp>)."
            )
            return
        next_sp = sp_element.getnext()
        while next_sp is not None and local_name(next_sp.tag) != "sp":
            next_sp = next_sp.getnext()
        if next_sp is None:
            QMessageBox.information(
                self,
                "Marquer un vers partagé",
                "Aucune réplique suivante (<sp>) trouvée pour y placer la suite du vers.",
            )
            return
        next_sp_span = located.span_of(next_sp)
        if next_sp_span is None:
            return
        insert_offset = next_sp_span.content_start
        first_child = next(iter(next_sp), None)
        if first_child is not None and local_name(first_child.tag) == "speaker":
            speaker_span = located.span_of(first_child)
            if speaker_span is not None and speaker_span.end_tag_end is not None:
                insert_offset = speaker_span.end_tag_end
        existing_n = located.element.get("n") or ""
        n_value, ok = QInputDialog.getText(
            self,
            "Marquer un vers partagé",
            "Numéro de vers (@n, commun aux deux fragments) :",
            text=existing_n,
        )
        n_value = n_value.strip()
        if not ok or not n_value:
            return
        edits = plan_mark_shared_verse(text, l_span, offset, insert_offset, n_value)
        self._apply_structured_edit(edits)

    # -- 4. Insérer une leçon (app/lem/rdg) -----------------------------------
    def _insert_apparatus(self) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(
                self,
                "Insérer une leçon (app/lem/rdg)…",
                "Sélectionnez d'abord le texte de la leçon retenue (lem).",
            )
            return
        rdg_count, ok = QInputDialog.getInt(
            self, "Insérer une leçon (app/lem/rdg)…", "Nombre de leçons rejetées (rdg) :", 1, 1, 10
        )
        if not ok:
            return
        edits, cursor_position = plan_insert_apparatus(
            cursor.selectionStart(), cursor.selectionEnd(), rdg_count
        )
        self._apply_structured_edit(edits, final_position=cursor_position)
