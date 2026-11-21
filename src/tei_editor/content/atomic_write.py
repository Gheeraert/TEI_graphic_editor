# Repris de C:\merope src/bloggen/content/atomic_write.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30), sans
# changement de comportement (seul le commentaire d'en-tête est adapté).
"""Primitive minimale, indépendante de toute interface graphique, pour
un remplacement de fichier résistant à une interruption en cours
d'écriture."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Écrit ``text`` entièrement avant de remplacer ``path`` de façon
    atomique.

    L'appelant est responsable de la création du répertoire parent. Le
    fichier temporaire est créé à côté de la cible pour que
    :func:`os.replace` reste sur le même volume.
    """

    target = Path(path)
    try:
        target_mode = stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        target_mode = None

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.tmp-",
        dir=target.parent,
    )
    temporary_path = Path(temporary_name)
    descriptor_open = True
    try:
        stream = os.fdopen(descriptor, "w", encoding=encoding)
        descriptor_open = False
        with stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())

        if target_mode is not None:
            os.chmod(temporary_path, target_mode)
        os.replace(temporary_path, target)
    finally:
        try:
            if descriptor_open:
                os.close(descriptor)
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
