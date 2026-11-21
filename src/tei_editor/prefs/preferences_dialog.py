"""Boîte de dialogue « Préférences » : thème, dossier des derniers
fichiers (affichage), autosave (activation/intervalle).

Lit et écrit directement via les fonctions de :mod:`tei_editor.prefs.settings`
(un ``QSettings`` est passé par l'appelant, pour rester testable avec un
``QSettings`` de test — ``QSettings.Format.IniFormat`` sur un fichier
temporaire plutôt que le registre/les fichiers système réels).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from tei_editor.prefs import settings as prefs


class PreferencesDialog(QDialog):
    def __init__(self, settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        self._settings = settings

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(list(prefs.THEME_CHOICES))
        self._theme_combo.setCurrentText(prefs.get_theme(settings))

        recent_files = prefs.cleaned_recent_files(settings)
        last_directory = str(recent_files[0]) if recent_files else "(aucun fichier récent)"
        self._recent_directory_label = QLabel(last_directory)

        self._autosave_checkbox = QCheckBox("Activer l'enregistrement automatique")
        self._autosave_checkbox.setChecked(prefs.get_autosave_enabled(settings))

        self._autosave_interval_spin = QSpinBox()
        self._autosave_interval_spin.setRange(5, 3600)
        self._autosave_interval_spin.setSuffix(" s")
        self._autosave_interval_spin.setValue(prefs.get_autosave_interval_seconds(settings))

        form = QFormLayout()
        form.addRow("Thème :", self._theme_combo)
        form.addRow("Dernier fichier ouvert :", self._recent_directory_label)
        form.addRow(self._autosave_checkbox)
        form.addRow("Intervalle d'autosave :", self._autosave_interval_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def selected_theme(self) -> str:
        return self._theme_combo.currentText()

    def _save_and_accept(self) -> None:
        prefs.set_theme(self._settings, self._theme_combo.currentText())
        prefs.set_autosave_enabled(self._settings, self._autosave_checkbox.isChecked())
        prefs.set_autosave_interval_seconds(self._settings, self._autosave_interval_spin.value())
        self.accept()
