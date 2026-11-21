# Repris partiellement de C:\merope src/bloggen/markdown/typography.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30) : les
# fonctions `split_century_ordinals`/`_split_run_by_century` (ainsi que
# `CENTURY_RE`/`is_valid_century_ordinal`, qui n'existaient que pour les
# servir) sont volontairement laissées de côté, de même que l'import
# `from bloggen.markdown.rich_text_model import InlineRun` : elles
# produisent des fragments de texte en exposant superscript/normal sur le
# pivot `InlineRun` de Mérope, qui n'existe pas ici (ADR-0001). Toutes les
# autres fonctions sont du texte pur, sans dépendance à `bloggen` ni à un
# pivot objet, et sont reprises sans changement de comportement.
"""Typographie française à la frappe : espaces insécables, guillemets.

Conformément à `docs/ROADMAP.md` §4 et ADR-0001, ces transformations ne
doivent être appliquées qu'à l'intérieur des nœuds texte d'un document
TEI, jamais au texte XML dans son ensemble (balises, attributs)."""

from __future__ import annotations

import re

NBSP = " "
EN_DASH = "–"
EM_DASH = "—"
DOUBLE_PUNCTUATION = ";:!?"
CURLY_OPENING_QUOTE = "“"
CURLY_CLOSING_QUOTE = "”"
OPENING_GUILLEMET = "«"  # «
CLOSING_GUILLEMET = "»"  # »


def typed_dash_replacement(prefix: str) -> str | None:
    """Renvoie le remplacement, à la frappe, pour le suffixe de *prefix*.

    Deux tirets tapés deviennent un tiret demi-cadratin ; un troisième
    tiret suivant, voyant le suffixe ``–-`` déjà formé, le fait passer en
    tiret cadratin. Délibérément une aide à la frappe, pas une règle de
    normalisation générale du texte.
    """
    if prefix.endswith(f"{EN_DASH}-"):
        return EM_DASH
    if prefix.endswith("--"):
        return EN_DASH
    return None


def apply_french_typography(text: str) -> str:
    """Convertit les guillemets droits/courbes en guillemets français
    alternés (avec une espace insécable collée à l'intérieur), corrige
    l'espacement des guillemets déjà présents comme tels, assure une
    espace insécable unique avant ``; : ! ?``, et colle « p. »/« pp. » au
    numéro de page suivant avec une espace insécable. Idempotent : une
    double application n'ajoute pas d'espace supplémentaire et ne
    réinverse pas la parité des guillemets.
    """
    text = convert_curly_quotes_to_guillemets(text)
    text = _convert_straight_quotes(text)
    text = fix_guillemet_spacing(text)
    text = fix_double_punctuation_spacing(text)
    text = fix_page_number_spacing(text)
    return fix_period_spacing(text)


def convert_curly_quotes_to_guillemets(text: str) -> str:
    """Convertit directement les guillemets déjà courbes (p. ex. issus
    de la correction automatique de Word/Google Docs) en guillemets
    français. À la différence des guillemets droits, les guillemets
    courbes sont univoques (ouvrant/fermant encodé dans le caractère
    lui-même), donc aucun suivi de parité n'est nécessaire.
    """
    text = text.replace(CURLY_OPENING_QUOTE, OPENING_GUILLEMET + NBSP)
    return text.replace(CURLY_CLOSING_QUOTE, NBSP + CLOSING_GUILLEMET)


def convert_straight_quotes_stateful(text: str, *, opening_next: bool = True) -> tuple[str, bool]:
    """Même conversion que ci-dessus, mais fait transiter la parité
    ouvrant/fermant entre plusieurs appels au lieu de toujours repartir
    d'« ouvrant ». Nécessaire pour convertir un contenu collé fragment par
    fragment dans l'ordre du document, quand une paire de guillemets peut
    s'étendre sur plus d'un fragment.

    Renvoie ``(texte_converti, prochain_opening_next)``.
    """
    result: list[str] = []
    for char in text:
        if char == '"':
            if opening_next:
                result.append(OPENING_GUILLEMET + NBSP)
            else:
                result.append(NBSP + CLOSING_GUILLEMET)
            opening_next = not opening_next
        else:
            result.append(char)
    return "".join(result), opening_next


def _convert_straight_quotes(text: str) -> str:
    converted, _ = convert_straight_quotes_stateful(text, opening_next=True)
    return converted


def fix_guillemet_spacing(text: str) -> str:
    """Si des chevrons (« / ») sont déjà présents en tant que tels dans le
    texte importé, ils sont laissés exactement où ils sont (jamais
    réappariés, dupliqués ou réinterprétés). Ceci assure seulement qu'une
    espace ordinaire collée à l'intérieur en devienne une insécable.
    Idempotent : seule une espace ordinaire littérale est remplacée.
    """
    text = text.replace(f"{OPENING_GUILLEMET} ", f"{OPENING_GUILLEMET}{NBSP}")
    return text.replace(f" {CLOSING_GUILLEMET}", f"{NBSP}{CLOSING_GUILLEMET}")


def fix_double_punctuation_spacing(text: str) -> str:
    """Assure une espace insécable unique avant ``; : ! ?`` (en remplaçant
    une espace ordinaire précédente, ou en en insérant une si la
    ponctuation est collée au mot précédent). Idempotent.
    """
    result: list[str] = []
    for index, char in enumerate(text):
        if char in DOUBLE_PUNCTUATION:
            preceding = text[index - 1] if index > 0 else ""
            if preceding != NBSP:
                if result and result[-1] == " ":
                    result.pop()
                result.append(NBSP)
        result.append(char)
    return "".join(result)


SPACE_BEFORE_PERIOD_RE = re.compile(r"[  ]+\.")


def fix_period_spacing(text: str) -> str:
    """À la différence de ``; : ! ?``, la typographie française ne met
    jamais d'espace avant un point — supprime toute espace ordinaire ou
    insécable précédant directement un point. Idempotent.
    """
    return SPACE_BEFORE_PERIOD_RE.sub(".", text)


_LETTER_CLASS = "A-Za-zÀ-ÖØ-öø-ÿ"
PAGE_ABBREVIATION_RE = re.compile(rf"(?<![{_LETTER_CLASS}])(pp?\.)( |{NBSP})?")


def fix_page_number_spacing(text: str) -> str:
    """Assure une espace insécable unique après « p. »/« pp. » isolés, en
    en insérant une si aucune n'a été tapée. Idempotent.
    """
    return PAGE_ABBREVIATION_RE.sub(rf"\1{NBSP}", text)


OE_LIGATURE = "œ"
OE_LIGATURE_UPPER = "Œ"
OE_LIGATURE_WORDS = (
    "soeur",
    "oeuvre",
    "boeuf",
    "coeur",
    "noeud",
    "voeu",
    "moeurs",
    "oeil",
    "foetus",
    "oesophage",
    "oedeme",
    "manoeuvre",
    "oeuf",
    "choeur",
    "coeliaque",
    "oenologie",
    "oecumenique",
    "oestrogene",
)
_OE_PAIR_RE = re.compile("oe", re.IGNORECASE)


def oe_ligature_replacement(word: str) -> str:
    """Remplace le digramme « oe » dans *word* (correspondance
    insensible à la casse avec un mot de :data:`OE_LIGATURE_WORDS`) par
    la ligature française œ. Mis en majuscule en Œ quand le digramme
    ouvre le mot (début de mot en capitale, p. ex. « Oeuvre ») ou est
    lui-même entièrement en capitales (p. ex. « SOEUR ») ; en minuscule
    sinon.
    """
    match = _OE_PAIR_RE.search(word)
    if match is None:
        return word
    o_char, e_char = match.group()[0], match.group()[1]
    word_initial = match.start() == 0
    upper = o_char.isupper() and (word_initial or e_char.isupper())
    ligature = OE_LIGATURE_UPPER if upper else OE_LIGATURE
    return word[: match.start()] + ligature + word[match.end() :]


ACCENTED_CAPITAL_E_WORDS = frozenset(
    """
    ecart echec echelle eclat ecole ecoles ecoute ecouter ecran ecrans ecrire
    ecrit ecrits ecriture ecrivain ecrivains edifice edition editions editeur
    editeurs education egalement egalite eglise eglises elite elu emotion
    energie epoque epoques epreuve episode equipe equipes erudit etape etat
    etats etais etait etaient etant etoile etonnant etranger etrangers etre
    etude etudes etudiant etudiants
    """.split()
)


def accented_capital_e_applies(word: str) -> bool:
    """Vrai quand *word* commence par un « E » capital et que, son
    accent une fois restitué, il correspond à un mot de
    :data:`ACCENTED_CAPITAL_E_WORDS` (quelle que soit la casse).
    """
    return word[:1] == "E" and word.lower() in ACCENTED_CAPITAL_E_WORDS
