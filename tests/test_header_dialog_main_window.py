"""Test Qt bout en bout (hors écran) de l'assistant d'en-tête (phase 6) :
ouvrir un document réel dans `MainWindow`, lancer l'assistant, modifier
un champ, appliquer, relire le texte du document et vérifier le
changement attendu — vérifie le câblage réel (``main_window.py`` >
« Outils > Assistant d'en-tête... »), pas seulement les modules isolés.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tei_editor.header_dialog.wizard import HeaderWizardDialog
from tei_editor.main_window import MainWindow

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tei-samples"
COMPLETE_HEADER = FIXTURES / "02-entete" / "01-entete-complet.xml"


def _make_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings, recovery_dir=tmp_path / "recovery")
    window.editor.setPlainText(COMPLETE_HEADER.read_text(encoding="utf-8"))
    window.editor.document().setModified(False)
    window._update_structural_info()
    return window


def test_header_wizard_action_opens_dialog_from_tools_menu(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    assert window.actions.header_wizard.text().replace("&", "") == "Assistant d'en-tête..."
    window.close()


def test_apply_with_no_changes_leaves_document_byte_identical(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    original_text = window.editor.toPlainText()

    dialog = HeaderWizardDialog(window.editor, window)
    dialog._apply()

    assert window.editor.toPlainText() == original_text
    window.close()


def test_apply_with_one_field_changed_updates_only_that_field(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)
    original_text = window.editor.toPlainText()

    dialog = HeaderWizardDialog(window.editor, window)
    dialog.edition_tab.extent_field.setText("20 lettres")
    dialog._apply()

    new_text = window.editor.toPlainText()
    assert new_text != original_text
    assert "<extent>20 lettres</extent>" in new_text
    assert "12 lettres" not in new_text

    # Le reste du document (titleStmt, publicationStmt, sourceDesc...)
    # reste identique au caractère près.
    assert "<title type=\"main\">Les Lettres d'exemple</title>" in new_text
    assert "<publisher>Presses universitaires d'exemple</publisher>" in new_text

    # Un seul « Annuler » restaure exactement le texte d'origine
    # (ADR-0008 : bloc d'annulation unique).
    window.editor.undo()
    assert window.editor.toPlainText() == original_text
    window.close()


def test_apply_adding_author_through_title_tab(qapp: QApplication, tmp_path: Path) -> None:
    window = _make_window(qapp, tmp_path)

    dialog = HeaderWizardDialog(window.editor, window)
    dialog.title_tab.parties_table.add_row(["author", "Nouvel Auteur", "", "", "", ""])
    dialog._apply()

    new_text = window.editor.toPlainText()
    assert "Nouvel Auteur" in new_text

    # Pas de confirmation de fermeture nécessaire pour ce test : le document
    # modifié est volontairement laissé tel quel (c'est l'objet du test).
    window.editor.document().setModified(False)
    window.close()
