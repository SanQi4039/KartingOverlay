import importlib

import pytest
from PySide6.QtWidgets import QApplication

from kart_overlay.ui.track_editor import TrackEditor


def test_track_editor_rejects_removed_sync_pick_mode():
    app = QApplication.instance() or QApplication([])
    editor = TrackEditor()

    with pytest.raises(ValueError):
        editor.set_edit_mode("sync_pick")

    app.quit()


def test_removed_sync_modules_are_no_longer_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("kart_overlay.domain.sync.models")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("kart_overlay.application.sync_service")
