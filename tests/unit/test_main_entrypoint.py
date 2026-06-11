from PySide6.QtWidgets import QApplication

from kart_overlay.main import build_runtime
from kart_overlay.ui.texts import app_text


def test_build_runtime_creates_application_and_window():
    runtime = build_runtime([])

    assert isinstance(runtime.application, QApplication)
    assert runtime.window.windowTitle() == app_text("window_title")

    runtime.application.quit()
