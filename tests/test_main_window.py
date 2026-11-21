from PySide6.QtWidgets import QApplication

from tei_editor.main_window import MainWindow


def test_main_window_opens_empty(qapp: QApplication) -> None:
    window = MainWindow()
    assert window.windowTitle() == "Éditeur TEI"
    window.close()
