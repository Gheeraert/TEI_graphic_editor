"""Lecture **sans perte** d'un ``<teiHeader>`` existant (phase 6,
``docs/ROADMAP.md`` §5) : le cœur technique de cette phase.

Pour chacun des sous-éléments que l'assistant gère explicitement
(:mod:`tei_editor.tei.header_model`), ce module calcule à la fois :

- les valeurs à afficher dans le modèle de données (lecture *tolérante* :
  un ``<teiHeader>`` incomplet ou aux variantes de structure raisonnables
  se lit sans planter, remplit ce qu'il peut, laisse le reste vide) ;
- la **plage exacte de texte source** occupée par ce sous-élément
  (:class:`SubElementLocation`), ou son point d'insertion s'il n'existe
  pas encore.

Conformément à ADR-0001, la fidélité repose sur le **texte**, pas sur un
modèle objet reconstruit puis resérialisé. Ce module ne construit
*jamais* un sous-élément qu'il ne gère pas explicitement (``seriesStmt``,
``notesStmt``, ``classDecl``, ``appInfo``, tout élément/attribut/commentaire
personnalisé...) : la préservation de ces « zones non gérées » découle
simplement du fait qu'elles ne sont ni lues ni jamais référencées par une
plage à réécrire — c'est :mod:`tei_editor.tei.header_writer` qui, en ne
touchant qu'aux plages listées ici, laisse tout le reste du document
strictement intact (voir ses tests de non-perte).

Repose sur :func:`tei_editor.editor.current_element.element_spans`
(même mécanisme de repérage par positions déjà utilisé par les
opérations structurées de la phase 5), pas un second algorithme.
"""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from tei_editor.editor.current_element import element_spans, local_name
from tei_editor.tei.header_model import (
    ChangeEntry,
    EditionStatement,
    EncodingDescription,
    IdentifierEntry,
    LanguageUsage,
    PublicationStatement,
    ResponsibleParty,
    RevisionDescription,
    SourceDescription,
    ProfileDescription,
    TeiHeaderData,
    TitleEntry,
)
from tei_editor.tei.licenses import SPDX_LICENSES
from tei_editor.tei.xml_safety import UnsafeXmlError, parse_xml_safely

#: Ordre schématique des enfants directs de ``<fileDesc>`` pertinents pour
#: le calcul des points d'insertion (y compris les enfants non gérés,
#: ``seriesStmt``/``notesStmt``, pour que l'insertion d'un sous-élément
#: géré respecte leur position s'ils sont présents).
_FILEDESC_ORDER = [
    "titleStmt",
    "editionStmt",
    "extent",
    "publicationStmt",
    "seriesStmt",
    "notesStmt",
    "sourceDesc",
]

#: Ordre schématique des enfants directs de ``<teiHeader>`` pertinents
#: pour le calcul des points d'insertion (``xenoData`` inclus bien que
#: non géré, pour un positionnement correct de ``revisionDesc`` s'il est
#: présent).
_HEADER_ORDER = ["fileDesc", "encodingDesc", "profileDesc", "xenoData", "revisionDesc"]

_MANAGED_FILEDESC_KEYS = ("titleStmt", "editionStmt", "extent", "publicationStmt", "sourceDesc")
_MANAGED_HEADER_KEYS = ("encodingDesc", "profileDesc", "revisionDesc")

#: Pour chaque conteneur géré qui a des enfants structurés (pas
#: `editionStmt`/`extent`, de simples feuilles texte), le nom des enfants
#: directs effectivement gérés par le modèle de données. Tout autre
#: enfant direct (ex. `<refsDecl>`/`<classDecl>` dans `encodingDesc`,
#: `<creation>` dans `profileDesc`, `<sponsor>` dans `titleStmt`...) est
#: une « zone non gérée » : son texte brut exact est conservé par
#: :func:`_extra_xml` et resplicé verbatim par `header_writer` quand le
#: conteneur est régénéré — pas seulement quand il ne l'est pas.
_MANAGED_CHILDREN_OF_CONTAINER: dict[str, set[str]] = {
    "titleStmt": {"title", "author", "editor", "funder", "respStmt"},
    "publicationStmt": {"publisher", "pubPlace", "date", "idno", "availability"},
    "sourceDesc": {"bibl", "msDesc"},
    "encodingDesc": {"projectDesc", "editorialDecl", "tagsDecl"},
    "profileDesc": {"langUsage", "textClass", "abstract", "particDesc"},
    "revisionDesc": {"change"},
}

_INDENT_FILEDESC_CHILD = "      "
_INDENT_HEADER_CHILD = "    "

_SPDX_BY_URL_OR_NAME: dict[tuple[str, str], str] = {
    (name, url): spdx_id for spdx_id, (name, url) in SPDX_LICENSES.items()
}


@dataclass(frozen=True)
class SubElementLocation:
    """Plage exacte ``[start, end)`` du sous-élément dans le texte source
    quand ``exists`` est vrai ; sinon, ``start == end`` est son point
    d'insertion. ``indent`` est l'indentation à utiliser par
    :mod:`header_writer` pour une insertion (sans effet quand ``exists``)."""

    exists: bool
    start: int
    end: int
    indent: str


@dataclass
class HeaderReadResult:
    """Résultat complet de la lecture : modèle de données rempli +
    emplacements des sous-éléments gérés. ``well_formed`` est faux pour
    un document mal formé (rien d'autre n'est alors exploitable).
    ``header_exists``/``file_desc_exists`` signalent les cas marginaux où
    ``<teiHeader>``/``<fileDesc>`` lui-même est absent : l'assistant reste
    alors en lecture tolérante (modèle vide), mais
    :mod:`header_writer` ne peut pas construire ces ancêtres manquants
    (limitation assumée, voir le docstring de ce module)."""

    data: TeiHeaderData
    locations: dict[str, SubElementLocation]
    header_exists: bool
    file_desc_exists: bool
    well_formed: bool
    extra_xml: dict[str, str] = None  # type: ignore[assignment]  # défini dans __post_init__

    def __post_init__(self) -> None:
        if self.extra_xml is None:
            self.extra_xml = {}


# -- Utilitaires -------------------------------------------------------------


def _direct_child(parent: etree._Element | None, name: str) -> etree._Element | None:
    if parent is None:
        return None
    for child in parent:
        if isinstance(child.tag, str) and local_name(child.tag) == name:
            return child
    return None


def _direct_children(parent: etree._Element | None, names) -> list[etree._Element]:
    if parent is None:
        return []
    return [c for c in parent if isinstance(c.tag, str) and local_name(c.tag) in names]


def _text(el: etree._Element | None) -> str:
    if el is None:
        return ""
    return " ".join("".join(el.itertext()).split())


def _element_end(span) -> int:
    return span.end_tag_end if span.end_tag_end is not None else span.start_tag_end


def _extra_xml(container_el: etree._Element | None, container_span, text: str, managed_names: set[str], spans) -> str:
    """Texte brut exact des enfants directs de ``container_el`` qui ne
    sont *pas* dans ``managed_names`` (zone non gérée), avec les espaces
    environnants, tel qu'il faut le resplicer verbatim quand
    ``header_writer`` régénère ce conteneur (voir
    :data:`_MANAGED_CHILDREN_OF_CONTAINER`). Calculé en retirant du texte
    intérieur du conteneur les plages des enfants *gérés* : ce qui reste
    est, par construction, exactement le contenu non géré (enfants
    inconnus + la ponctuation blanche d'origine)."""
    if container_el is None or container_span is None:
        return ""
    content_start = container_span.content_start
    content_end = container_span.content_end
    deletions: list[tuple[int, int]] = []
    for child in container_el:
        if not isinstance(child.tag, str):
            continue
        if local_name(child.tag) not in managed_names:
            continue
        span = spans.get(id(child))
        if span is not None:
            deletions.append((span.start_tag_start, _element_end(span)))
    inner = text[content_start:content_end]
    for start, end in sorted(deletions, key=lambda r: r[0], reverse=True):
        inner = inner[: start - content_start] + inner[end - content_start :]
    return inner


def _insertion_point(parent_el, parent_span, spans, order: list[str], target_name: str) -> int | None:
    if parent_el is None or parent_span is None:
        return None
    best_end = parent_span.content_start
    target_rank = order.index(target_name) if target_name in order else len(order)
    for child in parent_el:
        if not isinstance(child.tag, str):
            continue
        name = local_name(child.tag)
        rank = order.index(name) if name in order else len(order)
        span = spans.get(id(child))
        if span is None or rank > target_rank:
            continue
        best_end = max(best_end, _element_end(span))
    return best_end


# -- Extraction par sous-élément ---------------------------------------------


def _read_title_stmt(title_stmt: etree._Element | None) -> tuple[list[TitleEntry], list[ResponsibleParty]]:
    titles: list[TitleEntry] = []
    parties: list[ResponsibleParty] = []
    if title_stmt is None:
        return titles, parties
    for child in title_stmt:
        if not isinstance(child.tag, str):
            continue
        name = local_name(child.tag)
        if name == "title":
            titles.append(TitleEntry(text=_text(child), type=child.get("type")))
        elif name in ("author", "editor", "funder"):
            parties.append(_read_simple_responsible_party(child, name))
        elif name == "respStmt":
            resp = _direct_child(child, "resp")
            name_el = _direct_child(child, "name")
            parties.append(
                ResponsibleParty(
                    role="respStmt",
                    name=_text(name_el),
                    resp_label=_text(resp) or None,
                    affiliation=_text(_direct_child(child, "affiliation")) or None,
                )
            )
    return titles, parties


def _read_simple_responsible_party(child: etree._Element, role: str) -> ResponsibleParty:
    pers_name = _direct_child(child, "persName")
    orcid: str | None = None
    if pers_name is not None:
        name_value = _text(pers_name)
        ref = pers_name.get("ref") or ""
        if "orcid.org" in ref:
            orcid = ref
    else:
        name_value = _text(child)
    if orcid is None:
        idno = next(
            (el for el in child.iter() if isinstance(el.tag, str) and local_name(el.tag) == "idno" and el.get("type") == "ORCID"),
            None,
        )
        if idno is not None:
            orcid = _text(idno) or None
    affiliation = _text(_direct_child(child, "affiliation")) or None
    return ResponsibleParty(
        role=role,  # type: ignore[arg-type]
        name=name_value,
        role_attribute=child.get("role"),
        orcid=orcid,
        affiliation=affiliation,
    )


def _read_edition(edition_stmt: etree._Element | None) -> EditionStatement:
    if edition_stmt is None:
        return EditionStatement()
    edition = _direct_child(edition_stmt, "edition")
    if edition is not None:
        return EditionStatement(text=_text(edition), n=edition.get("n"))
    return EditionStatement(text=_text(edition_stmt))


def _read_publication(publication_stmt: etree._Element | None) -> PublicationStatement:
    result = PublicationStatement()
    if publication_stmt is None:
        return result
    result.publisher = _text(_direct_child(publication_stmt, "publisher"))
    result.pub_place = _text(_direct_child(publication_stmt, "pubPlace"))
    date_el = _direct_child(publication_stmt, "date")
    if date_el is not None:
        result.date_when = date_el.get("when") or ""
        result.date_text = _text(date_el)
    result.identifiers = [
        IdentifierEntry(type=idno.get("type"), value=_text(idno))
        for idno in _direct_children(publication_stmt, {"idno"})
    ]
    availability = _direct_child(publication_stmt, "availability")
    if availability is not None:
        result.availability_status = availability.get("status")
        licence = _direct_child(availability, "licence")
        if licence is not None:
            result.license_name = _text(licence) or None
            result.license_url = licence.get("target")
            key = (result.license_name or "", result.license_url or "")
            result.license_spdx_id = _SPDX_BY_URL_OR_NAME.get(key)
        statements = [
            _text(p) for p in _direct_children(availability, {"p"}) if _text(p)
        ]
        result.rights_statement = "\n".join(statements)
    return result


def _read_source(source_desc: etree._Element | None) -> SourceDescription:
    result = SourceDescription()
    if source_desc is None:
        return result
    msdesc = _direct_child(source_desc, "msDesc")
    bibl = _direct_child(source_desc, "bibl")
    if msdesc is not None:
        result.mode = "msDesc"
        ms_identifier = _direct_child(msdesc, "msIdentifier")
        if ms_identifier is not None:
            result.msdesc_repository = _text(_direct_child(ms_identifier, "repository"))
            result.msdesc_idno = _text(_direct_child(ms_identifier, "idno"))
        result.msdesc_summary = _text(_direct_child(msdesc, "physDesc")) or _text(msdesc)
    elif bibl is not None:
        result.mode = "bibl"
        result.bibl_text = _text(bibl)
    else:
        result.mode = "bibl"
        result.bibl_text = _text(source_desc)
    return result


def _read_encoding(encoding_desc: etree._Element | None) -> EncodingDescription:
    result = EncodingDescription()
    if encoding_desc is None:
        return result
    result.project_desc = _text(_direct_child(encoding_desc, "projectDesc"))
    result.editorial_decl = _text(_direct_child(encoding_desc, "editorialDecl"))
    result.tags_decl = _text(_direct_child(encoding_desc, "tagsDecl"))
    return result


def _read_profile(profile_desc: etree._Element | None) -> ProfileDescription:
    result = ProfileDescription()
    if profile_desc is None:
        return result
    lang_usage = _direct_child(profile_desc, "langUsage")
    result.languages = [
        LanguageUsage(ident=lang.get("ident") or "", name=_text(lang), usage_percent=lang.get("usage"))
        for lang in _direct_children(lang_usage, {"language"})
    ]
    text_class = _direct_child(profile_desc, "textClass")
    keywords_el = _direct_child(text_class, "keywords")
    terms = _direct_children(keywords_el, {"term"})
    if terms:
        result.keywords = [_text(t) for t in terms]
    elif keywords_el is not None:
        raw = _text(keywords_el)
        result.keywords = [part.strip() for part in raw.split(",") if part.strip()]
    result.abstract = _text(_direct_child(profile_desc, "abstract"))
    result.participants = _text(_direct_child(profile_desc, "particDesc"))
    return result


def _read_revisions(revision_desc: etree._Element | None) -> RevisionDescription:
    result = RevisionDescription()
    if revision_desc is None:
        return result
    result.status = revision_desc.get("status")
    result.changes = [
        ChangeEntry(when=c.get("when") or "", who=c.get("who") or "", description=_text(c))
        for c in _direct_children(revision_desc, {"change"})
    ]
    return result


# -- Point d'entrée -----------------------------------------------------------


def read_header(text: str) -> HeaderReadResult:
    """Lit le ``<teiHeader>`` de ``text`` de façon tolérante : ne lève
    jamais, remplit ce qu'elle peut. Renvoie un résultat avec
    ``well_formed=False`` si le document n'est même pas bien formé
    (:func:`tei_editor.tei.xml_safety.parse_xml_safely`)."""
    try:
        root = parse_xml_safely(text)
    except UnsafeXmlError:
        return HeaderReadResult(
            data=TeiHeaderData(), locations={}, header_exists=False, file_desc_exists=False, well_formed=False
        )

    header_el = _direct_child(root, "teiHeader")
    data = TeiHeaderData()
    locations: dict[str, SubElementLocation] = {}
    extra_xml: dict[str, str] = {}

    if header_el is None:
        return HeaderReadResult(
            data=data, locations=locations, header_exists=False, file_desc_exists=False, well_formed=True
        )

    spans = element_spans(root, text)
    header_span = spans.get(id(header_el))

    def _record_extra(key: str, element: etree._Element | None) -> None:
        if element is None or key not in _MANAGED_CHILDREN_OF_CONTAINER:
            return
        span = spans.get(id(element))
        extra_xml[key] = _extra_xml(element, span, text, _MANAGED_CHILDREN_OF_CONTAINER[key], spans)

    file_desc_el = _direct_child(header_el, "fileDesc")
    file_desc_exists = file_desc_el is not None
    if file_desc_exists:
        file_desc_span = spans.get(id(file_desc_el))
        for key in _MANAGED_FILEDESC_KEYS:
            child = _direct_child(file_desc_el, key)
            if child is not None and id(child) in spans:
                span = spans[id(child)]
                locations[key] = SubElementLocation(True, span.start_tag_start, _element_end(span), _INDENT_FILEDESC_CHILD)
                _record_extra(key, child)
                continue
            insertion_point = _insertion_point(file_desc_el, file_desc_span, spans, _FILEDESC_ORDER, key)
            if insertion_point is not None:
                locations[key] = SubElementLocation(False, insertion_point, insertion_point, _INDENT_FILEDESC_CHILD)

        data.titles, data.responsible_parties = _read_title_stmt(_direct_child(file_desc_el, "titleStmt"))
        data.edition = _read_edition(_direct_child(file_desc_el, "editionStmt"))
        data.extent = _text(_direct_child(file_desc_el, "extent"))
        data.publication = _read_publication(_direct_child(file_desc_el, "publicationStmt"))
        data.source = _read_source(_direct_child(file_desc_el, "sourceDesc"))

    for key in _MANAGED_HEADER_KEYS:
        child = _direct_child(header_el, key)
        if child is not None and id(child) in spans:
            span = spans[id(child)]
            locations[key] = SubElementLocation(True, span.start_tag_start, _element_end(span), _INDENT_HEADER_CHILD)
            _record_extra(key, child)
            continue
        insertion_point = _insertion_point(header_el, header_span, spans, _HEADER_ORDER, key)
        if insertion_point is not None:
            locations[key] = SubElementLocation(False, insertion_point, insertion_point, _INDENT_HEADER_CHILD)

    data.encoding = _read_encoding(_direct_child(header_el, "encodingDesc"))
    data.profile = _read_profile(_direct_child(header_el, "profileDesc"))
    data.revisions = _read_revisions(_direct_child(header_el, "revisionDesc"))

    return HeaderReadResult(
        data=data,
        locations=locations,
        header_exists=True,
        file_desc_exists=file_desc_exists,
        well_formed=True,
        extra_xml=extra_xml,
    )
