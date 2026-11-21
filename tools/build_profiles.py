"""Construction des profils de balisage (listes blanches) à partir du
catalogue TEI complet.

Un profil est une liste de groupes d'éléments destinés à une future palette
de balises dans l'interface graphique (voir ``docs/ROADMAP.md`` §3,
phase 7). Les regroupements ci-dessous reprennent la structure proposée en
``docs/ROADMAP.md`` §3.A2, filtrée contre le catalogue réellement généré
(un élément mentionné dans la roadmap mais absent du catalogue — faute de
frappe, élément renommé/déprécié dans la version TEI courante — est
silencieusement écarté, mais retracé dans ``missing`` pour inspection).

Quatre profils sont produits ici (le cinquième prévu par la roadmap,
``commons_publishing``, est hors périmètre de cette tâche et sera ajouté
avec le code repris de Mérope à la phase 2) :

- ``tei_all`` : la totalité du catalogue, groupée par module TEI — profil
  générique « tout voir ».
- ``edition_textes`` : profil d'édition de textes (phase 7, premier jeu de
  balises à livrer).
- ``theatre`` : profil pour les textes de théâtre.
- ``edition_critique`` : profil pour l'apparat critique (variantes,
  témoins).
"""

from __future__ import annotations

# Regroupements thématiques repris de docs/ROADMAP.md §3.A2 ("Ensemble de
# départ, à confronter au catalogue généré, qui fait foi").

HEADER_GROUPS = {
    "header_title": (
        "Titre et responsabilités",
        ["titleStmt", "title", "author", "editor", "respStmt", "resp", "name", "funder"],
    ),
    "header_edition": (
        "Édition",
        ["editionStmt", "edition", "extent"],
    ),
    "header_publication": (
        "Publication",
        [
            "publicationStmt",
            "publisher",
            "pubPlace",
            "date",
            "idno",
            "availability",
            "licence",
            "authority",
        ],
    ),
    "header_series_notes": (
        "Collection et notes",
        ["seriesStmt", "notesStmt", "note"],
    ),
    "header_source": (
        "Source",
        ["sourceDesc", "bibl", "biblStruct", "msDesc", "listWit"],
    ),
    "header_encoding": (
        "Déclarations d'encodage",
        [
            "encodingDesc",
            "projectDesc",
            "editorialDecl",
            "tagsDecl",
            "refsDecl",
            "classDecl",
            "charDecl",
            "appInfo",
        ],
    ),
    "header_profile": (
        "Profil du texte",
        [
            "profileDesc",
            "langUsage",
            "language",
            "creation",
            "textClass",
            "keywords",
            "abstract",
            "particDesc",
            "correspDesc",
        ],
    ),
    "header_revision": (
        "Révisions",
        ["revisionDesc", "change", "listChange"],
    ),
    "header_root": (
        "Squelette",
        ["TEI", "teiCorpus", "teiHeader", "fileDesc"],
    ),
}

STRUCTURE_GROUP = (
    "structure",
    "Structure du texte",
    [
        "text",
        "front",
        "body",
        "back",
        "group",
        "floatingText",
        "div",
        "head",
        "byline",
        "dateline",
        "salute",
        "signed",
        "opener",
        "closer",
        "epigraph",
        "argument",
        "titlePage",
        "docTitle",
        "titlePart",
        "docAuthor",
        "docImprint",
        "docDate",
        "p",
        "ab",
        "lg",
        "l",
        "seg",
        "lb",
        "pb",
        "cb",
        "milestone",
        "anchor",
    ],
)

PHRASE_GROUP = (
    "phrase",
    "Niveau phrastique",
    [
        "hi",
        "emph",
        "foreign",
        "mentioned",
        "soCalled",
        "q",
        "quote",
        "cit",
        "said",
        "title",
        "term",
        "gloss",
        "distinct",
        "date",
        "time",
        "num",
        "measure",
        "name",
        "persName",
        "placeName",
        "orgName",
        "geogName",
        "rs",
        "ref",
        "ptr",
        "note",
        "bibl",
        "idno",
    ],
)

TRANSCRIPTION_GROUP = (
    "transcription",
    "Édition de textes et transcription",
    [
        "abbr",
        "expan",
        "am",
        "ex",
        "choice",
        "sic",
        "corr",
        "orig",
        "reg",
        "unclear",
        "gap",
        "supplied",
        "add",
        "del",
        "subst",
        "damage",
        "restore",
        "space",
        "handShift",
    ],
)

APPARATUS_GROUP = (
    "apparatus",
    "Apparat critique",
    ["app", "lem", "rdg", "rdgGrp", "wit", "witDetail", "listWit", "witness", "listApp"],
)

THEATRE_GROUP = (
    "theatre",
    "Théâtre",
    [
        "sp",
        "speaker",
        "stage",
        "castList",
        "castItem",
        "role",
        "roleDesc",
        "set",
        "performance",
    ],
)

LISTS_GROUP = (
    "lists",
    "Listes, tableaux, images",
    [
        "list",
        "item",
        "label",
        "table",
        "row",
        "cell",
        "figure",
        "figDesc",
        "graphic",
        "facsimile",
        "surface",
        "zone",
    ],
)

ENTITIES_GROUP = (
    "entities",
    "Indices et entités",
    [
        "listPerson",
        "person",
        "listPlace",
        "place",
        "listOrg",
        "org",
        "listBibl",
        "link",
        "linkGrp",
        "join",
    ],
)


def _filter_group(group_id: str, label: str, idents: list[str], all_idents: set[str]):
    present = [i for i in idents if i in all_idents]
    missing = [i for i in idents if i not in all_idents]
    return {"id": group_id, "label": label, "elements": sorted(set(present))}, missing


def _build_groups(specs: list[tuple[str, str, list[str]]], all_idents: set[str]):
    groups = []
    all_missing: list[str] = []
    for group_id, label, idents in specs:
        group, missing = _filter_group(group_id, label, idents, all_idents)
        if group["elements"]:
            groups.append(group)
        all_missing.extend(missing)
    return groups, all_missing


def _header_group_specs() -> list[tuple[str, str, list[str]]]:
    return [(gid, label, idents) for gid, (label, idents) in HEADER_GROUPS.items()]


def build_tei_all(all_idents: set[str]) -> dict:
    """Profil générique : tout le catalogue, groupé par ordre alphabétique.

    Ce profil n'utilise pas les regroupements thématiques (il expose
    littéralement tout) ; un seul groupe « Tous les éléments » suffit pour
    une palette qui sera, de toute façon, filtrée/recherchée par l'UI.
    """

    return {
        "id": "tei_all",
        "label": "TEI (complet)",
        "description": (
            "Tous les éléments du catalogue TEI P5 généré, sans filtrage. "
            "Profil générique destiné à l'exploration complète du jeu de "
            "balises, pas à un usage éditorial quotidien."
        ),
        "groups": [
            {
                "id": "all",
                "label": "Tous les éléments",
                "elements": sorted(all_idents),
            }
        ],
    }


def build_edition_textes(all_idents: set[str]) -> tuple[dict, list[str]]:
    specs = (
        _header_group_specs()
        + [STRUCTURE_GROUP, PHRASE_GROUP, TRANSCRIPTION_GROUP, LISTS_GROUP, ENTITIES_GROUP]
        + [APPARATUS_GROUP]
    )
    groups, missing = _build_groups(specs, all_idents)
    profile = {
        "id": "edition_textes",
        "label": "Édition de textes",
        "description": (
            "Profil pour l'édition savante de textes en prose ou en vers : "
            "structure, normalisation (choice/orig/reg, sic/corr, "
            "abbr/expan), lacunes et restitutions, entités nommées, et un "
            "apparat critique de base."
        ),
        "groups": groups,
    }
    return profile, missing


def build_theatre(all_idents: set[str]) -> tuple[dict, list[str]]:
    specs = (
        _header_group_specs()
        + [STRUCTURE_GROUP, THEATRE_GROUP, PHRASE_GROUP, TRANSCRIPTION_GROUP, ENTITIES_GROUP]
    )
    groups, missing = _build_groups(specs, all_idents)
    profile = {
        "id": "theatre",
        "label": "Théâtre",
        "description": (
            "Profil pour les textes dramatiques : répliques, didascalies, "
            "distribution, vers partagés (@part sur l et lg), en plus de la "
            "structure et du niveau phrastique communs."
        ),
        "groups": groups,
    }
    return profile, missing


def build_edition_critique(all_idents: set[str]) -> tuple[dict, list[str]]:
    specs = (
        _header_group_specs()
        + [STRUCTURE_GROUP, PHRASE_GROUP, TRANSCRIPTION_GROUP, APPARATUS_GROUP, ENTITIES_GROUP]
    )
    groups, missing = _build_groups(specs, all_idents)
    profile = {
        "id": "edition_critique",
        "label": "Édition critique",
        "description": (
            "Profil centré sur l'apparat critique : variantes (app/lem/rdg/"
            "rdgGrp), témoins (wit/witDetail/listWit/witness/listApp), en "
            "plus de la structure, du niveau phrastique et de la "
            "transcription communs à une édition savante."
        ),
        "groups": groups,
    }
    return profile, missing


def build_all_profiles(all_idents: set[str]) -> list[dict]:
    """Construit les quatre profils et affiche les éventuels éléments de la
    roadmap absents du catalogue généré (diagnostic de dérive, pas une
    erreur bloquante : le catalogue généré fait foi, pas la liste indicative
    de docs/ROADMAP.md §3.A2)."""

    profiles = [build_tei_all(all_idents)]
    for builder in (build_edition_textes, build_theatre, build_edition_critique):
        profile, missing = builder(all_idents)
        if missing:
            print(
                f"[profil {profile['id']}] éléments de la roadmap absents du "
                f"catalogue (ignorés) : {sorted(set(missing))}"
            )
        profiles.append(profile)
    return profiles
