from PySide6.QtWidgets import QApplication

from kart_overlay.ui.export_dialog import ExportDialog


def test_export_dialog_lists_transparent_export_formats_with_size_notes():
    app = QApplication.instance() or QApplication([])
    dialog = ExportDialog()

    assert dialog.windowTitle()
    assert dialog.format_combo.count() == 2
    assert "MOV ProRes 4444" in dialog.format_combo.currentText()
    assert "透明" in dialog.format_combo.currentText()
    assert "约" in dialog.format_combo.currentText()
    assert dialog.fps_input.text() == "60"
    assert dialog.button_box.button(dialog.button_box.StandardButton.Ok).text() != "OK"
    assert dialog.button_box.button(dialog.button_box.StandardButton.Cancel).text() != "Cancel"

    app.quit()
