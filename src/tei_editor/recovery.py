"""Autosave et restauration après plantage, sans interface graphique.

Réécrit sur le principe documenté dans ``docs/AUDIT_MEROPE.md`` pour
``ui/editor_recovery.py`` de Mérope (dataclass minimale + sauvegarde/
chargement/suppression en JSON, écriture atomique), mais dans le
vocabulaire de cet éditeur : chemin du fichier ouvert (ou ``None`` pour
un document « Sans titre »), position du curseur, texte XML courant —
pas de ``Block``/notes (ADR-0001 : pas de pivot objet).

Un brouillon est identifié par une clef stable dérivée du chemin ouvert
(ou ``"untitled"`` en l'absence de fichier), pour retrouver facilement,
à l'ouverture d'un fichier donné, le brouillon qui lui correspond.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from tei_editor.content.atomic_write import atomic_write_text

RECOVERY_SUFFIX = ".recovery.json"


@dataclass(frozen=True, slots=True)
class RecoveryState:
    """Un brouillon de récupération pour un document en cours d'édition."""

    file_path: str | None
    cursor_position: int
    text: str
    saved_at: str


def recovery_key(file_path: str | None) -> str:
    """Clef stable (nom de fichier sûr sur tout système) pour ``file_path``."""
    if not file_path:
        return "untitled"
    digest = hashlib.sha1(file_path.encode("utf-8")).hexdigest()
    return f"file-{digest}"


def _recovery_path(directory, key: str):
    from pathlib import Path

    return Path(directory) / f"{key}{RECOVERY_SUFFIX}"


def save_recovery(directory, state: RecoveryState) -> None:
    """Écrit (de façon atomique) le brouillon ``state`` pour son fichier."""
    from pathlib import Path

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = _recovery_path(directory, recovery_key(state.file_path))
    atomic_write_text(path, json.dumps(asdict(state), ensure_ascii=False, indent=2))


def load_recovery(directory, file_path: str | None) -> RecoveryState | None:
    """Charge le brouillon correspondant à ``file_path``, ou ``None``
    s'il n'existe pas ou ne peut pas être lu."""
    path = _recovery_path(directory, recovery_key(file_path))
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return RecoveryState(
            file_path=data.get("file_path"),
            cursor_position=int(data.get("cursor_position", 0)),
            text=data.get("text", ""),
            saved_at=data.get("saved_at", ""),
        )
    except (OSError, ValueError, KeyError):
        return None


def clear_recovery(directory, file_path: str | None) -> None:
    """Supprime le brouillon de ``file_path`` s'il existe (après un
    enregistrement réussi, par exemple)."""
    path = _recovery_path(directory, recovery_key(file_path))
    path.unlink(missing_ok=True)


def list_orphan_recoveries(directory) -> list[RecoveryState]:
    """Liste tous les brouillons présents dans ``directory``, y compris
    ceux de documents « Sans titre » (aucun fichier associé)."""
    from pathlib import Path

    directory = Path(directory)
    if not directory.is_dir():
        return []
    states = []
    for entry in sorted(directory.glob(f"*{RECOVERY_SUFFIX}")):
        try:
            data = json.loads(entry.read_text(encoding="utf-8"))
            states.append(
                RecoveryState(
                    file_path=data.get("file_path"),
                    cursor_position=int(data.get("cursor_position", 0)),
                    text=data.get("text", ""),
                    saved_at=data.get("saved_at", ""),
                )
            )
        except (OSError, ValueError, KeyError):
            continue
    return states


def default_recovery_directory():
    """Dossier par défaut des brouillons : ``AppDataLocation`` de Qt
    (voir ``docs/DECISIONS.md``), sous-dossier ``recovery``."""
    from pathlib import Path

    from PySide6.QtCore import QStandardPaths

    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not base:
        base = str(Path.home() / ".tigre")
    # Segment "TIGRE" toujours ajouté explicitement : QStandardPaths ne
    # qualifie le chemin par organisation/application que si elles ont
    # été définies sur QCoreApplication, ce qui n'est pas garanti ici
    # (notamment en test).
    return Path(base) / "TIGRE" / "recovery"
