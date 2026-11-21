# Repris de C:\merope src/bloggen/tei/licenses.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30), sans
# changement de comportement (seul le commentaire d'en-tête est adapté).
"""Résolution des licences Creative Commons usuelles pour l'assistant
de teiHeader (identifiant SPDX -> nom canonique + URL).
"""

from __future__ import annotations

from dataclasses import dataclass

SPDX_LICENSES: dict[str, tuple[str, str]] = {
    "CC-BY-4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    "CC-BY-SA-4.0": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    "CC-BY-ND-4.0": ("CC BY-ND 4.0", "https://creativecommons.org/licenses/by-nd/4.0/"),
    "CC-BY-NC-4.0": ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/"),
    "CC-BY-NC-SA-4.0": ("CC BY-NC-SA 4.0", "https://creativecommons.org/licenses/by-nc-sa/4.0/"),
    "CC-BY-NC-ND-4.0": ("CC BY-NC-ND 4.0", "https://creativecommons.org/licenses/by-nc-nd/4.0/"),
    "CC0-1.0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
}


@dataclass(slots=True, frozen=True)
class ResolvedLicense:
    name: str | None
    url: str | None


def resolve_license(*, spdx_id: str | None, name: str | None, url: str | None) -> ResolvedLicense:
    """Un identifiant SPDX connu (voir SPDX_LICENSES) se résout vers son
    nom/URL canoniques, en écrasant un nom/url libre éventuellement fourni
    en même temps — c'est tout l'intérêt de nommer une licence connue par
    son identifiant SPDX plutôt que de la saisir en texte libre. Un
    identifiant absent ou inconnu retombe sur les champs libres tels que
    fournis, pour que toute autre licence reste représentable sans SPDX.
    """
    canonical = SPDX_LICENSES.get((spdx_id or "").strip())
    if canonical is not None:
        return ResolvedLicense(name=canonical[0], url=canonical[1])
    return ResolvedLicense(name=(name or "").strip() or None, url=(url or "").strip() or None)
