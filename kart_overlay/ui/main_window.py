from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QTabWidget,
)

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.export_workspace import ExportWorkspace
from kart_overlay.ui.track_workspace import TrackWorkspace
from kart_overlay.ui.canvas_workspace import CanvasWorkspace
from kart_overlay.ui.project_panel import ProjectPanel
from kart_overlay.ui.texts import app_text


def create_main_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle(app_text("window_title"))
    window.resize(1440, 900)
    session = ProjectSession()
    window._project_session = session

    splitter = QSplitter()
    tabs = QTabWidget()
    tabs.addTab(TrackWorkspace(session=session), app_text("tab_track"))
    tabs.addTab(CanvasWorkspace(session=session), app_text("tab_canvas"))
    tabs.addTab(ExportWorkspace(session=session), app_text("tab_export"))

    project_panel = ProjectPanel(session=session)
    project_panel.setMinimumWidth(220)

    splitter.addWidget(project_panel)
    splitter.addWidget(tabs)
    splitter.setHandleWidth(10)
    splitter.setChildrenCollapsible(False)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([260, 1540])
    window.setCentralWidget(splitter)
    return window
