"""Critère d'acceptation central de la phase 3 (``docs/ROADMAP.md`` §5) :
ouvrir un fichier TEI valide, ne rien modifier, l'enregistrer, et
retrouver des octets strictement identiques à l'original — pas de
normalisation de fin de ligne, pas de réindentation, pas de changement
d'encodage, pas d'ajout/suppression de BOM, pas de perte de commentaires/
PI, pas de réordonnancement d'attributs.

Même motif de chargement du corpus que ``tests/test_tei_samples_corpus.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from tei_editor.editor.encoding import decode_document, encode_document
from tei_editor.editor.text_editor import XmlTextEditor
from tei_editor.main_window import MainWindow

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "tei-samples"


def _load_manifest() -> dict:
    with (FIXTURES_DIR / "manifest.json").open(encoding="utf-8") as handle:
        return json.load(handle)


VALID_ENTRIES = [entry for entry in _load_manifest()["files"] if not entry.get("expect")]


@pytest.mark.parametrize("entry", VALID_ENTRIES, ids=lambda entry: entry["file"])
def test_editor_open_then_save_is_byte_identical(qapp: QApplication, entry: dict, tmp_path: Path) -> None:
    """Pipeline complet « éditeur » : ouvrir dans un ``XmlTextEditor``, ne
    rien modifier, enregistrer vers un autre chemin, comparer les octets."""
    source = FIXTURES_DIR / entry["file"]
    original_bytes = source.read_bytes()

    editor = XmlTextEditor()
    editor.load_file(source)
    assert editor.toPlainText() == decode_document(original_bytes)[0]

    destination = tmp_path / source.name
    editor.save_to(destination)

    assert destination.read_bytes() == original_bytes, entry["file"]


@pytest.mark.parametrize("entry", VALID_ENTRIES, ids=lambda entry: entry["file"])
def test_io_pipeline_open_then_save_is_byte_identical(entry: dict, tmp_path: Path) -> None:
    """Test complémentaire indépendant de l'interface : uniquement
    décodage -> réencodage -> écriture atomique, sans passer par un
    ``QPlainTextEdit``."""
    source = FIXTURES_DIR / entry["file"]
    original_bytes = source.read_bytes()

    text, encoding = decode_document(original_bytes)
    rebuilt_bytes = encode_document(text, encoding)

    assert rebuilt_bytes == original_bytes, entry["file"]


@pytest.mark.parametrize("entry", VALID_ENTRIES, ids=lambda entry: entry["file"])
def test_insert_then_delete_same_text_round_trips(
    qapp: QApplication, entry: dict, tmp_path: Path
) -> None:
    """Aller-retour de modification : insérer puis supprimer exactement le
    même texte redonne, après enregistrement, les octets d'origine."""
    source = FIXTURES_DIR / entry["file"]
    original_bytes = source.read_bytes()

    editor = XmlTextEditor()
    editor.load_file(source)

    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    inserted = "<!-- brouillon temporaire -->"
    cursor.insertText(inserted)
    for _ in range(len(inserted)):
        cursor.deletePreviousChar()
    editor.setTextCursor(cursor)

    destination = tmp_path / source.name
    editor.save_to(destination)

    assert destination.read_bytes() == original_bytes, entry["file"]


def test_main_window_open_then_save_is_byte_identical(qapp: QApplication, tmp_path: Path) -> None:
    """Vérifie le même critère en passant par la fenêtre principale
    (menus Fichier > Ouvrir / Enregistrer sous), pas seulement le widget nu."""
    source = FIXTURES_DIR / "01-structure" / "01-minimal.xml"
    original_bytes = source.read_bytes()

    settings_path = tmp_path / "settings.ini"
    from PySide6.QtCore import QSettings

    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    window._open_path(source)

    destination = tmp_path / "copie.xml"
    window._save_to_path(destination)
    window.close()

    assert destination.read_bytes() == original_bytes
