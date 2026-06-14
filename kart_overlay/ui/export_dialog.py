from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from kart_overlay.application.export_formats import available_export_formats, format_option_label
from kart_overlay.ui.export_options import FpsComboBox
from kart_overlay.ui.texts import app_text


class ExportDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_text("export_dialog_title"))

        self.format_combo = QComboBox()
        for spec in available_export_formats():
            self.format_combo.addItem(
                format_option_label(spec, canvas_size=(1280, 720), fps=50.0, duration_sec=25 * 60),
                spec.key,
            )

        self.fps_input = FpsComboBox()
        self.output_path_input = QLineEdit()

        form = QFormLayout()
        form.addRow(app_text("export_format"), self.format_combo)
        form.addRow(app_text("fps"), self.fps_input)
        form.addRow(app_text("output_path"), self.output_path_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(app_text("dialog_ok"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(app_text("dialog_cancel"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.button_box)
