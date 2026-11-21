"""XPath courant calculé depuis une position de curseur dans le texte XML.

Approche volontairement simple pour cette phase (voir
``docs/ROADMAP.md`` §5, phase 3) : un balayage du texte par expressions
régulières, qui reconstruit la pile d'imbrication des éléments jusqu'à
la position donnée, sans dépendre d'informations de position que
``lxml`` ne fournit pas nativement (seul ``sourceline`` du début de
balise est disponible, pas la fin d'un élément). Le fil d'Ariane XPath
précis par positions arrive en phase 4.

:func:`current_xpath` vérifie d'abord la bonne formation du document
entier avec :func:`tei_editor.tei.xml_safety.parse_xml_safely` (comme
demandé par la roadmap) : si le document est actuellement mal formé,
elle renvoie ``None`` plutôt que de risquer un résultat trompeur sur un
balayage partiel.
"""

from __future__ import annotations

import re

from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

_TOKEN_RE = re.compile(
    r"<!--.*?-->"
    r"|<\?.*?\?>"
    r"|<!\[CDATA\[.*?\]\]>"
    r"|</(?P<close>[A-Za-z_][\w.:-]*)\s*>"
    r"|<(?P<open>[A-Za-z_][\w.:-]*)"
    r"(?P<attrs>(?:[^<>\"']|\"[^\"]*\"|'[^']*')*?)"
    r"(?P<selfclose>/)?>",
    re.DOTALL,
)


def _scan_xpath(text: str, offset: int) -> str:
    """Balaie ``text[:offset]`` et renvoie le chemin XPath absolu de
    l'élément dans lequel se trouve ``offset`` (entre sa balise ouvrante
    et sa balise fermante). Renvoie ``"/"`` si ``offset`` est hors de
    tout élément (avant la racine, ou après sa fermeture).

    Ne suppose pas que le document est bien formé au-delà d'``offset`` :
    une balise non refermée avant ``offset`` reste simplement ouverte
    dans la pile renvoyée.
    """
    frames: list[dict[str, int]] = [{}]
    stack: list[tuple[str, int]] = []
    for match in _TOKEN_RE.finditer(text, 0, offset):
        close_name = match.group("close")
        if close_name is not None:
            if stack:
                stack.pop()
                frames.pop()
            continue
        open_name = match.group("open")
        if open_name is None:
            # Commentaire, instruction de traitement ou CDATA : rien à faire.
            continue
        counts = frames[-1]
        counts[open_name] = counts.get(open_name, 0) + 1
        index = counts[open_name]
        if match.group("selfclose"):
            continue
        stack.append((open_name, index))
        frames.append({})
    if not stack:
        return "/"
    return "/" + "/".join(f"{name}[{index}]" for name, index in stack)


def current_xpath(text: str, offset: int) -> str | None:
    """Renvoie l'XPath absolu de l'élément courant à ``offset`` dans
    ``text``, ou ``None`` si ``text`` est actuellement mal formé
    (l'appelant doit alors afficher un indicateur neutre).
    """
    try:
        parse_xml_safely(text)
    except UnsafeXmlError:
        return None
    offset = max(0, min(offset, len(text)))
    return _scan_xpath(text, offset)
