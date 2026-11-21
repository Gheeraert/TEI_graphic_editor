"""``QAction`` centralisées (``docs/ROADMAP.md`` §5 : « QAction
centralisées dans un module dédié, pas éparpillées dans ``MainWindow`` »).

Ce module ne fait que construire les actions (texte, raccourci,
« cochable », groupes exclusifs) ; leur branchement (``triggered.connect``)
est fait par ``main_window.py``. Phase 5 : les menus « Insertion » et
« Balises » reçoivent leurs commandes réelles (envelopper, dégrouper,
renommer, scinder/fusionner, générer un xml:id) ; les jeux de balises
par profil restent pour la phase 7.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QWidget

from tei_editor.prefs.settings import THEME_CHOICES
from tei_editor.tei.templates import TEMPLATES


def _action(parent: QWidget, text: str, *, shortcut: str | None = None, checkable: bool = False) -> QAction:
    action = QAction(text, parent)
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    action.setCheckable(checkable)
    return action


@dataclass
class ViewDockActions:
    outline: QAction
    inspector: QAction
    problems: QAction
    palette: QAction


@dataclass
class TagActions:
    wrap_selection: QAction
    unwrap: QAction
    rename: QAction
    split_paragraph: QAction
    merge_paragraph: QAction
    generate_xml_id: QAction


@dataclass
class SnippetActions:
    """Commandes composites de la phase 7 (jeux de balises) :
    « Grouper en choix… », « Insérer une liste de personnages… »,
    « Marquer un vers partagé », « Insérer une leçon (app/lem/rdg)… »."""

    group_as_choice: QAction
    insert_cast_list: QAction
    mark_shared_verse: QAction
    insert_apparatus: QAction


@dataclass
class ThemeActions:
    group: QActionGroup
    by_name: dict[str, QAction] = field(default_factory=dict)


@dataclass
class ProfileActions:
    group: QActionGroup
    by_id: dict[str, QAction] = field(default_factory=dict)


@dataclass
class TemplateActions:
    """Sous-menu « Nouveau > » (phase 6) : un ``QAction`` par modèle de
    `tei_editor.tei.templates.TEMPLATES`."""

    by_id: dict[str, QAction] = field(default_factory=dict)


@dataclass
class HeaderWizardAction:
    open_wizard: QAction


@dataclass
class Actions:
    # Fichier
    new: QAction
    new_templates: TemplateActions
    open: QAction
    recent_menu_placeholder: QAction  # remplacé dynamiquement par menus.py
    save: QAction
    save_as: QAction
    export: QAction
    quit: QAction
    # Édition
    undo: QAction
    redo: QAction
    cut: QAction
    copy: QAction
    paste: QAction
    find_replace: QAction
    goto_line: QAction
    # Insertion / Balises (phase 5 ; jeux de balises par profil : phase 7)
    insertion_unavailable: QAction
    tags: TagActions
    snippets: SnippetActions
    # Affichage
    docks: ViewDockActions
    zoom_in: QAction
    zoom_out: QAction
    zoom_reset: QAction
    themes: ThemeActions
    # Outils
    validate: QAction
    profiles: ProfileActions
    header_wizard: QAction
    preferences: QAction
    # Aide
    about: QAction


def build_actions(parent: QWidget, *, profile_ids_and_labels: list[tuple[str, str]]) -> Actions:
    # « Nouveau » (Ctrl+N) crée directement le modèle minimal (comportement
    # de la phase 3 conservé) ; le sous-menu « Nouveau depuis un modèle »
    # (phase 6) propose les 4 modèles, y compris ce même modèle minimal
    # (même ``QAction``, pour ne pas dupliquer le raccourci).
    new = _action(parent, "&Nouveau", shortcut="Ctrl+N")
    new_templates = TemplateActions(by_id={"minimal": new})
    for template in TEMPLATES:
        if template.template_id == "minimal":
            continue
        new_templates.by_id[template.template_id] = _action(parent, template.label)
    open_ = _action(parent, "&Ouvrir...", shortcut="Ctrl+O")
    save = _action(parent, "&Enregistrer", shortcut="Ctrl+S")
    save_as = _action(parent, "Enregistrer &sous...", shortcut="Ctrl+Shift+S")
    export = _action(parent, "&Exporter une copie...")
    quit_ = _action(parent, "&Quitter", shortcut="Ctrl+Q")

    undo = _action(parent, "&Annuler", shortcut="Ctrl+Z")
    redo = _action(parent, "&Rétablir", shortcut="Ctrl+Shift+Z")
    cut = _action(parent, "Co&uper", shortcut="Ctrl+X")
    copy = _action(parent, "&Copier", shortcut="Ctrl+C")
    paste = _action(parent, "C&oller", shortcut="Ctrl+V")
    find_replace = _action(parent, "&Rechercher/remplacer...", shortcut="Ctrl+F")
    goto_line = _action(parent, "Aller à la li&gne...", shortcut="Ctrl+G")

    insertion_unavailable = _action(parent, "Palette de balises : voir le dock « Palette » (Affichage)")
    insertion_unavailable.setEnabled(False)

    tags = TagActions(
        wrap_selection=_action(parent, "&Envelopper la sélection...", shortcut="Ctrl+E"),
        unwrap=_action(parent, "&Dégrouper la balise"),
        rename=_action(parent, "&Renommer la balise..."),
        split_paragraph=_action(parent, "&Scinder le paragraphe"),
        merge_paragraph=_action(parent, "&Fusionner avec le paragraphe suivant"),
        generate_xml_id=_action(parent, "&Générer un xml:id"),
    )

    snippets = SnippetActions(
        group_as_choice=_action(parent, "&Grouper en choix…"),
        insert_cast_list=_action(parent, "Insérer une &liste de personnages…"),
        mark_shared_verse=_action(parent, "Marquer un &vers partagé"),
        insert_apparatus=_action(parent, "Insérer une &leçon (app/lem/rdg)…"),
    )

    outline = _action(parent, "&Plan", checkable=True)
    inspector = _action(parent, "&Inspecteur", checkable=True)
    problems = _action(parent, "Pro&blèmes", checkable=True)
    palette = _action(parent, "&Palette", checkable=True)
    docks = ViewDockActions(outline=outline, inspector=inspector, problems=problems, palette=palette)

    zoom_in = _action(parent, "Zoom &avant", shortcut="Ctrl++")
    zoom_out = _action(parent, "Zoom a&rrière", shortcut="Ctrl+-")
    zoom_reset = _action(parent, "Zoom &réinitialiser", shortcut="Ctrl+0")

    theme_group = QActionGroup(parent)
    theme_group.setExclusive(True)
    theme_actions = ThemeActions(group=theme_group)
    theme_labels = {"clair": "Thème &clair", "sombre": "Thème &sombre"}
    for theme_id in THEME_CHOICES:
        theme_action = _action(parent, theme_labels.get(theme_id, theme_id), checkable=True)
        theme_action.setActionGroup(theme_group)
        theme_actions.by_name[theme_id] = theme_action

    validate = _action(parent, "&Valider", shortcut="F7")

    profile_group = QActionGroup(parent)
    profile_group.setExclusive(True)
    profile_actions = ProfileActions(group=profile_group)
    for profile_id, label in profile_ids_and_labels:
        profile_action = _action(parent, label, checkable=True)
        profile_action.setActionGroup(profile_group)
        profile_actions.by_id[profile_id] = profile_action

    header_wizard = _action(parent, "&Assistant d'en-tête...")
    preferences = _action(parent, "&Préférences...")
    about = _action(parent, "À &propos de TIGRE")

    return Actions(
        new=new,
        new_templates=new_templates,
        open=open_,
        recent_menu_placeholder=_action(parent, "(fichiers récents)"),
        save=save,
        save_as=save_as,
        export=export,
        quit=quit_,
        undo=undo,
        redo=redo,
        cut=cut,
        copy=copy,
        paste=paste,
        find_replace=find_replace,
        goto_line=goto_line,
        insertion_unavailable=insertion_unavailable,
        tags=tags,
        snippets=snippets,
        docks=docks,
        zoom_in=zoom_in,
        zoom_out=zoom_out,
        zoom_reset=zoom_reset,
        themes=theme_actions,
        validate=validate,
        profiles=profile_actions,
        header_wizard=header_wizard,
        preferences=preferences,
        about=about,
    )
