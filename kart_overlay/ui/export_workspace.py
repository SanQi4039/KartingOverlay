from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from kart_overlay.application.export_events import ExportTaskRequest
from kart_overlay.application.export_service import ExportService
from kart_overlay.application.export_task_runner import BackgroundExportTaskRunner
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.application.video_metadata_service import VideoMetadataService
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.ui.texts import app_text
from kart_overlay.widgets.widget_factory import build_widgets_from_session


class ExportWorkspace(QWidget):
    def __init__(
        self,
        *,
        export_service: ExportService | None = None,
        video_metadata_service: VideoMetadataService | None = None,
        export_task_runner=None,
        session: ProjectSession | None = None,
    ) -> None:
        super().__init__()
        self._export_service = export_service or ExportService()
        self._video_metadata_service = video_metadata_service or VideoMetadataService()
        self._export_task_runner = export_task_runner or BackgroundExportTaskRunner(export_service=self._export_service)
        self._session = session or ProjectSession()
        self._telemetry: TelemetryStore | None = None
        self._telemetry_source_path: str = ""
        self._video_metadata = None
        self._active_output_path: Path | None = None

        self.video_path_input = QLineEdit()
        self.output_dir_input = QLineEdit()
        self.output_filename_input = QLineEdit("overlay")
        self.fps_input = QLineEdit("60")
        self.canvas_width_input = QLineEdit("1280")
        self.canvas_height_input = QLineEdit("720")
        self.output_dir_browse_button = QPushButton(app_text("browse_output_directory"))
        self.video_info_label = QLabel(app_text("video_info_not_loaded"))
        self.tools_label = QLabel()
        self.preflight_label = QLabel(app_text("preflight_waiting"))
        self.status_label = QLabel(app_text("status_ready"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.read_video_button = QPushButton(app_text("read_video_info"))
        self.read_video_button.clicked.connect(self.read_video_metadata)
        self.export_button = QPushButton(app_text("export_mov"))
        self.export_button.clicked.connect(self.start_export)
        self.cancel_button = QPushButton(app_text("cancel_export"))
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_export)
        self.output_dir_browse_button.clicked.connect(self._browse_output_directory)

        for label in (
            self.video_info_label,
            self.tools_label,
            self.preflight_label,
            self.status_label,
        ):
            label.setWordWrap(True)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        output_dir_row = QHBoxLayout()
        output_dir_row.addWidget(self.output_dir_input)
        output_dir_row.addWidget(self.output_dir_browse_button)

        form = QFormLayout()
        form.addRow(app_text("video_file"), self.video_path_input)
        form.addRow(app_text("output_directory"), output_dir_row)
        form.addRow(app_text("output_filename"), self.output_filename_input)
        form.addRow(app_text("fps"), self.fps_input)
        form.addRow(app_text("canvas_width"), self.canvas_width_input)
        form.addRow(app_text("canvas_height"), self.canvas_height_input)

        actions = QHBoxLayout()
        actions.addWidget(self.read_video_button)
        actions.addWidget(self.export_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.tools_label)
        layout.addWidget(self.video_info_label)
        layout.addWidget(self.preflight_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_output)
        layout.addStretch(1)

        self.output_dir_input.editingFinished.connect(self._push_export_settings)
        self.output_filename_input.editingFinished.connect(self._push_export_settings)
        self.fps_input.editingFinished.connect(self._push_export_settings)
        self.canvas_width_input.editingFinished.connect(self._push_export_settings)
        self.canvas_height_input.editingFinished.connect(self._push_export_settings)

        self._refresh_tools_status()
        self._bind_session()
        self._handle_session_export_settings_changed(self._session.export_settings)

    def load_telemetry(self, telemetry: TelemetryStore, *, source_path: str | Path | None = None) -> None:
        self._apply_loaded_telemetry(telemetry, source_path=source_path)
        self._session.set_telemetry(telemetry, source_path=source_path)

    def _apply_loaded_telemetry(
        self,
        telemetry: TelemetryStore,
        *,
        source_path: str | Path | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._telemetry_source_path = str(source_path or "")

    def read_video_metadata(self) -> None:
        video_path = self.video_path_input.text().strip()
        if not video_path:
            self.status_label.setText("未选择视频文件")
            return

        try:
            metadata = self._video_metadata_service.inspect(video_path)
        except FileNotFoundError as exc:
            self.status_label.setText(f"视频信息读取失败：{exc}")
            self._refresh_tools_status()
            return
        except Exception as exc:
            self.status_label.setText(f"视频信息读取失败：{exc}")
            return

        self._session.set_video_path(video_path)
        self._apply_video_metadata(metadata)
        self._session.set_video_metadata(metadata)
        self.status_label.setText("视频信息已读取")

    def _refresh_tools_status(self) -> None:
        status = self._video_metadata_service.runtime_status()
        ffmpeg_state = (
            app_text("tools_status_ffmpeg_ready")
            if status["ffmpeg_available"]
            else app_text("tools_status_ffmpeg_missing")
        )
        ffprobe_state = (
            app_text("tools_status_ffprobe_ready")
            if status["ffprobe_available"]
            else app_text("tools_status_ffprobe_missing")
        )
        self.tools_label.setText(
            f"{ffmpeg_state}：{status['ffmpeg_path']} | "
            f"{ffprobe_state}：{status['ffprobe_path']}"
        )

    def _bind_session(self) -> None:
        self._session.telemetry_changed.connect(self._handle_session_telemetry_changed)
        self._session.video_path_changed.connect(self._handle_session_video_path_changed)
        self._session.video_metadata_changed.connect(self._handle_session_video_metadata_changed)
        self._session.widget_layouts_changed.connect(self._handle_session_widget_layouts_changed)
        self._session.export_settings_changed.connect(self._handle_session_export_settings_changed)

    def _handle_session_telemetry_changed(self, telemetry, source_path) -> None:
        if telemetry is self._telemetry and str(source_path or "") == self._telemetry_source_path:
            return
        self._apply_loaded_telemetry(telemetry, source_path=source_path)

    def _handle_session_video_path_changed(self, video_path: str) -> None:
        if self.video_path_input.text().strip() == video_path:
            return
        self.video_path_input.setText(video_path)

    def _handle_session_video_metadata_changed(self, metadata) -> None:
        self._apply_video_metadata(metadata)

    def _apply_video_metadata(self, metadata) -> None:
        self._video_metadata = metadata
        canvas_width, canvas_height = metadata.canvas_size
        self.fps_input.setText(f"{metadata.fps:.6f}")
        self.canvas_width_input.setText(str(canvas_width))
        self.canvas_height_input.setText(str(canvas_height))
        vfr_suffix = " | 可变帧率风险" if metadata.is_variable_frame_rate else ""
        self.video_info_label.setText(
            f"视频：{metadata.width}x{metadata.height}，旋转 {metadata.rotation_deg} 度，"
            f"画布 {canvas_width}x{canvas_height}，{metadata.fps:.3f} fps，"
            f"{metadata.duration_sec:.3f} 秒{vfr_suffix}"
        )
        self._push_export_settings()

    def _handle_session_widget_layouts_changed(self, widget_layouts) -> None:
        return

    def _handle_session_export_settings_changed(self, export_settings: dict[str, str]) -> None:
        self.output_dir_input.setText(export_settings.get("output_dir", ""))
        self.output_filename_input.setText(export_settings.get("output_filename", "overlay"))
        self.fps_input.setText(export_settings.get("fps", "60"))
        self.canvas_width_input.setText(export_settings.get("canvas_width", "1280"))
        self.canvas_height_input.setText(export_settings.get("canvas_height", "720"))

    def _push_export_settings(self) -> None:
        self._session.set_export_settings(
            {
                "output_dir": self.output_dir_input.text().strip(),
                "output_filename": self.output_filename_input.text().strip() or "overlay",
                "fps": self.fps_input.text().strip() or "60",
                "canvas_width": self.canvas_width_input.text().strip() or "1280",
                "canvas_height": self.canvas_height_input.text().strip() or "720",
                "range_mode": "full_telemetry",
                "format": "mov_prores_4444",
            }
        )

    def _browse_output_directory(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            app_text("select_output_directory"),
            self.output_dir_input.text().strip() or ".",
        )
        if selected_dir:
            self.output_dir_input.setText(selected_dir)
            self._push_export_settings()

    def _build_export_widgets(self) -> list[object]:
        return build_widgets_from_session(self._session)

    def _set_export_running(self, running: bool) -> None:
        self.export_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.read_video_button.setEnabled(not running)
        self.output_dir_browse_button.setEnabled(not running)
        self.output_dir_input.setEnabled(not running)
        self.output_filename_input.setEnabled(not running)
        self.fps_input.setEnabled(not running)
        self.canvas_width_input.setEnabled(not running)
        self.canvas_height_input.setEnabled(not running)

    def _build_preflight(
        self,
        *,
        fps: float,
        canvas_size: tuple[int, int],
    ) -> tuple[list[object], float]:
        if self._telemetry is None:
            raise ValueError("未导入遥测数据")
        if fps <= 0:
            raise ValueError("帧率必须大于 0")
        if canvas_size[0] <= 0 or canvas_size[1] <= 0:
            raise ValueError("画布尺寸必须大于 0")
        widgets = self._build_export_widgets()
        if not widgets:
            raise ValueError("没有可导出的已启用组件")

        self.preflight_label.setText(
            f"预检：完整遥测区间，数据 0.000 秒，时长 {self._telemetry.duration_sec:.3f} 秒"
        )
        return widgets, self._telemetry.duration_sec

    def start_export(self) -> None:
        if self._telemetry is None:
            self.status_label.setText("未导入遥测数据")
            return

        tools_status = self._video_metadata_service.runtime_status()
        if not tools_status["ffmpeg_available"]:
            self.status_label.setText(
                "导出失败：未找到 ffmpeg，请设置 KART_OVERLAY_FFMPEG_PATH 或将 ffmpeg 加入 PATH。"
            )
            self._refresh_tools_status()
            return

        try:
            output_dir = Path(self.output_dir_input.text().strip() or ".")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filename = self._normalized_output_filename(self.output_filename_input.text())
            fps = float(self.fps_input.text().strip() or "60")
            canvas_size = (
                int(self.canvas_width_input.text().strip() or "1280"),
                int(self.canvas_height_input.text().strip() or "720"),
            )
            self._push_export_settings()
            widgets, duration_sec = self._build_preflight(
                fps=fps,
                canvas_size=canvas_size,
            )
            output_path = output_dir / output_filename
            self._active_output_path = output_path
            request = ExportTaskRequest(
                telemetry=self._telemetry,
                widgets=widgets,
                canvas_size=canvas_size,
                fps=fps,
                duration_sec=duration_sec,
                start_data_time_sec=0.0,
                output_path=output_path,
                manifest_path=output_dir / "export_manifest.json",
                log_path=output_dir / "export.log",
                manifest_payload={
                    "project_name": "kart_overlay_project",
                    "video_file": self.video_path_input.text().strip(),
                    "data_file": self._telemetry_source_path,
                    "overlay_start_video_time_sec": 0.0,
                    "data_start_time_sec": 0.0,
                    "data_duration_sec": duration_sec,
                    "canvas_width": canvas_size[0],
                    "canvas_height": canvas_size[1],
                    "fps": fps,
                    "export_range_mode": "full_telemetry",
                    "export_format": "mov_prores_4444",
                    "alpha": True,
                },
            )
        except (FileNotFoundError, ValueError) as exc:
            self.status_label.setText(f"导出失败：{self._localize_export_error(str(exc))}")
            return
        except Exception as exc:
            self.status_label.setText(f"导出失败：{exc}")
            return

        self.log_output.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("正在导出")
        self._set_export_running(True)
        self._export_task_runner.start(
            request,
            on_progress=self._handle_export_progress,
            on_finished=self._handle_export_finished,
            on_failed=self._handle_export_failed,
            on_cancelled=self._handle_export_cancelled,
        )

    def cancel_export(self) -> None:
        self._export_task_runner.cancel()
        self.status_label.setText("正在取消导出...")

    def _handle_export_progress(self, progress_event) -> None:
        self.progress_bar.setValue(progress_event.percent)
        self.status_label.setText(progress_event.message)

    def _handle_export_finished(self, result) -> None:
        self.progress_bar.setValue(100)
        self._set_export_running(False)
        self._load_log_preview(result.log_path)
        output_path = self._active_output_path or result.manifest_path.parent / "overlay.mov"
        self.status_label.setText(f"导出完成：{output_path}")

    def _handle_export_failed(self, message: str, log_path: Path) -> None:
        self._set_export_running(False)
        self._load_log_preview(log_path)
        self.status_label.setText(f"导出失败：{self._localize_export_error(message)}")

    def _handle_export_cancelled(self, message: str, log_path: Path) -> None:
        self._set_export_running(False)
        self._load_log_preview(log_path)
        self.status_label.setText(message)

    def _load_log_preview(self, log_path: Path) -> None:
        if not log_path.exists():
            return
        self.log_output.setPlainText(log_path.read_text(encoding="utf-8"))

    @staticmethod
    def _normalized_output_filename(filename: str) -> str:
        text = filename.strip() or "overlay"
        path = Path(text)
        if path.suffix.lower() == ".mov":
            return path.name
        if path.suffix:
            return f"{path.stem}.mov"
        return f"{path.name}.mov"

    @staticmethod
    def _localize_export_error(message: str) -> str:
        replacements = {
            "ffmpeg not found": "未找到 ffmpeg",
        }
        return replacements.get(message, message)
