from PySide6.QtWidgets import QApplication

from kart_overlay.ui.export_dialog import ExportDialog


def test_export_dialog_defaults_to_mov_prores_4444():
    app = QApplication.instance() or QApplication([])
    dialog = ExportDialog()

    assert dialog.windowTitle()
    assert dialog.format_combo.count() == 1
    assert "MOV ProRes 4444" in dialog.format_combo.currentText()
    assert dialog.fps_input.text() == "60"
    assert dialog.button_box.button(dialog.button_box.StandardButton.Ok).text() != "OK"
    assert dialog.button_box.button(dialog.button_box.StandardButton.Cancel).text() != "Cancel"

    app.quit()
