"""Conversion XML TEI (``<body>``) ↔ ``Block``/``InlineRun`` (ADR-0009).

Pur Python, testable sans Qt : ``lxml`` pour analyser, et de simples
chaînes pour resérialiser (pas de sérialiseur ``lxml`` générique — on ne
produit que les quelques balises du périmètre du premier jalon,
``model.BLOCK_TAGS``/``CONTAINER_TAGS``/``INLINE_TAGS``).

**Politique de simplification (le cœur du risque accepté, voir ADR-0009).**
Tout élément rencontré dans ``<body>`` qui n'est dans aucune des tables de
``model.py`` est désenveloppé : son texte est conservé comme texte brut,
sa balise et ses attributs sont supprimés. Appliqué récursivement, donc
sans distinction entre « élément de bloc inconnu » et « élément inline
inconnu » : les deux redeviennent simplement du texte, à l'endroit où ils
apparaissent.
"""

from __future__ import annotations

from lxml import etree

from tei_editor.editor.current_element import ElementSpan, element_spans, local_name
from tei_editor.tei.xml_safety import parse_xml_safely

from .model import BLOCK_TAGS, INLINE_TAGS, Block, InlineRun, merge_adjacent_runs

_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def find_body_element(root: etree._Element) -> etree._Element | None:
    for element in root.iter():
        if isinstance(element.tag, str) and local_name(element.tag) == "body":
            return element
    return None


# -- XML -> Blocs -------------------------------------------------------------
def _extract_runs(
    element: etree._Element, *, ambient_style: str | None = None, ambient_lang: str | None = None
) -> list[InlineRun]:
    runs: list[InlineRun] = []
    if element.text:
        runs.append(InlineRun(text=element.text, style=ambient_style, lang=ambient_lang))
    for child in element:
        if not isinstance(child.tag, str):
            # Commentaire/PI : transparent, seul son texte suivant (tail)
            # compte, comme pour tout élément désenveloppé.
            if child.tail:
                runs.append(InlineRun(text=child.tail, style=ambient_style, lang=ambient_lang))
            continue
        tag = local_name(child.tag)
        if tag in INLINE_TAGS:
            child_lang = child.get(_XML_LANG_ATTR) if tag == "foreign" else None
            runs.extend(_extract_runs(child, ambient_style=tag, ambient_lang=child_lang))
        else:
            # Politique de simplification : élément inline non modélisé,
            # transparent (hérite du style ambiant, pas le sien).
            runs.extend(_extract_runs(child, ambient_style=ambient_style, ambient_lang=ambient_lang))
        if child.tail:
            runs.append(InlineRun(text=child.tail, style=ambient_style, lang=ambient_lang))
    return runs


def _walk_container(container: etree._Element, *, div_depth: int, list_depth: int) -> list[Block]:
    blocks: list[Block] = []
    for child in container:
        if not isinstance(child.tag, str):
            continue
        tag = local_name(child.tag)
        if tag == "div":
            blocks.extend(_walk_container(child, div_depth=div_depth + 1, list_depth=list_depth))
        elif tag == "lg":
            blocks.extend(_walk_container(child, div_depth=div_depth, list_depth=list_depth))
        elif tag == "list":
            blocks.extend(_walk_container(child, div_depth=div_depth, list_depth=list_depth + 1))
        elif tag == "head":
            level = max(1, min(div_depth, 4))
            blocks.append(Block(kind="head", level=level, runs=merge_adjacent_runs(_extract_runs(child))))
        elif tag == "item":
            level = max(1, list_depth)
            blocks.append(Block(kind="item", level=level, runs=merge_adjacent_runs(_extract_runs(child))))
        elif tag in ("p", "l", "note"):
            blocks.append(Block(kind=tag, level=div_depth, runs=merge_adjacent_runs(_extract_runs(child))))
        else:
            # Politique de simplification : élément de bloc non modélisé
            # (apparat critique, théâtre, table, figure...) -> désenveloppé
            # en un seul paragraphe, texte brut conservé, balise perdue.
            flattened = merge_adjacent_runs(_extract_runs(child))
            if flattened:
                blocks.append(Block(kind="p", level=div_depth, runs=flattened))
    return blocks


def xml_to_blocks(body: etree._Element) -> list[Block]:
    """Convertit le contenu de ``<body>`` en une liste plate de blocs.

    Les conteneurs (``div``/``lg``/``list``) n'apparaissent pas comme
    blocs : seule leur profondeur (``Block.level``) est conservée."""
    return _walk_container(body, div_depth=0, list_depth=0)


# -- Blocs -> XML -------------------------------------------------------------
def _escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(text: str) -> str:
    return _escape_text(text).replace('"', "&quot;")


def _runs_to_xml(runs: list[InlineRun]) -> str:
    parts: list[str] = []
    for run in runs:
        text = _escape_text(run.text)
        if run.style is None:
            parts.append(text)
        elif run.style == "foreign" and run.lang:
            parts.append(f'<foreign xml:lang="{_escape_attr(run.lang)}">{text}</foreign>')
        else:
            parts.append(f"<{run.style}>{text}</{run.style}>")
    return "".join(parts)


def blocks_to_xml(blocks: list[Block]) -> str:
    """Resérialise une liste plate de blocs en XML TEI (contenu de
    ``<body>``, sans la balise ``<body>`` elle-même — voir
    :func:`replace_body_in_document`)."""
    parts: list[str] = []
    div_depth = 0
    list_depth = 0
    lg_open = False

    def close_lg() -> None:
        nonlocal lg_open
        if lg_open:
            parts.append("</lg>")
            lg_open = False

    def set_list_depth(target: int) -> None:
        nonlocal list_depth
        while list_depth > target:
            parts.append("</list>")
            list_depth -= 1
        while list_depth < target:
            parts.append("<list>")
            list_depth += 1

    def set_div_depth(target: int) -> None:
        nonlocal div_depth
        while div_depth > target:
            parts.append("</div>")
            div_depth -= 1
        while div_depth < target:
            parts.append("<div>")
            div_depth += 1

    for block in blocks:
        if block.kind in ("head", "p", "note"):
            close_lg()
            set_list_depth(0)
            set_div_depth(block.level)
            parts.append(f"<{block.kind}>{_runs_to_xml(block.runs)}</{block.kind}>")
        elif block.kind == "l":
            set_list_depth(0)
            set_div_depth(block.level)
            if not lg_open:
                parts.append("<lg>")
                lg_open = True
            parts.append(f"<l>{_runs_to_xml(block.runs)}</l>")
        elif block.kind == "item":
            close_lg()
            set_list_depth(block.level)
            parts.append(f"<item>{_runs_to_xml(block.runs)}</item>")
    close_lg()
    set_list_depth(0)
    set_div_depth(0)
    return "".join(parts)


def replace_body_in_document(full_text: str, new_body_inner_xml: str) -> str:
    """Remplace uniquement le contenu de ``<body>...</body>`` dans
    ``full_text`` par ``new_body_inner_xml``. Tout ce qui est hors
    ``<body>`` (``teiHeader``, prologue, ``front``/``back``) reste
    byte-identique.

    Lève :class:`tei_editor.tei.xml_safety.UnsafeXmlError` si
    ``full_text`` est mal formé, ``ValueError`` si aucun ``<body>`` n'y
    est trouvé."""
    root = parse_xml_safely(full_text)
    body = find_body_element(root)
    if body is None:
        raise ValueError("Aucun élément <body> dans ce document : bascule WYSIWYG impossible.")
    spans = element_spans(root, full_text)
    span: ElementSpan | None = spans.get(id(body))
    if span is None or span.self_closing:
        raise ValueError("L'élément <body> est introuvable ou auto-fermant.")
    return full_text[: span.content_start] + new_body_inner_xml + full_text[span.content_end :]
