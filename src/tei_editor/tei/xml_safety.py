# Repris de C:\merope src/bloggen/tei/xml_safety.py
# (commit 3006514eeaea43a21189a19a46713ad981984d0a, 2026-10-30), adapté :
# fonction `parse_xml_safely_for_elementtree` (spécifique à header_builder,
# non repris) supprimée ; aucun autre changement de comportement.
"""Frontière de parsing XML durci pour le TEI manipulé par cet éditeur.

Analyse avec accès réseau, chargement de DTD et résolution d'entités tous
désactivés, puis rejette tout document qui déclare un DOCTYPE (DTD ou
non) : le TEI édité ici n'a jamais besoin de DOCTYPE, de sous-ensemble
DTD externe/interne ni d'entité personnalisée.
"""

from __future__ import annotations

from lxml import etree


class UnsafeXmlError(ValueError):
    """Levée quand le XML TEI échoue à la politique de parsing durci :
    XML mal formé, ou document déclarant un DOCTYPE (refusé dans tous
    les cas, DTD ou non).
    """


def _safe_xml_parser() -> etree.XMLParser:
    # Un analyseur neuf par appel, pas une instance partagée au niveau
    # module : un XMLParser porte un état d'erreur mutable par document,
    # et rien ici n'est assez sollicité pour justifier d'amortir son coût
    # de construction.
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        recover=False,
        huge_tree=False,
        # Les commentaires et instructions de traitement sont conservés
        # (contrairement à xml.etree.ElementTree.fromstring, qui les
        # supprime silencieusement) : la fidélité du contenu mixte
        # l'exige (ADR-0001).
        remove_comments=False,
        remove_pis=False,
    )


def parse_xml_safely(xml: str | bytes) -> etree._Element:
    """Analyse ``xml`` selon la politique durcie et renvoie la racine lxml.

    Lève :class:`UnsafeXmlError` (une ``ValueError``) pour un XML mal
    formé ou un DOCTYPE refusé — ne laisse jamais une
    ``lxml.etree.XMLSyntaxError`` brute franchir cette frontière.
    """
    data = xml.encode("utf-8") if isinstance(xml, str) else xml
    try:
        root = etree.fromstring(data, parser=_safe_xml_parser())
    except etree.XMLSyntaxError as exc:
        raise UnsafeXmlError(f"XML TEI invalide (parse) : {exc}") from exc
    # load_dtd=False empêche seulement la *récupération* d'un sous-ensemble
    # externe ; une déclaration DOCTYPE elle-même (sous-ensemble interne,
    # déclarations d'entités, ou simple `<!DOCTYPE TEI>`) reste enregistrée
    # sur le document analysé et doit être vérifiée explicitement —
    # docinfo.doctype est une chaîne vide quand aucun DOCTYPE n'était présent.
    if root.getroottree().docinfo.doctype:
        raise UnsafeXmlError(
            "Les déclarations DOCTYPE/DTD ne sont pas autorisées dans ce document TEI."
        )
    return root
