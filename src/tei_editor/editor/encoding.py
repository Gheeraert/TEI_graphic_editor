"""Détection d'encodage et de fin de ligne pour un round-trip octet à octet.

``QPlainTextEdit``/``QTextDocument`` normalisent toute fin de ligne en
``"\\n"`` interne (ADR-0006). Pour réécrire des octets strictement
identiques à l'original (critère d'acceptation de la phase 3, voir
``docs/ROADMAP.md`` §5), ce module isole deux informations qu'il faut
retenir entre l'ouverture et l'enregistrement : l'encodage effectif
(avec son éventuel BOM) et la convention de fin de ligne du fichier
d'origine, pour les réappliquer tels quels à l'écriture.

Limite assumée (voir ``docs/DECISIONS.md``) : la déclaration
``encoding="..."`` dans le prologue XML n'est détectée que si elle est
elle-même en octets ASCII-compatibles (le cas de tous les encodages
usuels d'un document TEI : UTF-8, latin-1...). Un fichier UTF-16 *sans*
BOM n'est pas détecté par inspection du prologue (il faudrait déjà
connaître l'encodage pour le décoder) : seul UTF-16 BOM plus présent est
reconnu de façon fiable. En l'absence de BOM et de déclaration
reconnaissable, l'encodage par défaut est UTF-8, conformément à
``docs/ROADMAP.md`` §3.A3.1 (TEI impose UTF-8 par défaut).
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass

_BOM_UTF8 = codecs.BOM_UTF8
_BOM_UTF16_LE = codecs.BOM_UTF16_LE
_BOM_UTF16_BE = codecs.BOM_UTF16_BE

_DECLARED_ENCODING_RE = re.compile(
    rb"""<\?xml[^>]*\sencoding\s*=\s*["']([A-Za-z0-9._-]+)["']""",
)

DEFAULT_ENCODING = "utf-8"
DEFAULT_NEWLINE = "\n"


@dataclass(frozen=True, slots=True)
class DocumentEncoding:
    """Ce qu'il faut retenir d'un fichier pour le réécrire à l'identique."""

    name: str
    bom: bytes
    newline: str


def _declared_encoding(body: bytes) -> str | None:
    match = _DECLARED_ENCODING_RE.search(body[:512])
    if not match:
        return None
    candidate = match.group(1).decode("ascii", errors="ignore").lower()
    try:
        codecs.lookup(candidate)
    except LookupError:
        return None
    return candidate


def _detect_newline(body: bytes) -> str:
    crlf = body.count(b"\r\n")
    lf_only = body.count(b"\n") - crlf
    cr_only = body.count(b"\r") - crlf
    counts = {"\r\n": crlf, "\n": lf_only, "\r": cr_only}
    newline = max(counts, key=counts.get)
    return newline if counts[newline] > 0 else DEFAULT_NEWLINE


def detect_encoding(data: bytes) -> DocumentEncoding:
    """Détecte l'encodage effectif et la fin de ligne de ``data``.

    Ne décode rien : renvoie seulement ce qu'il faut pour le faire
    (voir :func:`decode_document`) et pour réécrire des octets
    identiques (voir :func:`encode_document`).
    """
    if data.startswith(_BOM_UTF8):
        return DocumentEncoding("utf-8", _BOM_UTF8, _detect_newline(data[len(_BOM_UTF8):]))
    if data.startswith(_BOM_UTF16_LE):
        return DocumentEncoding(
            "utf-16-le", _BOM_UTF16_LE, _detect_newline(data[len(_BOM_UTF16_LE):])
        )
    if data.startswith(_BOM_UTF16_BE):
        return DocumentEncoding(
            "utf-16-be", _BOM_UTF16_BE, _detect_newline(data[len(_BOM_UTF16_BE):])
        )
    name = _declared_encoding(data) or DEFAULT_ENCODING
    return DocumentEncoding(name, b"", _detect_newline(data))


def decode_document(data: bytes) -> tuple[str, DocumentEncoding]:
    """Détecte l'encodage de ``data`` et renvoie ``(texte, encodage)``.

    Le texte renvoyé normalise toute fin de ligne en ``"\\n"`` (la
    convention interne de ``QTextDocument``, que l'éditeur voit de toute
    façon une fois le texte chargé dans un ``QPlainTextEdit``) : ce
    module reste ainsi testable et cohérent indépendamment de Qt. La fin
    de ligne d'origine, retenue dans ``encoding.newline``, est réappliquée
    par :func:`encode_document`.
    """
    encoding = detect_encoding(data)
    body = data[len(encoding.bom):]
    text = body.decode(encoding.name)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text, encoding


def encode_document(text: str, encoding: DocumentEncoding) -> bytes:
    """Réencode ``text`` (fins de ligne ``"\\n"``, convention Qt) selon
    ``encoding`` : réapplique le BOM et la fin de ligne d'origine.
    """
    if encoding.newline != "\n":
        text = text.replace("\n", encoding.newline)
    return encoding.bom + text.encode(encoding.name)
