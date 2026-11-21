"""Icônes SVG Lucide adaptées au thème actif (``docs/ROADMAP.md`` §5,
phase 8).

Les fichiers SVG de ``data/icons/`` (récupérés par ``tools/fetch_icons.py``,
voir ``data/icons/PROVENANCE.json``) utilisent la convention Lucide
``stroke="currentColor"``, qui ne se résout pas automatiquement dans un
``QIcon`` Qt (ce n'est pas un navigateur). La substitution de
``currentColor`` par la couleur de premier plan du thème actif se fait
ici **en mémoire**, à l'usage : pas de second jeu de fichiers par
couleur à committer.

La correspondance action -> icône est une donnée externe
(``data/icons/action_icons.json``), jamais codée en dur dans un widget
(``CLAUDE.md``).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent.parent / "data" / "icons"
DEFAULT_ICON_SIZE = 20


@lru_cache(maxsize=1)
def _action_icon_names() -> dict[str, str]:
    data = (ICONS_DIR / "action_icons.json").read_text(encoding="utf-8")
    return json.loads(data)


def icon_name_for_action(action_name: str) -> str | None:
    """Nom de l'icône Lucide associée à ``action_name`` (ex.
    ``"save"`` ou ``"tags.wrap_selection"``), ou ``None`` si l'action
    n'a pas d'icône dans ``action_icons.json``."""
    return _action_icon_names().get(action_name)


@lru_cache(maxsize=None)
def _raw_svg(icon_name: str) -> bytes:
    return (ICONS_DIR / f"{icon_name}.svg").read_bytes()


def colored_svg_bytes(icon_name: str, color: str) -> bytes:
    """Octets du SVG ``icon_name`` avec ``currentColor`` remplacé par
    ``color`` (ex. ``"#f8f8f2"``). Fonction pure, testable sans Qt."""
    raw = _raw_svg(icon_name)
    return raw.replace(b"currentColor", color.encode("ascii"))


def colored_svg_bytes_for_action(action_name: str, color: str) -> bytes | None:
    """Comme :func:`colored_svg_bytes`, mais à partir du nom d'action.
    Renvoie ``None`` si l'action n'a pas d'icône associée."""
    icon_name = icon_name_for_action(action_name)
    if icon_name is None:
        return None
    return colored_svg_bytes(icon_name, color)


def load_action_icon(action_name: str, color: str, *, size: int = DEFAULT_ICON_SIZE):
    """Construit un ``QIcon`` pour ``action_name``, coloré selon
    ``color`` (couleur de premier plan du thème actif). Renvoie un
    ``QIcon`` vide si l'action n'a pas d'icône associée."""
    from PySide6.QtCore import QByteArray, QSize, Qt
    from PySide6.QtGui import QIcon, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    svg_bytes = colored_svg_bytes_for_action(action_name, color)
    if svg_bytes is None:
        return QIcon()

    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    return QIcon(pixmap)


def apply_action_icons(actions, color: str, *, size: int = DEFAULT_ICON_SIZE) -> None:
    """Pose une icône (colorée selon ``color``) sur chaque ``QAction`` de
    ``actions`` qui en a une dans ``action_icons.json``. Appelé à
    l'initialisation et chaque fois que le thème change (``_apply_theme``),
    pour que les icônes suivent la couleur de premier plan active."""
    from tei_editor.ui.action_registry import flatten_actions

    for name, action in flatten_actions(actions).items():
        icon = load_action_icon(name, color, size=size)
        if not icon.isNull():
            action.setIcon(icon)
