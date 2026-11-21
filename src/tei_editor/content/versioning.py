# Repris partiellement de C:\merope src/bloggen/content/versioning.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30) : seules
# les primitives d'archivage pur `pathlib.Path` (list_versions,
# archive_previous_version, versions_to_purge, purge_versions) sont
# reprises. La fonction `convert_content_file` (conversion page/post
# Markdown, et son import de `bloggen.content.writer`) est volontairement
# laissée de côté : hors-sujet pour un éditeur TEI et seule source de
# couplage à `bloggen` dans le fichier d'origine (voir docs/AUDIT_MEROPE.md).
"""Archivage de version précédente d'un document, indépendant de toute
interface graphique : chaque enregistrement peut conserver une copie
numérotée de l'état précédent du fichier, et purger les plus anciennes
au-delà d'un seuil."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

VERSIONS_DIRNAME = ".versions"
MAX_VERSIONS_PER_DOCUMENT = 20
VERSION_PURGE_PROMPT_INTERVAL = 50
_VERSION_FILENAME_RE_TEMPLATE = r"^{stem}\.v(\d+){suffix}$"


@dataclass(frozen=True, slots=True)
class ArchiveResult:
    """Résultat de l'archivage de l'état sur disque actuel d'un document."""

    archived_path: Path | None
    versions: tuple[tuple[int, Path], ...]
    should_offer_purge: bool


def list_versions(path: Path, versions_dir: Path | None = None) -> list[tuple[int, Path]]:
    """Liste les archives numérotées valides de ``path``, numéro croissant."""
    path = Path(path)
    versions_dir = Path(versions_dir) if versions_dir is not None else path.parent / VERSIONS_DIRNAME
    pattern = re.compile(
        _VERSION_FILENAME_RE_TEMPLATE.format(
            stem=re.escape(path.stem),
            suffix=re.escape(path.suffix),
        )
    )
    numbered: list[tuple[int, Path]] = []
    for existing in versions_dir.glob(f"{path.stem}.v*{path.suffix}"):
        match = pattern.match(existing.name)
        if match:
            numbered.append((int(match.group(1)), existing))
    numbered.sort(key=lambda item: item[0])
    return numbered


def archive_previous_version(
    path: Path,
    *,
    prompt_interval: int = VERSION_PURGE_PROMPT_INTERVAL,
) -> ArchiveResult:
    """Archive le fichier actuel et indique si l'interface doit proposer
    une purge.

    Aucune suppression n'est effectuée ici. L'appelant reste responsable
    de tout choix interactif et peut ensuite passer :func:`versions_to_purge`
    à :func:`purge_versions` après confirmation explicite de l'utilisateur.
    """
    path = Path(path)
    if not path.exists():
        return ArchiveResult(None, (), False)

    versions_dir = path.parent / VERSIONS_DIRNAME
    versions_dir.mkdir(exist_ok=True)
    existing_versions = list_versions(path, versions_dir)
    next_number = existing_versions[-1][0] + 1 if existing_versions else 1
    version_path = versions_dir / f"{path.stem}.v{next_number}{path.suffix}"
    version_path.write_bytes(path.read_bytes())

    existing_versions.append((next_number, version_path))
    return ArchiveResult(
        archived_path=version_path,
        versions=tuple(existing_versions),
        should_offer_purge=(len(existing_versions) % prompt_interval == 0),
    )


def versions_to_purge(
    versions: list[tuple[int, Path]] | tuple[tuple[int, Path], ...],
    *,
    keep: int = MAX_VERSIONS_PER_DOCUMENT,
) -> list[tuple[int, Path]]:
    """Renvoie les plus anciennes versions au-delà de ``keep``, sans supprimer."""
    overflow = len(versions) - keep
    return list(versions[:overflow]) if overflow > 0 else []


def purge_versions(versions: list[tuple[int, Path]]) -> None:
    """Supprime exactement les fichiers de version sélectionnés par l'appelant."""
    for _number, old_path in versions:
        old_path.unlink(missing_ok=True)
