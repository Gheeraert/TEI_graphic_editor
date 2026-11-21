"""Fabrique de widgets Qt par type d'attribut, pour l'inspecteur
d'attributs typé de la phase 5 (`docs/ROADMAP.md` §5.7). Séparée du
dock (`editor/inspector_panel.py`) pour rester testable sans assembler
toute la fenêtre.

Une entrée d'attribut (telle que renvoyée par
``tei_editor.tei.catalog.attributes_of``) porte ``closed_values``,
``datatype``, ``gloss``, ``desc`` : c'est ce dictionnaire, pas une
liste codée en dur, qui pilote le choix du widget (`CLAUDE.md`).
"""

from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLineEdit

#: Petite liste statique de langues courantes pour ``teidata.language``
#: (``xml:lang``) — **pas** une tentative de couvrir tout BCP 47 (hors
#: périmètre de cette phase, `docs/ROADMAP.md` §5.7, qui ne demande
#: qu'« une petite liste statique raisonnable »). La saisie libre reste
#: toujours possible : le ``QComboBox`` est éditable.
COMMON_LANGUAGES = ["fr", "en", "la", "grc", "de", "es", "it"]

#: Attributs dont la valeur attendue est typiquement une référence
#: interne (``#id``), proposée avec complétion sur les ``xml:id`` du
#: document courant (`docs/ROADMAP.md` §5.7) — même liste que celle
#: utilisée par le contrôle des références croisées
#: (`editor/diagnostics.py`).
POINTER_LIKE_ATTRIBUTES = frozenset({"ref", "target", "corresp", "wit", "resp", "who", "facs"})

#: Motifs de date/heure acceptés pour un attribut temporel
#: (``teidata.temporal.*``/``teidata.xTemporal.*``) : validation simple
#: par expression régulière, pas un widget calendrier (`docs/ROADMAP.md`
#: §5.7, qui demande explicitement « pas un widget calendrier complexe »).
_TEMPORAL_PATTERNS = [
    re.compile(r"^\d{4}$"),  # YYYY
    re.compile(r"^\d{4}-\d{2}$"),  # YYYY-MM
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # YYYY-MM-DD
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$"),  # YYYY-MM-DDThh:mm[:ss]
]

_INVALID_STYLE = "background-color: #fdecea; border: 1px solid #c0392b;"


def is_temporal_datatype(datatype: str | None) -> bool:
    return bool(datatype) and "temporal" in datatype


def is_valid_temporal_value(value: str) -> bool:
    """Une valeur vide est considérée valide (champ pas encore rempli) :
    seule une valeur non vide qui ne correspond à aucun motif connu est
    signalée."""
    if not value:
        return True
    return any(pattern.match(value) for pattern in _TEMPORAL_PATTERNS)


class TemporalLineEdit(QLineEdit):
    """``QLineEdit`` qui signale visuellement (fond rouge pâle,
    info-bulle) une valeur qui ne correspond à aucun motif de date/heure
    reconnu — retour simple, pas un widget calendrier."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.textChanged.connect(self._revalidate)
        self._revalidate(self.text())

    def _revalidate(self, text: str) -> None:
        if is_valid_temporal_value(text):
            self.setStyleSheet("")
            self.setToolTip("")
        else:
            self.setStyleSheet(_INVALID_STYLE)
            self.setToolTip(
                "Format de date non reconnu (attendu par ex. YYYY, "
                "YYYY-MM-DD ou YYYY-MM-DDThh:mm:ss)."
            )


def make_closed_values_combo(closed_values: list[dict], current_value: str = "") -> QComboBox:
    """``QComboBox`` pour un attribut à valeurs fermées : une entrée par
    valeur du catalogue, info-bulle avec sa glose/description."""
    combo = QComboBox()
    combo.setEditable(False)
    for entry in closed_values:
        ident = entry.get("ident", "")
        combo.addItem(ident)
        tooltip = entry.get("gloss") or entry.get("desc") or ""
        if tooltip:
            combo.setItemData(combo.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole)
    index = combo.findText(current_value)
    if index >= 0:
        combo.setCurrentIndex(index)
    elif current_value:
        combo.insertItem(0, current_value)
        combo.setCurrentIndex(0)
    return combo


def make_language_combo(current_value: str = "") -> QComboBox:
    """``QComboBox`` éditable pour ``xml:lang`` : langues courantes +
    saisie libre."""
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(COMMON_LANGUAGES)
    if current_value and combo.findText(current_value) < 0:
        combo.addItem(current_value)
    combo.setCurrentText(current_value)
    return combo


def make_pointer_combo(document_xml_ids: list[str], current_value: str = "") -> QComboBox:
    """``QComboBox`` éditable pour un attribut de type référence interne
    (``@ref``, ``@target``...) : complétion sur les ``xml:id`` du
    document courant (préfixés ``#``), saisie libre acceptée pour une
    URI externe."""
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(sorted(f"#{xml_id}" for xml_id in document_xml_ids))
    if current_value and combo.findText(current_value) < 0:
        combo.addItem(current_value)
    combo.setCurrentText(current_value)
    return combo


def make_temporal_line_edit(current_value: str = "") -> TemporalLineEdit:
    line_edit = TemporalLineEdit()
    line_edit.setText(current_value)
    return line_edit


def make_plain_line_edit(current_value: str = "") -> QLineEdit:
    line_edit = QLineEdit()
    line_edit.setText(current_value)
    return line_edit


def make_editor_for_attribute(attribute: dict, *, current_value: str = "", document_xml_ids: list[str] | None = None):
    """Choisit et construit le widget Qt adapté à ``attribute`` (entrée
    du catalogue, voir ``tei_editor.tei.catalog.attributes_of``) :

    - ``closed_values`` non vide -> ``QComboBox`` fermé.
    - ``teidata.language`` (``xml:lang``) -> ``QComboBox`` éditable,
      langues courantes + saisie libre.
    - identifiant parmi :data:`POINTER_LIKE_ATTRIBUTES` et
      ``teidata.pointer`` -> ``QComboBox`` éditable, complétion sur les
      ``xml:id`` du document.
    - ``teidata.temporal.*``/``teidata.xTemporal.*`` -> ``QLineEdit``
      avec validation visuelle simple.
    - sinon -> ``QLineEdit`` simple.
    """
    closed_values = attribute.get("closed_values") or []
    datatype = attribute.get("datatype")
    ident = attribute.get("ident", "")
    local_ident = ident.rsplit(":", 1)[-1]

    if closed_values:
        return make_closed_values_combo(closed_values, current_value)
    if datatype == "teidata.language" or local_ident == "lang":
        return make_language_combo(current_value)
    if ident in POINTER_LIKE_ATTRIBUTES or (datatype == "teidata.pointer" and ident in POINTER_LIKE_ATTRIBUTES):
        return make_pointer_combo(document_xml_ids or [], current_value)
    if datatype == "teidata.pointer":
        # Un pointeur hors de la petite liste connue : toujours une
        # saisie libre, mais avec la même complétion utile (ADR-0007 :
        # suggérer de façon permissive).
        return make_pointer_combo(document_xml_ids or [], current_value)
    if is_temporal_datatype(datatype):
        return make_temporal_line_edit(current_value)
    return make_plain_line_edit(current_value)
