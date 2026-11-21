"""Modèle de données de l'assistant d'en-tête TEI (phase 6,
``docs/ROADMAP.md`` §5).

Ces dataclasses représentent ce que l'assistant *gère explicitement* dans
un ``<teiHeader>`` : elles ne prétendent pas couvrir toute la richesse de
l'en-tête TEI (voir ``docs/AUDIT_MINI_METOPES.md`` pour l'inspiration
retenue — modèle multi-responsables typés par rôle, inspiré de
``Contributor``/``Affiliation`` de mini-metopes mais adapté au vocabulaire
TEI natif, pas copié). Tout le reste d'un ``<teiHeader>`` existant
(``seriesStmt``, ``notesStmt``, ``classDecl``...) est préservé tel quel
par :mod:`tei_editor.tei.header_reader`/``header_writer`` sans jamais
passer par ce modèle (c'est le cœur de l'exigence de non-perte de cette
phase, pas une limite de ce module).

Choix délibérément simples, conformes à la consigne de cette phase :
``sourceDesc`` reste un ``bibl`` texte libre ou un ``msDesc`` minimal (pas
de structuration poussée) ; ``encodingDesc``/``profileDesc`` utilisent des
champs texte libre plutôt qu'une structuration fine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

#: Rôle TEI porté par un responsable de ``titleStmt``. ``"respStmt"``
#: désigne un responsable générique dont le libellé de responsabilité
#: (``<resp>``) est un texte libre, pas limité aux rôles ``author``/
#: ``editor``/``funder`` (``docs/ROADMAP.md`` §5, phase 6 : « respStmt
#: générique avec un libellé de resp libre »).
ResponsiblePartyRole = Literal["author", "editor", "funder", "respStmt"]

SourceDescMode = Literal["bibl", "msDesc"]


@dataclass
class TitleEntry:
    """Un ``<title>`` de ``titleStmt`` (``type`` libre : ``"main"``,
    ``"sub"``... ou ``None`` pour un titre sans ``@type``)."""

    text: str = ""
    type: str | None = None


@dataclass
class ResponsibleParty:
    """Un responsable de ``titleStmt`` : un ``<author>``/``<editor>``/
    ``<funder>`` (``role in {"author", "editor", "funder"}``) ou un
    ``<respStmt>`` générique (``role == "respStmt"``, avec
    ``resp_label`` libre pour le texte de ``<resp>``)."""

    role: ResponsiblePartyRole = "author"
    name: str = ""
    resp_label: str | None = None
    role_attribute: str | None = None  # ex. @role sur <editor role="scientifique">
    orcid: str | None = None
    affiliation: str | None = None


@dataclass
class EditionStatement:
    """``editionStmt`` : une mention d'édition texte libre, avec un
    numéro d'édition optionnel (``@n`` de ``<edition>``)."""

    text: str = ""
    n: str | None = None


@dataclass
class IdentifierEntry:
    """Un ``<idno>`` de ``publicationStmt`` (``type`` libre : ``"URI"``,
    ``"ISBN"``...)."""

    type: str | None = None
    value: str = ""


@dataclass
class PublicationStatement:
    """``publicationStmt`` : éditeur, lieu, date, identifiants, licence.

    La licence réutilise :mod:`tei_editor.tei.licenses` (déjà extrait en
    phase 2) : ``license_spdx_id`` prioritaire si reconnu, sinon
    ``license_name``/``license_url`` en texte libre (même principe que
    :func:`tei_editor.tei.licenses.resolve_license`).
    """

    publisher: str = ""
    pub_place: str = ""
    date_when: str = ""
    date_text: str = ""
    identifiers: list[IdentifierEntry] = field(default_factory=list)
    availability_status: str | None = None
    license_spdx_id: str | None = None
    license_name: str | None = None
    license_url: str | None = None
    rights_statement: str = ""


@dataclass
class SourceDescription:
    """``sourceDesc`` : soit un ``bibl`` texte libre, soit un ``msDesc``
    minimal (identifiant de manuscrit + résumé physique texte libre). Un
    ``msDesc`` complet est hors de portée de cette phase
    (``docs/ROADMAP.md`` §5)."""

    mode: SourceDescMode = "bibl"
    bibl_text: str = ""
    msdesc_repository: str = ""
    msdesc_idno: str = ""
    msdesc_summary: str = ""


@dataclass
class EncodingDescription:
    """``encodingDesc`` : champs texte libre, pas de structure fine
    (``docs/ROADMAP.md`` §5 : « des champs texte libre suffisent »)."""

    project_desc: str = ""
    editorial_decl: str = ""
    tags_decl: str = ""


@dataclass
class LanguageUsage:
    """Une ``<language>`` de ``profileDesc/langUsage``."""

    ident: str = ""
    name: str = ""
    usage_percent: str | None = None


@dataclass
class ProfileDescription:
    """``profileDesc`` : langue(s), mots-clés, résumé, participants.
    Champs texte libre pour mots-clés/résumé/participants, conformément à
    la consigne de cette phase."""

    languages: list[LanguageUsage] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    abstract: str = ""
    participants: str = ""


@dataclass
class ChangeEntry:
    """Un ``<change>`` de ``revisionDesc``."""

    when: str = ""
    who: str = ""
    description: str = ""


@dataclass
class RevisionDescription:
    """``revisionDesc`` : statut optionnel + liste de ``<change>``."""

    status: str | None = None
    changes: list[ChangeEntry] = field(default_factory=list)


@dataclass
class TeiHeaderData:
    """Agrégat de tout ce que l'assistant d'en-tête gère explicitement.

    Ne contient *pas* les parties non gérées d'un ``<teiHeader>`` existant
    (``seriesStmt``, ``notesStmt``...) : celles-ci sont repérées comme
    « zones non gérées » par :mod:`tei_editor.tei.header_reader` et jamais
    construites ici (préservation par omission, voir ce module)."""

    titles: list[TitleEntry] = field(default_factory=list)
    responsible_parties: list[ResponsibleParty] = field(default_factory=list)
    edition: EditionStatement = field(default_factory=EditionStatement)
    extent: str = ""
    publication: PublicationStatement = field(default_factory=PublicationStatement)
    source: SourceDescription = field(default_factory=SourceDescription)
    encoding: EncodingDescription = field(default_factory=EncodingDescription)
    profile: ProfileDescription = field(default_factory=ProfileDescription)
    revisions: RevisionDescription = field(default_factory=RevisionDescription)
