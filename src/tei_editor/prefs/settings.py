"""Clefs et accès centralisés à ``QSettings`` pour toute l'application.

Convention retenue (voir ``docs/DECISIONS.md``) : organisation et
application ``"TIGRE"``/``"TIGRE"`` partout — fichiers récents, thème,
autosave, profil actif, géométrie de fenêtre.

La logique pure (dédoublonnage des fichiers récents, nettoyage des
chemins disparus) est séparée des fonctions qui touchent ``QSettings``,
pour rester testable sans Qt (``CLAUDE.md`` : « une fonctionnalité = un
module testable sans interface graphique + une fine couche Qt »).
"""

from __future__ import annotations

from pathlib import Path

ORGANIZATION = "TIGRE"
APPLICATION = "TIGRE"

KEY_RECENT_FILES = "files/recent"
KEY_THEME = "ui/theme"
KEY_ACTIVE_PROFILE = "tei/active_profile"
KEY_AUTOSAVE_ENABLED = "autosave/enabled"
KEY_AUTOSAVE_INTERVAL_SECONDS = "autosave/interval_seconds"
KEY_WINDOW_GEOMETRY = "window/geometry"
KEY_WINDOW_STATE = "window/state"
KEY_LAST_OPEN_DIRECTORY = "files/last_open_directory"

MAX_RECENT_FILES = 10
DEFAULT_THEME = "clair"
DEFAULT_ACTIVE_PROFILE = "tei_all"
DEFAULT_AUTOSAVE_ENABLED = True
DEFAULT_AUTOSAVE_INTERVAL_SECONDS = 60

THEME_CHOICES = ("clair", "sombre")


def normalize_recent_entry(path: str) -> str:
    return str(Path(path))


def add_recent_file(existing: list[str], new_path: str, max_items: int = MAX_RECENT_FILES) -> list[str]:
    """Place ``new_path`` en tête de la liste, sans doublon, tronquée à
    ``max_items``. Logique pure, sans ``QSettings``."""
    normalized = normalize_recent_entry(new_path)
    items = [p for p in existing if normalize_recent_entry(p) != normalized]
    items.insert(0, normalized)
    return items[:max_items]


def prune_missing_recent_files(existing: list[str]) -> list[str]:
    """Écarte les chemins qui ne correspondent plus à un fichier existant."""
    return [p for p in existing if Path(p).is_file()]


def get_settings():
    # Import différé : évite d'imposer PySide6 aux tests qui n'utilisent
    # que la logique pure ci-dessus.
    from PySide6.QtCore import QSettings

    return QSettings(ORGANIZATION, APPLICATION)


def load_recent_files(settings) -> list[str]:
    value = settings.value(KEY_RECENT_FILES, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def save_recent_files(settings, paths: list[str]) -> None:
    settings.setValue(KEY_RECENT_FILES, paths)


def record_recent_file(settings, path: str) -> list[str]:
    """Ajoute ``path`` aux fichiers récents (après nettoyage des chemins
    disparus) et renvoie la liste à jour, déjà enregistrée."""
    cleaned = prune_missing_recent_files(load_recent_files(settings))
    updated = add_recent_file(cleaned, path)
    save_recent_files(settings, updated)
    return updated


def cleaned_recent_files(settings) -> list[str]:
    """Nettoie et renvoie les fichiers récents existants, enregistre le
    résultat nettoyé."""
    cleaned = prune_missing_recent_files(load_recent_files(settings))
    save_recent_files(settings, cleaned)
    return cleaned


def get_theme(settings) -> str:
    value = settings.value(KEY_THEME, DEFAULT_THEME)
    return value if value in THEME_CHOICES else DEFAULT_THEME


def set_theme(settings, theme: str) -> None:
    settings.setValue(KEY_THEME, theme)


def get_active_profile(settings) -> str:
    return settings.value(KEY_ACTIVE_PROFILE, DEFAULT_ACTIVE_PROFILE)


def set_active_profile(settings, profile_id: str) -> None:
    settings.setValue(KEY_ACTIVE_PROFILE, profile_id)


def get_autosave_enabled(settings) -> bool:
    value = settings.value(KEY_AUTOSAVE_ENABLED, DEFAULT_AUTOSAVE_ENABLED)
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes")
    return bool(value)


def set_autosave_enabled(settings, enabled: bool) -> None:
    settings.setValue(KEY_AUTOSAVE_ENABLED, enabled)


def get_autosave_interval_seconds(settings) -> int:
    value = settings.value(KEY_AUTOSAVE_INTERVAL_SECONDS, DEFAULT_AUTOSAVE_INTERVAL_SECONDS)
    try:
        return max(5, int(value))
    except (TypeError, ValueError):
        return DEFAULT_AUTOSAVE_INTERVAL_SECONDS


def set_autosave_interval_seconds(settings, seconds: int) -> None:
    settings.setValue(KEY_AUTOSAVE_INTERVAL_SECONDS, max(5, int(seconds)))
