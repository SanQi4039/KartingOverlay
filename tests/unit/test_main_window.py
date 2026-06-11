from PySide6.QtWidgets import QApplication, QSplitter, QTabWidget

from kart_overlay.ui.main_window import create_main_window


def test_main_window_keeps_left_project_panel_and_removes_standalone_status_column():
    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    splitter = window.centralWidget()

    assert isinstance(splitter, QSplitter)
    assert splitter.count() == 2
    assert isinstance(splitter.widget(1), QTabWidget)
    app.quit()
