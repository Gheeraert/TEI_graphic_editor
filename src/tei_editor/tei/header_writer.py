"""Écriture **chirurgicale** des sous-éléments de ``<teiHeader>`` modifiés
par l'assistant (phase 6, ``docs/ROADMAP.md`` §5).

Pour chaque sous-élément géré dont les données ont changé (comparaison
entre ce qui a été lu par :mod:`tei_editor.tei.header_reader` et ce que le
dialogue a édité), ce module sérialise *uniquement ce sous-élément* et
remplace sa plage de texte source exacte (ou l'insère au bon endroit s'il
n'existait pas). Les sous-éléments inchangés ne sont **jamais**
réécrits : pas de diff calculé à partir d'une resérialisation complète,
l'octet d'origine est laissé tel quel (ADR-0001).

Réutilise le mécanisme à bloc d'annulation unique de la phase 5
(:mod:`tei_editor.editor.structured_edits`, :class:`TextEdit` et
:func:`apply_edits_with_cursor`) plutôt que d'en inventer un autre
(ADR-0008) : toute l'opération « Appliquer » de l'assistant forme un seul
pas d'annulation natif.
"""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from tei_editor.editor.structured_edits import TextEdit
from tei_editor.tei.header_model import (
    EditionStatement,
    EncodingDescription,
    PublicationStatement,
    ProfileDescription,
    ResponsibleParty,
    RevisionDescription,
    SourceDescription,
    TeiHeaderData,
    TitleEntry,
)
from tei_editor.tei.header_reader import HeaderReadResult
from tei_editor.tei.licenses import resolve_license


def _esc(text: str) -> str:
    return escape(text or "")


def _attr(name: str, value: str | None) -> str:
    return f" {name}={quoteattr(value)}" if value else ""


# -- Sérialisation par sous-élément -------------------------------------------


def serialize_title_stmt(titles: list[TitleEntry], parties: list[ResponsibleParty], indent: str, extra: str = "") -> str:
    inner = indent + "  "
    inner2 = indent + "    "
    lines = ["<titleStmt>"]
    for title in titles:
        lines.append(f"{inner}<title{_attr('type', title.type)}>{_esc(title.text)}</title>")
    for party in parties:
        if party.role == "respStmt":
            lines.append(f"{inner}<respStmt>")
            if party.resp_label:
                lines.append(f"{inner2}<resp>{_esc(party.resp_label)}</resp>")
            lines.append(f"{inner2}<name>{_esc(party.name)}</name>")
            if party.affiliation:
                lines.append(f"{inner2}<affiliation>{_esc(party.affiliation)}</affiliation>")
            lines.append(f"{inner}</respStmt>")
        else:
            lines.append(f"{inner}<{party.role}{_attr('role', party.role_attribute)}>")
            if party.orcid:
                lines.append(f"{inner2}<persName ref={quoteattr(party.orcid)}>{_esc(party.name)}</persName>")
            else:
                lines.append(f"{inner2}<persName>{_esc(party.name)}</persName>")
            if party.affiliation:
                lines.append(f"{inner2}<affiliation>{_esc(party.affiliation)}</affiliation>")
            lines.append(f"{inner}</{party.role}>")
    body = "\n".join(lines[1:])
    tail = extra if extra else ""
    return f"<titleStmt>\n{body}{tail}\n{indent}</titleStmt>" if body else f"<titleStmt>{tail}\n{indent}</titleStmt>"


def serialize_edition_stmt(edition: EditionStatement, indent: str) -> str:
    inner = indent + "  "
    return f"<editionStmt>\n{inner}<edition{_attr('n', edition.n)}>{_esc(edition.text)}</edition>\n{indent}</editionStmt>"


def serialize_extent(text: str) -> str:
    return f"<extent>{_esc(text)}</extent>"


def serialize_publication_stmt(publication: PublicationStatement, indent: str, extra: str = "") -> str:
    inner = indent + "  "
    inner2 = indent + "    "
    lines = []
    if publication.publisher:
        lines.append(f"{inner}<publisher>{_esc(publication.publisher)}</publisher>")
    if publication.pub_place:
        lines.append(f"{inner}<pubPlace>{_esc(publication.pub_place)}</pubPlace>")
    if publication.date_when or publication.date_text:
        lines.append(
            f"{inner}<date{_attr('when', publication.date_when)}>"
            f"{_esc(publication.date_text or publication.date_when)}</date>"
        )
    for identifier in publication.identifiers:
        if not identifier.value:
            continue
        lines.append(f"{inner}<idno{_attr('type', identifier.type)}>{_esc(identifier.value)}</idno>")
    resolved = resolve_license(
        spdx_id=publication.license_spdx_id, name=publication.license_name, url=publication.license_url
    )
    has_availability = bool(resolved.name or resolved.url or publication.rights_statement or publication.availability_status)
    if has_availability:
        lines.append(f"{inner}<availability{_attr('status', publication.availability_status)}>")
        if resolved.name:
            lines.append(f"{inner2}<licence{_attr('target', resolved.url)}>{_esc(resolved.name)}</licence>")
        for paragraph in (publication.rights_statement or "").splitlines():
            if paragraph.strip():
                lines.append(f"{inner2}<p>{_esc(paragraph.strip())}</p>")
        lines.append(f"{inner}</availability>")
    if not lines and not extra.strip():
        lines.append(f"{inner}<p>Non publié.</p>")
    body = "\n".join(lines)
    tail = extra if extra else ""
    if body:
        return f"<publicationStmt>\n{body}{tail}\n{indent}</publicationStmt>"
    return f"<publicationStmt>{tail}\n{indent}</publicationStmt>"


def serialize_source_desc(source: SourceDescription, indent: str, extra: str = "") -> str:
    inner = indent + "  "
    inner2 = indent + "    "
    inner3 = indent + "      "
    tail = extra if extra else ""
    if source.mode == "msDesc":
        lines = [f"{inner}<msDesc>", f"{inner2}<msIdentifier>"]
        if source.msdesc_repository:
            lines.append(f"{inner3}<repository>{_esc(source.msdesc_repository)}</repository>")
        lines.append(f"{inner3}<idno>{_esc(source.msdesc_idno or 'non précisé')}</idno>")
        lines.append(f"{inner2}</msIdentifier>")
        if source.msdesc_summary:
            lines.append(f"{inner2}<physDesc><p>{_esc(source.msdesc_summary)}</p></physDesc>")
        lines.append(f"{inner}</msDesc>")
        body = "\n".join(lines)
        return f"<sourceDesc>\n{body}{tail}\n{indent}</sourceDesc>"
    text = source.bibl_text or "Source non précisée."
    return f"<sourceDesc>\n{inner}<bibl>{_esc(text)}</bibl>{tail}\n{indent}</sourceDesc>"


def serialize_encoding_desc(encoding: EncodingDescription, indent: str, extra: str = "") -> str:
    inner = indent + "  "
    lines = []
    if encoding.project_desc:
        lines.append(f"{inner}<projectDesc><p>{_esc(encoding.project_desc)}</p></projectDesc>")
    if encoding.editorial_decl:
        lines.append(f"{inner}<editorialDecl><p>{_esc(encoding.editorial_decl)}</p></editorialDecl>")
    if encoding.tags_decl:
        # `tagsDecl` n'admet que `namespace`/`rendition` comme enfants (pas
        # `<p>`) : un texte libre est porté par une `<rendition>`
        # descriptive, qui accepte du texte directement — il ne s'agit pas
        # d'une véritable règle de présentation CSS, juste d'un porteur de
        # texte libre conforme au schéma.
        lines.append(f"{inner}<rendition>{_esc(encoding.tags_decl)}</rendition>")
    if not lines and not extra.strip():
        lines.append(f"{inner}<p>Aucune déclaration d'encodage.</p>")
    body = "\n".join(lines)
    tail = extra if extra else ""
    if body:
        return f"<encodingDesc>\n{body}{tail}\n{indent}</encodingDesc>"
    return f"<encodingDesc>{tail}\n{indent}</encodingDesc>"


def serialize_profile_desc(profile: ProfileDescription, indent: str, extra: str = "") -> str:
    inner = indent + "  "
    inner2 = indent + "    "
    lines = []
    if profile.languages:
        lines.append(f"{inner}<langUsage>")
        for language in profile.languages:
            lines.append(
                f"{inner2}<language{_attr('ident', language.ident)}{_attr('usage', language.usage_percent)}>"
                f"{_esc(language.name)}</language>"
            )
        lines.append(f"{inner}</langUsage>")
    if profile.keywords:
        lines.append(f"{inner}<textClass>")
        lines.append(f"{inner2}<keywords>")
        for keyword in profile.keywords:
            lines.append(f"{inner2}  <term>{_esc(keyword)}</term>")
        lines.append(f"{inner2}</keywords>")
        lines.append(f"{inner}</textClass>")
    if profile.abstract:
        lines.append(f"{inner}<abstract><p>{_esc(profile.abstract)}</p></abstract>")
    if profile.participants:
        lines.append(f"{inner}<particDesc><p>{_esc(profile.participants)}</p></particDesc>")
    if not lines and not extra.strip():
        lines.append(f"{inner}<langUsage><language ident=\"fr\">français</language></langUsage>")
    body = "\n".join(lines)
    tail = extra if extra else ""
    if body:
        return f"<profileDesc>\n{body}{tail}\n{indent}</profileDesc>"
    return f"<profileDesc>{tail}\n{indent}</profileDesc>"


def serialize_revision_desc(revisions: RevisionDescription, indent: str, extra: str = "") -> str:
    inner = indent + "  "
    lines = []
    for change in revisions.changes:
        lines.append(
            f"{inner}<change{_attr('when', change.when)}{_attr('who', change.who)}>{_esc(change.description)}</change>"
        )
    if not revisions.changes and not extra.strip():
        lines.append(f"{inner}<change>Sans historique de révision.</change>")
    body = "\n".join(lines)
    tail = extra if extra else ""
    opening = f"<revisionDesc{_attr('status', revisions.status)}>"
    if body:
        return f"{opening}\n{body}{tail}\n{indent}</revisionDesc>"
    return f"{opening}{tail}\n{indent}</revisionDesc>"


# -- Comparaison + plan d'édition ---------------------------------------------

#: Pour chaque clef gérée : (attribut de TeiHeaderData à comparer, fonction
#: de sérialisation prenant les données + l'indentation).
_SERIALIZERS = {
    "titleStmt": lambda data, indent, extra: serialize_title_stmt(data.titles, data.responsible_parties, indent, extra),
    "editionStmt": lambda data, indent, extra: serialize_edition_stmt(data.edition, indent),
    "extent": lambda data, indent, extra: serialize_extent(data.extent),
    "publicationStmt": lambda data, indent, extra: serialize_publication_stmt(data.publication, indent, extra),
    "sourceDesc": lambda data, indent, extra: serialize_source_desc(data.source, indent, extra),
    "encodingDesc": lambda data, indent, extra: serialize_encoding_desc(data.encoding, indent, extra),
    "profileDesc": lambda data, indent, extra: serialize_profile_desc(data.profile, indent, extra),
    "revisionDesc": lambda data, indent, extra: serialize_revision_desc(data.revisions, indent, extra),
}

#: Champ de :class:`TeiHeaderData` dont la modification déclenche la
#: réécriture de chaque clef (``titleStmt`` dépend de deux champs : titres
#: ET responsables).
_CHANGE_FIELDS = {
    "titleStmt": ("titles", "responsible_parties"),
    "editionStmt": ("edition",),
    "extent": ("extent",),
    "publicationStmt": ("publication",),
    "sourceDesc": ("source",),
    "encodingDesc": ("encoding",),
    "profileDesc": ("profile",),
    "revisionDesc": ("revisions",),
}


def changed_keys(original: TeiHeaderData, edited: TeiHeaderData) -> list[str]:
    """Clefs des sous-éléments dont les données ont changé entre
    ``original`` (tel que lu par :func:`header_reader.read_header`) et
    ``edited`` (tel qu'édité dans le dialogue)."""
    changed = []
    for key, fields in _CHANGE_FIELDS.items():
        if any(getattr(original, field) != getattr(edited, field) for field in fields):
            changed.append(key)
    return changed


def plan_header_edits(read_result: HeaderReadResult, edited: TeiHeaderData) -> list[TextEdit]:
    """Calcule le plan d'édition minimal : un :class:`TextEdit` par
    sous-élément dont les données ont changé, et seulement ceux-là. Les
    clefs absentes de ``read_result.locations`` (``<fileDesc>`` lui-même
    manquant, limitation assumée — voir le docstring de
    :mod:`header_reader`) sont silencieusement ignorées plutôt que de
    produire une plage invalide."""
    edits: list[TextEdit] = []
    for key in changed_keys(read_result.data, edited):
        location = read_result.locations.get(key)
        if location is None:
            continue
        extra = read_result.extra_xml.get(key, "")
        serialized = _SERIALIZERS[key](edited, location.indent, extra)
        replacement = serialized if location.exists else f"\n{location.indent}{serialized}"
        edits.append(TextEdit(location.start, location.end, replacement))
    return edits
