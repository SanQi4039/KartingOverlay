from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.ui.texts import app_text


class WorkflowStatusPanel(QWidget):
    def __init__(self, *, session: ProjectSession | None = None) -> None:
        super().__init__()
        self._session = session or ProjectSession()

        layout = QFormLayout(self)
        self.telemetry_value = QLabel(app_text("workflow_status_not_loaded"))
        self.video_value = QLabel(app_text("workflow_status_not_loaded"))

        layout.addRow(app_text("workflow_status_telemetry"), self.telemetry_value)
        layout.addRow(app_text("workflow_status_video"), self.video_value)

        self._session.telemetry_changed.connect(self._handle_telemetry_changed)
        self._session.video_metadata_changed.connect(self._handle_video_metadata_changed)

    def _handle_telemetry_changed(self, telemetry, source_path) -> None:
        source_name = source_path or "当前会话"
        self.telemetry_value.setText(f"{telemetry.sample_count} 个采样点 | {source_name}")

    def _handle_video_metadata_changed(self, metadata) -> None:
        self.video_value.setText(
            f"{metadata.width}x{metadata.height} | {metadata.fps:.3f} fps"
        )
