import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app
