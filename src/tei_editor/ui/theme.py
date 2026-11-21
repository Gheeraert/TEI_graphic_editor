"""Palettes de couleurs et feuilles de style Qt (QSS) claire/sombre
(``docs/ROADMAP.md`` §5, phase 8 — remplace la ``_DARK_STYLESHEET``
statique posée en phase 3, voir ``docs/DECISIONS.md`` ADR-0006 point 9).

Les couleurs sont des constantes Python (``THEMES``), pas des chaînes
littérales dispersées dans un gabarit QSS : c'est à partir de ces mêmes
constantes que la feuille de style est composée (:func:`stylesheet_for`)
*et* que le contraste WCAG est vérifié (``tests/test_theme_contrast.py``) —
les deux emplois lisent la même source, donc jamais de divergence entre
ce qui est affiché et ce qui est mesuré.

Palette retenue : esprit Monokai conservé pour le thème sombre (déjà en
place depuis la phase 3) ; thème clair neuf, sobre, à fort contraste.
Ratios de contraste WCAG texte normal/fond et texte désactivé/fond
vérifiés ≥ 4.5:1 pour les deux thèmes (voir le test dédié).
"""

from __future__ import annotations

THEME_IDS = ("clair", "sombre")

# Chaque thème porte le même jeu de clefs, utilisées à la fois par
# `stylesheet_for` et par les tests de contraste.
THEMES: dict[str, dict[str, str]] = {
    "clair": {
        "window_bg": "#f5f4f0",
        "surface_bg": "#ffffff",
        "surface_alt_bg": "#ebe9e2",
        "text": "#1f1e1b",
        "text_disabled": "#6b6a64",
        "border": "#c9c6bc",
        "accent": "#2563a6",
        "accent_text": "#ffffff",
        "selection_bg": "#2563a6",
        "selection_text": "#ffffff",
        "hover_bg": "#e3e1d8",
        "pressed_bg": "#d4d1c6",
        "error": "#9a2b22",
        "warning": "#8a5a00",
    },
    "sombre": {
        "window_bg": "#272822",
        "surface_bg": "#1e1f1c",
        "surface_alt_bg": "#32332c",
        "text": "#f8f8f2",
        "text_disabled": "#9a9a90",
        "border": "#49483e",
        "accent": "#66d9ef",
        "accent_text": "#1e1f1c",
        "selection_bg": "#49483e",
        "selection_text": "#f8f8f2",
        "hover_bg": "#3e3f36",
        "pressed_bg": "#49483e",
        "error": "#f92672",
        "warning": "#e6db74",
    },
}


def foreground_color(theme_id: str) -> str:
    """Couleur de premier plan (texte) du thème, utilisée aussi pour
    colorer les icônes SVG (``tei_editor.ui.icons``) : c'est **exactement**
    la même couleur que le texte de la feuille de style active."""
    return THEMES[theme_id]["text"]


def stylesheet_for(theme_id: str) -> str:
    """Feuille de style Qt complète pour ``theme_id`` (``"clair"`` ou
    ``"sombre"``) : fenêtre principale, menus, barres d'outils, barre
    d'état, docks, listes/arbres, boutons, champs de saisie. Boutons
    uniformes (police, marges, rayon d'angle) entre les deux thèmes."""
    c = THEMES[theme_id]
    return f"""
QWidget {{
    background-color: {c['window_bg']};
    color: {c['text']};
    font-size: 10pt;
}}
QWidget:disabled {{
    color: {c['text_disabled']};
}}

QMainWindow, QDialog {{
    background-color: {c['window_bg']};
}}

/* -- Édition --------------------------------------------------------- */
QPlainTextEdit, QTextEdit, QLineEdit, QSpinBox, QComboBox {{
    background-color: {c['surface_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 2px 4px;
    selection-background-color: {c['selection_bg']};
    selection-color: {c['selection_text']};
}}
QPlainTextEdit {{
    border-radius: 0px;
    padding: 4px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {c['accent']};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    color: {c['text_disabled']};
    background-color: {c['surface_alt_bg']};
}}

/* -- Menus ------------------------------------------------------------ */
QMenuBar {{
    background-color: {c['window_bg']};
    color: {c['text']};
    border-bottom: 1px solid {c['border']};
}}
QMenuBar::item {{
    padding: 4px 10px;
    background: transparent;
}}
QMenuBar::item:selected, QMenuBar::item:pressed {{
    background-color: {c['hover_bg']};
    border-radius: 4px;
}}
QMenu {{
    background-color: {c['surface_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
}}
QMenu::item {{
    padding: 5px 24px 5px 12px;
}}
QMenu::item:selected {{
    background-color: {c['hover_bg']};
}}
QMenu::item:disabled {{
    color: {c['text_disabled']};
}}
QMenu::separator {{
    height: 1px;
    background: {c['border']};
    margin: 4px 8px;
}}

/* -- Barres d'outils ---------------------------------------------------- */
QToolBar {{
    background-color: {c['window_bg']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 3px;
    spacing: 3px;
}}
QToolBar::separator {{
    background-color: {c['border']};
    width: 1px;
    margin: 4px 4px;
}}
QToolButton {{
    background-color: transparent;
    color: {c['text']};
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px;
}}
QToolButton:hover {{
    background-color: {c['hover_bg']};
    border: 1px solid {c['border']};
}}
QToolButton:pressed {{
    background-color: {c['pressed_bg']};
}}
QToolButton:checked {{
    background-color: {c['selection_bg']};
    color: {c['selection_text']};
}}
QToolButton:disabled {{
    color: {c['text_disabled']};
}}

/* -- Barre d'état -------------------------------------------------------- */
QStatusBar {{
    background-color: {c['window_bg']};
    color: {c['text']};
    border-top: 1px solid {c['border']};
}}
QStatusBar::item {{
    border: none;
}}

/* -- Docks ----------------------------------------------------------- */
QDockWidget {{
    color: {c['text']};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: {c['surface_alt_bg']};
    color: {c['text']};
    padding: 5px 8px;
    border-bottom: 1px solid {c['border']};
}}

/* -- Listes et arbres (Plan, Problèmes, Palette) ------------------------- */
QTreeView, QListView, QTableView {{
    background-color: {c['surface_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    alternate-background-color: {c['surface_alt_bg']};
    selection-background-color: {c['selection_bg']};
    selection-color: {c['selection_text']};
}}
QTreeView::item:hover, QListView::item:hover {{
    background-color: {c['hover_bg']};
}}
QHeaderView::section {{
    background-color: {c['surface_alt_bg']};
    color: {c['text']};
    padding: 4px;
    border: none;
    border-bottom: 1px solid {c['border']};
}}

/* -- Boutons de dialogue : uniformes --------------------------------- */
QPushButton {{
    background-color: {c['surface_alt_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 5px;
    padding: 5px 14px;
    min-width: 72px;
    font-size: 10pt;
}}
QPushButton:hover {{
    background-color: {c['hover_bg']};
}}
QPushButton:pressed {{
    background-color: {c['pressed_bg']};
}}
QPushButton:disabled {{
    color: {c['text_disabled']};
    background-color: {c['surface_alt_bg']};
}}
QPushButton:default {{
    border: 1px solid {c['accent']};
}}

/* -- Onglets (assistant d'en-tête, préférences) -------------------------- */
QTabBar::tab {{
    background-color: {c['surface_alt_bg']};
    color: {c['text']};
    padding: 6px 12px;
    border: 1px solid {c['border']};
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background-color: {c['surface_bg']};
}}
QTabWidget::pane {{
    border: 1px solid {c['border']};
}}

QToolTip {{
    background-color: {c['surface_alt_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    padding: 3px 6px;
}}
"""
