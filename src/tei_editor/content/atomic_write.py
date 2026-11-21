# Repris de C:\merope src/bloggen/content/atomic_write.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30) :
# `atomic_write_text` sans changement de comportement (seul le
# commentaire d'en-tête est adapté). `atomic_write_bytes` est un ajout de
# la phase 3 (voir docs/DECISIONS.md) : `atomic_write_text` ouvre son
# flux en mode texte, qui traduit toute fin de ligne écrite selon
# `os.linesep` — ce qui romprait le critère de round-trip octet à octet
# (ADR-0001/phase 3) sur un fichier dont la fin de ligne d'origine diffère
# de celle de la plateforme. `atomic_write_bytes` écrit des octets déjà
# encodés, sans aucune traduction, et est la primitive utilisée pour
# l'enregistrement d'un document TEI.
"""Primitives minimales, indépendantes de toute interface graphique, pour
un remplacement de fichier résistant à une interruption en cours
d'écriture."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import BinaryIO, TextIO


def _atomic_replace_with(path: Path, mode: str, encoding: str | None, write) -> None:
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
        stream: TextIO | BinaryIO
        if encoding is not None:
            stream = os.fdopen(descriptor, mode, encoding=encoding)
        else:
            stream = os.fdopen(descriptor, mode)
        descriptor_open = False
        with stream:
            write(stream)
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

    Mode texte : la fin de ligne écrite est traduite selon la plateforme
    (``os.linesep``). Ne pas utiliser pour un contenu dont les octets
    doivent être préservés à l'identique (voir :func:`atomic_write_bytes`,
    utilisée pour l'enregistrement d'un document TEI).
    """
    _atomic_replace_with(path, "w", encoding, lambda stream: stream.write(text))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Écrit ``data`` (déjà encodé) entièrement avant de remplacer ``path``
    de façon atomique, sans aucune traduction de fin de ligne.

    À utiliser pour tout contenu dont les octets doivent être préservés à
    l'identique (notamment le XML TEI édité par cette application, voir
    ``docs/DECISIONS.md`` sur le round-trip octet à octet).
    """
    _atomic_replace_with(path, "wb", None, lambda stream: stream.write(data))
