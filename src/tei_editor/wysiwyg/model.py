"""Modèle ``Block``/``InlineRun`` du mode WYSIWYG (ADR-0009).

Pur Python, sans Qt ni ``lxml`` : juste les deux structures de données et
les tables de correspondance qui définissent le périmètre du premier
jalon (profil « Édition de textes »). ``Block.kind``/``InlineRun.style``
sont littéralement le nom de la balise TEI qu'ils représentent (pas un
identifiant abstrait) : ça évite une table de correspondance inverse
séparée au moment de resérialiser en XML (``xml_adapter.blocks_to_xml``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Éléments TEI traités comme un bloc (un paragraphe/une ligne du
#: ``QTextDocument`` par occurrence). ``Block.kind`` est le nom de la
#: balise elle-même.
BLOCK_TAGS: frozenset[str] = frozenset({"head", "p", "l", "item", "note"})

#: Éléments conteneurs : ne produisent pas de bloc propre, seulement un
#: changement de profondeur pour les blocs qu'ils contiennent (``div``
#: pour ``head``/``p``/``l``/``note``, ``list`` pour ``item``, ``lg``
#: regroupe les ``l`` consécutifs sans créer de niveau propre).
CONTAINER_TAGS: frozenset[str] = frozenset({"div", "lg", "list"})

#: Éléments TEI traités comme une mise en forme inline (portée sur une
#: plage de texte à l'intérieur d'un bloc). ``InlineRun.style`` est le nom
#: de la balise elle-même.
INLINE_TAGS: frozenset[str] = frozenset(
    {"hi", "emph", "foreign", "title", "persName", "placeName", "orgName", "name", "date"}
)


@dataclass
class InlineRun:
    """Une plage de texte avec une mise en forme optionnelle.

    ``lang`` ne porte que le ``@xml:lang`` de ``<foreign>`` : seul
    attribut conservé dans ce premier jalon (ADR-0009). Tout autre
    attribut, sur n'importe quel élément, est perdu à la conversion
    (politique de simplification)."""

    text: str
    style: str | None = None
    lang: str | None = None


@dataclass
class Block:
    """Un bloc de niveau paragraphe/ligne.

    ``level`` est la profondeur de ``div`` ancêtres pour ``head``/``p``/
    ``l``/``note`` (0 = directement sous ``<body>``), et la profondeur de
    ``list`` ancêtres pour ``item`` (1 = premier niveau) — deux axes
    indépendants, volontairement : une liste n'ouvre pas une nouvelle
    « section » au sens d'un ``div``."""

    kind: str
    level: int
    runs: list[InlineRun] = field(default_factory=list)


def merge_adjacent_runs(runs: list[InlineRun]) -> list[InlineRun]:
    """Fusionne les ``InlineRun`` consécutifs de même ``style``/``lang``,
    et retire les runs de texte vide. Utilisé à la fois en sortie de
    ``xml_adapter.xml_to_blocks`` et de ``document_adapter.qtextdocument_to_blocks``
    pour ne pas produire de fragmentation artificielle (un run par
    frontière de ``QTextFragment`` ne correspond pas forcément à un
    changement de style réel)."""
    merged: list[InlineRun] = []
    for run in runs:
        if not run.text:
            continue
        if merged and merged[-1].style == run.style and merged[-1].lang == run.lang:
            previous = merged[-1]
            previous.text += run.text
        else:
            merged.append(InlineRun(text=run.text, style=run.style, lang=run.lang))
    return merged
