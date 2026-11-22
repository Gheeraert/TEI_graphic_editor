"""Fenêtre principale : assemble les modules de la phase 3 (menus, éditeur
de texte XML, barre d'état, préférences, autosave) sans en porter la
logique elle-même — chaque fonctionnalité vit dans son propre module
(``CLAUDE.md``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
)

from tei_editor import recovery
from tei_editor.actions import Actions, build_actions
from tei_editor.editor.current_element import all_xml_ids, local_name, locate_current_element
from tei_editor.editor.diagnostics import SEVERITY_ERROR, SEVERITY_WARNING, compute_diagnostics
from tei_editor.editor.diagnostics_overlay import apply_diagnostic_highlights
from tei_editor.editor.inspector_panel import InspectorPanel
from tei_editor.editor.outline import build_outline
from tei_editor.editor.outline_panel import OutlinePanel
from tei_editor.editor.palette_panel import PalettePanel
from tei_editor.editor.problems_panel import ProblemsPanel
from tei_editor.editor.status_bar import EditorStatusBar
from tei_editor.editor.snippet_commands_mixin import SnippetCommandsMixin
from tei_editor.editor.tag_commands_mixin import TagCommandsMixin
from tei_editor.editor.text_editor import XmlTextEditor
from tei_editor.editor.xpath import current_xpath
from tei_editor.find_replace_dialog import FindReplaceDialog
from tei_editor.menus import Menus, build_menu_bar, rebuild_recent_files_menu
from tei_editor.prefs import settings as prefs
from tei_editor.prefs.preferences_dialog import PreferencesDialog
from tei_editor.header_dialog.wizard import HeaderWizardDialog
from tei_editor.tei.profiles import list_profiles
from tei_editor.tei.templates import template_text
from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely
from tei_editor.ui.icons import apply_action_icons
from tei_editor.ui.theme import foreground_color, stylesheet_for
from tei_editor.ui.toolbars import Toolbars, build_toolbars
from tei_editor.ui.tooltips import apply_tooltips_with_shortcuts
from tei_editor.wysiwyg.editor_widget import WysiwygEditor
from tei_editor.wysiwyg.xml_adapter import (
    blocks_to_xml,
    find_body_element,
    replace_body_in_document,
    xml_to_blocks,
)

APP_TITLE = "TIGRE — Éditeur graphique de TEI"
STRUCTURAL_UPDATE_DEBOUNCE_MS = 400


class MainWindow(SnippetCommandsMixin, TagCommandsMixin, QMainWindow):
    def __init__(self, settings=None, recovery_dir: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1024, 768)

        self.settings = settings if settings is not None else prefs.get_settings()
        self.recovery_dir = Path(recovery_dir) if recovery_dir is not None else recovery.default_recovery_directory()

        self.editor = XmlTextEditor(self)
        self.wysiwyg_editor = WysiwygEditor(self)
        self._view_stack = QStackedWidget(self)
        self._view_stack.addWidget(self.editor)
        self._view_stack.addWidget(self.wysiwyg_editor)
        self.setCentralWidget(self._view_stack)

        self.status_bar = EditorStatusBar(self)
        self.setStatusBar(self.status_bar)

        self._profile_choices = list_profiles()
        self._profile_labels = dict(self._profile_choices)
        self.actions: Actions = build_actions(self, profile_ids_and_labels=self._profile_choices)
        self.menus: Menus = build_menu_bar(self.menuBar(), self.actions)
        self.toolbars: Toolbars = build_toolbars(self, self.actions)
        apply_tooltips_with_shortcuts(self.actions)

        self._build_docks()
        self._connect_actions()
        self._restore_geometry()
        self._apply_theme(prefs.get_theme(self.settings))
        self._apply_active_profile(prefs.get_active_profile(self.settings))
        self._refresh_recent_files_menu()

        self._structural_timer = QTimer(self)
        self._structural_timer.setSingleShot(True)
        self._structural_timer.setInterval(STRUCTURAL_UPDATE_DEBOUNCE_MS)
        self._structural_timer.timeout.connect(self._update_structural_info)
        self.editor.textChanged.connect(self._schedule_structural_update)
        self.editor.cursorPositionChanged.connect(self._schedule_structural_update)
        self.editor.cursorPositionChanged.connect(self._update_cursor_position_label)

        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave_tick)
        self._configure_autosave()

        self._find_dialog: FindReplaceDialog | None = None

        self._update_cursor_position_label()
        self._update_structural_info()
        self._maybe_offer_recovery(None)

    # -- Construction -------------------------------------------------------
    def _build_docks(self) -> None:
        self.outline_dock = QDockWidget("Plan", self)
        self.outline_dock.setObjectName("dock_plan")
        self.outline_dock.setAccessibleName("Panneau Plan")
        self.outline_panel = OutlinePanel(self.outline_dock)
        self.outline_dock.setWidget(self.outline_panel)
        self.outline_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.outline_dock)
        self.outline_panel.jump_requested.connect(self._goto_outline_line)

        self.inspector_dock = QDockWidget("Inspecteur", self)
        self.inspector_dock.setObjectName("dock_inspecteur")
        self.inspector_dock.setAccessibleName("Panneau Inspecteur")
        self.inspector_panel = InspectorPanel(self.inspector_dock)
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector_dock)
        self.inspector_panel.attribute_committed.connect(self._on_attribute_committed)
        self.inspector_panel.attribute_removed.connect(self._on_attribute_removed)
        self.inspector_panel.generate_xml_id_requested.connect(self._on_generate_xml_id)

        self.problems_dock = QDockWidget("Problèmes", self)
        self.problems_dock.setObjectName("dock_problemes")
        self.problems_dock.setAccessibleName("Panneau Problèmes")
        self.problems_panel = ProblemsPanel(self.problems_dock)
        self.problems_dock.setWidget(self.problems_panel)
        self.problems_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.problems_dock)
        self.problems_panel.jump_requested.connect(self._goto_problem_position)

        self.palette_dock = QDockWidget("Palette", self)
        self.palette_dock.setObjectName("dock_palette")
        self.palette_dock.setAccessibleName("Panneau Palette")
        self.palette_panel = PalettePanel(self.palette_dock)
        self.palette_dock.setWidget(self.palette_panel)
        self.palette_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.palette_dock)
        self.palette_panel.element_chosen.connect(self._on_palette_element_chosen)

        self.actions.docks.outline.toggled.connect(self.outline_dock.setVisible)
        self.actions.docks.inspector.toggled.connect(self.inspector_dock.setVisible)
        self.actions.docks.problems.toggled.connect(self.problems_dock.setVisible)
        self.actions.docks.palette.toggled.connect(self.palette_dock.setVisible)
        self.outline_dock.visibilityChanged.connect(self.actions.docks.outline.setChecked)
        self.inspector_dock.visibilityChanged.connect(self.actions.docks.inspector.setChecked)
        self.problems_dock.visibilityChanged.connect(self.actions.docks.problems.setChecked)
        self.palette_dock.visibilityChanged.connect(self.actions.docks.palette.setChecked)

    def _connect_actions(self) -> None:
        actions = self.actions

        for template_id, template_action in actions.new_templates.by_id.items():
            template_action.triggered.connect(partial(self._new_document_from_template, template_id))
        actions.open.triggered.connect(self._open_file_dialog)
        actions.save.triggered.connect(self._save_file)
        actions.save_as.triggered.connect(self._save_file_as)
        actions.export.triggered.connect(self._export_copy)
        actions.quit.triggered.connect(self.close)

        actions.undo.triggered.connect(self.editor.undo)
        actions.redo.triggered.connect(self.editor.redo)
        actions.cut.triggered.connect(self.editor.cut)
        actions.copy.triggered.connect(self.editor.copy)
        actions.paste.triggered.connect(self.editor.paste)
        actions.find_replace.triggered.connect(self._open_find_replace)
        actions.goto_line.triggered.connect(self._goto_line)

        document = self.editor.document()
        actions.undo.setEnabled(False)
        actions.redo.setEnabled(False)
        actions.copy.setEnabled(False)
        actions.cut.setEnabled(False)
        document.undoAvailable.connect(actions.undo.setEnabled)
        document.redoAvailable.connect(actions.redo.setEnabled)
        self.editor.copyAvailable.connect(actions.copy.setEnabled)
        self.editor.copyAvailable.connect(actions.cut.setEnabled)

        actions.tags.wrap_selection.setEnabled(False)
        self.editor.copyAvailable.connect(actions.tags.wrap_selection.setEnabled)
        actions.tags.wrap_selection.triggered.connect(self._wrap_selection)
        actions.tags.unwrap.triggered.connect(self._unwrap_current_element)
        actions.tags.rename.triggered.connect(self._rename_current_element)
        actions.tags.split_paragraph.triggered.connect(self._split_paragraph)
        actions.tags.merge_paragraph.triggered.connect(self._merge_paragraph)
        actions.tags.generate_xml_id.triggered.connect(self._on_generate_xml_id)
        actions.snippets.group_as_choice.triggered.connect(self._group_as_choice)
        actions.snippets.insert_cast_list.triggered.connect(self._insert_cast_list)
        actions.snippets.mark_shared_verse.triggered.connect(self._mark_shared_verse)
        actions.snippets.insert_apparatus.triggered.connect(self._insert_apparatus)

        actions.wysiwyg.toggle.toggled.connect(self._on_wysiwyg_toggled)

        actions.zoom_in.triggered.connect(self.editor.zoom_editor_in)
        actions.zoom_out.triggered.connect(self.editor.zoom_editor_out)
        actions.zoom_reset.triggered.connect(self.editor.zoom_editor_reset)

        for theme_id, theme_action in actions.themes.by_name.items():
            theme_action.triggered.connect(partial(self._on_theme_chosen, theme_id))

        actions.validate.triggered.connect(self._validate_document)
        for profile_id, profile_action in actions.profiles.by_id.items():
            profile_action.triggered.connect(partial(self._on_profile_chosen, profile_id))
        actions.header_wizard.triggered.connect(self._open_header_wizard)
        actions.preferences.triggered.connect(self._open_preferences)

        actions.about.triggered.connect(self._show_about)

    # -- Nouveau / ouverture / enregistrement --------------------------------
    def _confirm_discard_changes(self) -> bool:
        if not self.editor.document().isModified() and not self.wysiwyg_editor.document().isModified():
            return True
        reply = QMessageBox.question(
            self,
            "Modifications non enregistrées",
            "Le document actuel contient des modifications non enregistrées. "
            "Continuer sans les enregistrer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _new_document_from_template(self, template_id: str) -> None:
        if not self._confirm_discard_changes():
            return
        self.actions.wysiwyg.toggle.setChecked(False)
        self.editor.new_from_template(template_text(template_id))
        self.setWindowTitle(APP_TITLE)
        self._update_structural_info()

    def _open_file_dialog(self) -> None:
        if not self._confirm_discard_changes():
            return
        start_dir = self.settings.value(prefs.KEY_LAST_OPEN_DIRECTORY, "")
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un document TEI",
            start_dir,
            "Documents TEI/XML (*.xml *.tei);;Tous les fichiers (*)",
        )
        if path_str:
            self._open_path(Path(path_str))

    def _open_path(self, path: Path) -> None:
        self.actions.wysiwyg.toggle.setChecked(False)
        try:
            self.editor.load_file(path)
        except OSError as exc:
            QMessageBox.critical(self, "Ouvrir", f"Impossible d'ouvrir ce fichier :\n{exc}")
            return
        self.settings.setValue(prefs.KEY_LAST_OPEN_DIRECTORY, str(path.parent))
        prefs.record_recent_file(self.settings, str(path))
        self._refresh_recent_files_menu()
        self.setWindowTitle(f"{APP_TITLE} — {path.name}")
        self._update_structural_info()
        self._maybe_offer_recovery(str(path))

    def _open_recent(self, path_str: str) -> None:
        if not self._confirm_discard_changes():
            return
        self._open_path(Path(path_str))

    def _save_file(self) -> None:
        self._commit_wysiwyg_to_editor()
        if self.editor.current_path is None:
            self._save_file_as()
            return
        self._save_to_path(self.editor.current_path)

    def _save_file_as(self) -> None:
        self._commit_wysiwyg_to_editor()
        start_dir = str(self.editor.current_path) if self.editor.current_path else ""
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            start_dir,
            "Documents TEI/XML (*.xml);;Tous les fichiers (*)",
        )
        if path_str:
            self._save_to_path(Path(path_str))

    def _save_to_path(self, path: Path) -> None:
        try:
            self.editor.save_to(path)
        except OSError as exc:
            QMessageBox.critical(self, "Enregistrer", f"Impossible d'enregistrer :\n{exc}")
            return
        prefs.record_recent_file(self.settings, str(path))
        self._refresh_recent_files_menu()
        recovery.clear_recovery(self.recovery_dir, str(path))
        self.setWindowTitle(f"{APP_TITLE} — {path.name}")
        self.statusBar().showMessage(f"Enregistré : {path}", 4000)

    def _export_copy(self) -> None:
        self._commit_wysiwyg_to_editor()
        start_dir = str(self.editor.current_path) if self.editor.current_path else ""
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter une copie",
            start_dir,
            "Documents XML (*.xml);;Tous les fichiers (*)",
        )
        if not path_str:
            return
        try:
            self.editor.export_copy_to(Path(path_str))
        except OSError as exc:
            QMessageBox.critical(self, "Exporter", f"Impossible d'exporter :\n{exc}")
            return
        self.statusBar().showMessage(f"Copie exportée vers {path_str}", 4000)

    def _refresh_recent_files_menu(self) -> None:
        paths = prefs.cleaned_recent_files(self.settings)
        rebuild_recent_files_menu(self.menus.recent_files_menu, paths, on_choose=self._open_recent)

    # -- Édition --------------------------------------------------------------
    def _open_find_replace(self) -> None:
        if self._find_dialog is None:
            self._find_dialog = FindReplaceDialog(self.editor, self)
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()

    def _goto_line(self) -> None:
        max_line = max(1, self.editor.document().blockCount())
        line, ok = QInputDialog.getInt(
            self, "Aller à la ligne", f"Numéro de ligne (1-{max_line}) :", 1, 1, max_line
        )
        if not ok:
            return
        self._goto_line_column(line, 1)

    def _goto_line_column(self, line: int, column: int) -> None:
        block = self.editor.document().findBlockByNumber(max(0, line - 1))
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + max(0, column - 1))
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _goto_outline_line(self, line: int) -> None:
        self._goto_line_column(line, 1)

    def _goto_problem_position(self, line: int, column: int) -> None:
        self._goto_line_column(line, column)

    # -- Mode WYSIWYG (phase 10, ADR-0009) -------------------------------------
    def _on_wysiwyg_toggled(self, checked: bool) -> None:
        if checked:
            self._switch_to_wysiwyg()
        else:
            self._switch_to_text()

    def _switch_to_wysiwyg(self) -> None:
        text = self.editor.toPlainText()
        try:
            root = parse_xml_safely(text)
        except UnsafeXmlError as exc:
            QMessageBox.critical(
                self, "Mode WYSIWYG", f"Document mal formé, bascule impossible :\n{exc}"
            )
            self.actions.wysiwyg.toggle.setChecked(False)
            return
        body = find_body_element(root)
        if body is None:
            QMessageBox.critical(
                self, "Mode WYSIWYG", "Aucun élément <body> dans ce document : bascule impossible."
            )
            self.actions.wysiwyg.toggle.setChecked(False)
            return
        self.wysiwyg_editor.load_blocks(xml_to_blocks(body))
        self._view_stack.setCurrentWidget(self.wysiwyg_editor)

    def _switch_to_text(self) -> None:
        self._commit_wysiwyg_to_editor()
        self._view_stack.setCurrentWidget(self.editor)

    def _commit_wysiwyg_to_editor(self) -> None:
        """Resérialise le modèle de blocs WYSIWYG dans le texte XML de
        ``self.editor`` (ADR-0009 : le pivot de blocs est la source de
        vérité pendant l'édition WYSIWYG, le texte XML la redevient à la
        bascule/sauvegarde). Ne fait rien si le mode WYSIWYG n'est pas
        actif : sans risque à appeler avant chaque enregistrement."""
        if self._view_stack.currentWidget() is not self.wysiwyg_editor:
            return
        new_body_xml = blocks_to_xml(self.wysiwyg_editor.to_blocks())
        current_text = self.editor.toPlainText()
        try:
            new_text = replace_body_in_document(current_text, new_body_xml)
        except (UnsafeXmlError, ValueError) as exc:
            QMessageBox.critical(
                self, "Mode WYSIWYG", f"Impossible de resynchroniser le texte XML :\n{exc}"
            )
            return
        if new_text == current_text:
            return
        cursor_position = self.editor.textCursor().position()
        self.editor.setPlainText(new_text)
        cursor = self.editor.textCursor()
        cursor.setPosition(min(cursor_position, len(new_text)))
        self.editor.setTextCursor(cursor)

    # -- Affichage : zoom/thème --------------------------------------------
    def _apply_theme(self, theme_id: str) -> None:
        self.setStyleSheet(stylesheet_for(theme_id))
        apply_action_icons(self.actions, foreground_color(theme_id))
        action = self.actions.themes.by_name.get(theme_id)
        if action is not None:
            action.setChecked(True)

    def _on_theme_chosen(self, theme_id: str) -> None:
        prefs.set_theme(self.settings, theme_id)
        self._apply_theme(theme_id)

    # -- Outils : valider/profil/préférences --------------------------------
    def _validate_document(self) -> None:
        self._update_structural_info()
        diagnostics = self._last_diagnostics
        errors = [d for d in diagnostics if d.severity == SEVERITY_ERROR]
        warnings = [d for d in diagnostics if d.severity == SEVERITY_WARNING]
        if not diagnostics:
            profile_label = self._profile_labels.get(
                prefs.get_active_profile(self.settings), ""
            )
            QMessageBox.information(
                self,
                "Validation",
                f"Document valide (profil : {profile_label}).",
            )
            return
        parts = []
        if errors:
            parts.append(f"{len(errors)} erreur(s)")
        if warnings:
            parts.append(f"{len(warnings)} avertissement(s) hors profil")
        summary = ", ".join(parts)
        if errors:
            QMessageBox.warning(self, "Validation", f"{summary}. Voir le panneau Problèmes.")
        else:
            QMessageBox.information(self, "Validation", f"{summary}. Voir le panneau Problèmes.")

    def _apply_active_profile(self, profile_id: str) -> None:
        action = self.actions.profiles.by_id.get(profile_id)
        if action is not None:
            action.setChecked(True)
        label = self._profile_labels.get(profile_id, profile_id)
        self.status_bar.set_active_profile(label)

    def _on_profile_chosen(self, profile_id: str) -> None:
        prefs.set_active_profile(self.settings, profile_id)
        self._apply_active_profile(profile_id)

    def _open_header_wizard(self) -> None:
        dialog = HeaderWizardDialog(self.editor, self)
        dialog.exec()

    def _open_preferences(self) -> None:
        dialog = PreferencesDialog(self.settings, self)
        if dialog.exec() == PreferencesDialog.DialogCode.Accepted:
            self._apply_theme(prefs.get_theme(self.settings))
            self._configure_autosave()

    # -- Aide -----------------------------------------------------------------
    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "À propos de TIGRE",
            "<b>TIGRE</b> — TEI Graphic Editor<br>"
            "Éditeur graphique de bureau pour XML-TEI P5 (édition assistée, "
            "sans rendu HTML/XSLT/Pandoc).<br><br>"
            "Voir docs/ROADMAP.md pour la feuille de route complète.",
        )

    # -- Barre d'état (débouncée) ---------------------------------------------
    def _schedule_structural_update(self) -> None:
        self._structural_timer.start()

    def _update_cursor_position_label(self) -> None:
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock() + 1
        self.status_bar.set_cursor_position(line, column)

    def _update_structural_info(self) -> None:
        text = self.editor.toPlainText()
        active_profile = prefs.get_active_profile(self.settings)
        diagnostics = compute_diagnostics(text, active_profile)
        self._last_diagnostics = diagnostics

        try:
            root = parse_xml_safely(text)
            well_formed = True
        except UnsafeXmlError:
            root = None
            well_formed = False

        has_errors = any(d.severity == SEVERITY_ERROR for d in diagnostics)
        if not well_formed:
            message = "Document mal formé"
        elif has_errors:
            message = "Document invalide (schéma TEI)"
        else:
            message = "Document valide"
        self.status_bar.set_validity(well_formed=not has_errors, message=message)

        offset = self.editor.textCursor().position()
        xpath_value = current_xpath(text, offset) if well_formed else None
        self.status_bar.set_xpath(xpath_value)

        self.problems_panel.set_diagnostics(diagnostics)
        apply_diagnostic_highlights(self.editor, diagnostics)

        outline_root = build_outline(root) if root is not None else None
        self.outline_panel.set_outline(outline_root)
        if outline_root is not None:
            self.outline_panel.select_line(self.editor.textCursor().blockNumber() + 1)

        located = locate_current_element(text, offset) if well_formed else None
        current_name = local_name(located.element.tag) if located is not None else None
        self.palette_panel.set_context(current_name, active_profile)
        document_xml_ids = sorted(all_xml_ids(root)) if root is not None else []
        self.inspector_panel.set_element(located, text, document_xml_ids)
        self._update_tag_actions_enabled(located)

    # -- Autosave / récupération ----------------------------------------------
    def _configure_autosave(self) -> None:
        interval_seconds = prefs.get_autosave_interval_seconds(self.settings)
        self._autosave_timer.setInterval(interval_seconds * 1000)
        if prefs.get_autosave_enabled(self.settings):
            self._autosave_timer.start()
        else:
            self._autosave_timer.stop()

    def _autosave_tick(self) -> None:
        if self._view_stack.currentWidget() is self.wysiwyg_editor:
            if not self.wysiwyg_editor.document().isModified():
                return
            self._commit_wysiwyg_to_editor()
        elif not self.editor.document().isModified():
            return
        state = recovery.RecoveryState(
            file_path=str(self.editor.current_path) if self.editor.current_path else None,
            cursor_position=self.editor.textCursor().position(),
            text=self.editor.toPlainText(),
            saved_at=datetime.now(timezone.utc).isoformat(),
        )
        recovery.save_recovery(self.recovery_dir, state)

    def _maybe_offer_recovery(self, file_path: str | None) -> None:
        state = recovery.load_recovery(self.recovery_dir, file_path)
        if state is None:
            return
        reply = QMessageBox.question(
            self,
            "Récupération",
            f"Un brouillon non enregistré existe pour ce document (sauvegardé "
            f"automatiquement le {state.saved_at}). Le restaurer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.editor.setPlainText(state.text)
            cursor = self.editor.textCursor()
            cursor.setPosition(min(state.cursor_position, len(state.text)))
            self.editor.setTextCursor(cursor)
        else:
            recovery.clear_recovery(self.recovery_dir, file_path)

    # -- Fenêtre ---------------------------------------------------------------
    def _restore_geometry(self) -> None:
        geometry = self.settings.value(prefs.KEY_WINDOW_GEOMETRY)
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self.settings.value(prefs.KEY_WINDOW_STATE)
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        if not self._confirm_discard_changes():
            event.ignore()
            return
        self.settings.setValue(prefs.KEY_WINDOW_GEOMETRY, self.saveGeometry())
        self.settings.setValue(prefs.KEY_WINDOW_STATE, self.saveState())
        event.accept()
