from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
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
from kart_overlay.application.export_formats import (
    available_export_formats,
    estimate_export_bitrate_mbps,
    estimate_export_size_bytes,
    export_format_by_key,
    format_option_label,
    format_size,
)
from kart_overlay.application.export_service import ExportService
from kart_overlay.application.export_task_runner import BackgroundExportTaskRunner
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.application.video_metadata_service import VideoMetadataService
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.ui.export_options import FpsComboBox
from kart_overlay.ui.texts import app_text
from kart_overlay.widgets.widget_factory import build_widgets_from_session


@dataclass(frozen=True)
class ExportWidgetScaleInfo:
    original_canvas: tuple[int, int]
    target_canvas: tuple[int, int]
    scale_x: float
    scale_y: float
    visual_scale: float

    def manifest_fields(self) -> dict[str, float | int]:
        return {
            "widget_original_canvas_width": self.original_canvas[0],
            "widget_original_canvas_height": self.original_canvas[1],
            "widget_target_canvas_width": self.target_canvas[0],
            "widget_target_canvas_height": self.target_canvas[1],
            "widget_scale_x": self.scale_x,
            "widget_scale_y": self.scale_y,
            "widget_visual_scale": self.visual_scale,
        }


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
        self._active_encoder_label: str = ""

        self.video_path_input = QLineEdit()
        self.output_dir_input = QLineEdit()
        self.output_filename_input = QLineEdit("overlay")
        self.fps_input = FpsComboBox()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItem("原始视频尺寸", "original")
        self.resolution_combo.addItem("1080p", "1080p")
        self.resolution_combo.addItem("720p", "720p")
        self.format_combo = QComboBox()
        self.format_info_label = QLabel()
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
            self.format_info_label,
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
        form.addRow(app_text("overlay_resolution"), self.resolution_combo)
        form.addRow(app_text("export_format"), self.format_combo)
        form.addRow("", self.format_info_label)

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
        self.fps_input.currentIndexChanged.connect(self._handle_export_option_changed)
        self.resolution_combo.currentIndexChanged.connect(self._handle_export_option_changed)
        self.format_combo.currentIndexChanged.connect(self._handle_export_option_changed)

        self._refresh_tools_status()
        self._refresh_format_options()
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
        self.fps_input.set_source_fps(metadata.fps, selected_value=f"{metadata.fps:.6f}")
        vfr_suffix = " | 可变帧率风险" if metadata.is_variable_frame_rate else ""
        self.video_info_label.setText(
            f"视频：{metadata.width}x{metadata.height}，旋转 {metadata.rotation_deg} 度，"
            f"画布 {canvas_width}x{canvas_height}，{metadata.fps:.3f} fps，"
            f"{metadata.duration_sec:.3f} 秒{vfr_suffix}"
        )
        self._push_export_settings()
        self._refresh_format_options()

    def _handle_session_widget_layouts_changed(self, widget_layouts) -> None:
        return

    def _handle_session_export_settings_changed(self, export_settings: dict[str, str]) -> None:
        self.output_dir_input.setText(export_settings.get("output_dir", ""))
        self.output_filename_input.setText(export_settings.get("output_filename", "overlay"))
        self.fps_input.setText(export_settings.get("fps", "60"))
        mode = export_settings.get("overlay_resolution_mode", "original")
        index = self.resolution_combo.findData(mode)
        self.resolution_combo.setCurrentIndex(max(index, 0))
        export_format = export_settings.get("format", "mov_prores_4444")
        format_index = self.format_combo.findData(export_format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)
        self._refresh_format_options(selected_key=export_format)

    def _handle_export_option_changed(self) -> None:
        self._refresh_format_options()
        self._push_export_settings()

    def _push_export_settings(self) -> None:
        self._session.set_export_settings(
            {
                "output_dir": self.output_dir_input.text().strip(),
                "output_filename": self.output_filename_input.text().strip() or "overlay",
                "fps": self.fps_input.text().strip() or "60",
                "overlay_resolution_mode": self.resolution_combo.currentData() or "original",
                "range_mode": "full_telemetry",
                "format": self.format_combo.currentData() or "mov_prores_4444",
            }
        )

    def _refresh_format_options(self, *, selected_key: str | None = None) -> None:
        selected = selected_key or self.format_combo.currentData() or "mov_prores_4444"
        canvas_size = self._safe_canvas_size_for_estimate()
        fps = self._safe_fps_for_estimate()
        duration_sec = self._safe_duration_for_estimate()

        self.format_combo.blockSignals(True)
        self.format_combo.clear()
        for spec in available_export_formats():
            self.format_combo.addItem(
                format_option_label(spec, canvas_size=canvas_size, fps=fps, duration_sec=duration_sec),
                spec.key,
            )
        index = self.format_combo.findData(selected)
        self.format_combo.setCurrentIndex(max(index, 0))
        self.format_combo.blockSignals(False)
        self._update_format_info_label(canvas_size=canvas_size, fps=fps, duration_sec=duration_sec)

    def _update_format_info_label(
        self,
        *,
        canvas_size: tuple[int, int],
        fps: float,
        duration_sec: float,
    ) -> None:
        spec = export_format_by_key(self.format_combo.currentData())
        estimated_size = estimate_export_size_bytes(
            export_format_key=spec.key,
            canvas_size=canvas_size,
            fps=fps,
            duration_sec=duration_sec,
        )
        estimated_bitrate = estimate_export_bitrate_mbps(
            export_format_key=spec.key,
            canvas_size=canvas_size,
            fps=fps,
        )
        self.format_info_label.setText(
            f"{spec.description}；当前估算约 {format_size(estimated_size)}，"
            f"{estimated_bitrate:.1f} Mbps（按 {canvas_size[0]}x{canvas_size[1]}、{fps:.1f}fps、{duration_sec:.1f}s）"
        )

    def _safe_canvas_size_for_estimate(self) -> tuple[int, int]:
        if self._video_metadata is None:
            return (1280, 720)
        mode = str(self.resolution_combo.currentData() or "original")
        try:
            return self._resolve_canvas_size(mode)
        except ValueError:
            width, height = self._video_metadata.canvas_size
            return int(width), int(height)

    def _safe_fps_for_estimate(self) -> float:
        try:
            return float(self.fps_input.text().strip() or "60")
        except ValueError:
            return 60.0

    def _safe_duration_for_estimate(self) -> float:
        if self._telemetry is not None:
            return max(float(self._telemetry.duration_sec), 1.0)
        if self._video_metadata is not None:
            return max(float(self._video_metadata.duration_sec), 1.0)
        return 60.0

    def _browse_output_directory(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            app_text("select_output_directory"),
            self.output_dir_input.text().strip() or ".",
        )
        if selected_dir:
            self.output_dir_input.setText(selected_dir)
            self._push_export_settings()

    def _build_export_widgets(self, *, canvas_size: tuple[int, int] | None = None) -> list[object]:
        widgets = build_widgets_from_session(self._session)
        if canvas_size is None:
            return widgets
        scale_info = self._export_widget_scale_info(canvas_size)
        if scale_info.scale_x == 1.0 and scale_info.scale_y == 1.0:
            return widgets
        for widget in widgets:
            self._scale_export_widget_geometry(widget, scale_info)
        return widgets

    @staticmethod
    def _freeze_export_widgets(widgets: list[object]) -> list[object]:
        return deepcopy(widgets)

    def _export_widget_scale_info(self, canvas_size: tuple[int, int]) -> ExportWidgetScaleInfo:
        target_width = int(canvas_size[0])
        target_height = int(canvas_size[1])
        if self._video_metadata is None:
            original_width, original_height = target_width, target_height
        else:
            original_width, original_height = self._video_metadata.canvas_size
            original_width = int(original_width)
            original_height = int(original_height)

        if original_width <= 0 or original_height <= 0:
            return ExportWidgetScaleInfo(
                original_canvas=(original_width, original_height),
                target_canvas=(target_width, target_height),
                scale_x=1.0,
                scale_y=1.0,
                visual_scale=1.0,
            )

        scale_x = target_width / original_width
        scale_y = target_height / original_height
        return ExportWidgetScaleInfo(
            original_canvas=(original_width, original_height),
            target_canvas=(target_width, target_height),
            scale_x=scale_x,
            scale_y=scale_y,
            visual_scale=min(scale_x, scale_y),
        )

    @staticmethod
    def _scale_export_widget_geometry(widget: object, scale_info: ExportWidgetScaleInfo) -> None:
        for name, scale in (
            ("x", scale_info.scale_x),
            ("y", scale_info.scale_y),
            ("width", scale_info.scale_x),
            ("height", scale_info.scale_y),
        ):
            value = getattr(widget, name, None)
            if value is None:
                continue
            scaled = int(round(float(value) * scale))
            if name in {"width", "height"}:
                scaled = max(1, scaled)
            setattr(widget, name, scaled)
        setattr(widget, "visual_scale", max(0.01, float(scale_info.visual_scale)))

    def _set_export_running(self, running: bool) -> None:
        self.export_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.read_video_button.setEnabled(not running)
        self.output_dir_browse_button.setEnabled(not running)
        self.output_dir_input.setEnabled(not running)
        self.output_filename_input.setEnabled(not running)
        self.fps_input.setEnabled(not running)
        self.resolution_combo.setEnabled(not running)
        self.format_combo.setEnabled(not running)

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
        widgets = self._build_export_widgets(canvas_size=canvas_size)
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
            fps = float(self.fps_input.text().strip() or "60")
            resolution_mode = self.resolution_combo.currentData() or "original"
            canvas_size = self._resolve_canvas_size(str(resolution_mode))
            export_format = self.format_combo.currentData() or "mov_prores_4444"
            format_spec = export_format_by_key(str(export_format))
            output_filename = self._normalized_output_filename(
                self.output_filename_input.text(),
                extension=format_spec.extension,
            )
            widget_scale_info = self._export_widget_scale_info(canvas_size)
            self._push_export_settings()
            widgets, duration_sec = self._build_preflight(
                fps=fps,
                canvas_size=canvas_size,
            )
            export_widgets = self._freeze_export_widgets(widgets)
            output_path = output_dir / output_filename
            estimated_size = estimate_export_size_bytes(
                export_format_key=format_spec.key,
                canvas_size=canvas_size,
                fps=fps,
                duration_sec=duration_sec,
            )
            estimated_bitrate = estimate_export_bitrate_mbps(
                export_format_key=format_spec.key,
                canvas_size=canvas_size,
                fps=fps,
            )
            prepared = self._export_service.prepare_export(
                telemetry=self._telemetry,
                widgets=export_widgets,
                canvas_size=canvas_size,
                fps=fps,
                duration_sec=duration_sec,
                start_data_time_sec=0.0,
                output_path=output_path,
                export_format=format_spec.key,
            )
            self._active_encoder_label = prepared.encoder_label
            self.preflight_label.setText(
                f"{self.preflight_label.text()} | 编码器：{prepared.encoder_label}"
            )
            self._active_output_path = output_path
            request = ExportTaskRequest(
                telemetry=self._telemetry,
                widgets=export_widgets,
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
                    "source_video_width": None if self._video_metadata is None else self._video_metadata.canvas_size[0],
                    "source_video_height": None if self._video_metadata is None else self._video_metadata.canvas_size[1],
                    "overlay_width": canvas_size[0],
                    "overlay_height": canvas_size[1],
                    "overlay_resolution_mode": resolution_mode,
                    **widget_scale_info.manifest_fields(),
                    "fps": fps,
                    "export_range_mode": "full_telemetry",
                    "export_format": format_spec.key,
                    "export_format_label": format_spec.label,
                    "export_format_description": format_spec.description,
                    "estimated_output_size_bytes": estimated_size,
                    "estimated_output_bitrate_mbps": estimated_bitrate,
                    "alpha": True,
                },
                export_format=format_spec.key,
            )
        except (FileNotFoundError, ValueError) as exc:
            self.status_label.setText(f"导出失败：{self._localize_export_error(str(exc))}")
            return
        except Exception as exc:
            self.status_label.setText(f"导出失败：{exc}")
            return

        self.log_output.clear()
        self.progress_bar.setValue(0)
        if self._active_encoder_label:
            self.status_label.setText(f"正在导出 | 编码器：{self._active_encoder_label}")
        else:
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
        encoder_label = result.encoder_label or self._active_encoder_label
        if encoder_label:
            self.status_label.setText(f"导出完成：{output_path} | 编码器：{encoder_label}")
        else:
            self.status_label.setText(f"导出完成：{output_path}")

    def _handle_export_failed(self, message: str, log_path: Path) -> None:
        self._set_export_running(False)
        self._load_log_preview(log_path)
        self.status_label.setText(f"导出失败：{self._localize_export_error(message)}")

    def _handle_export_cancelled(self, message: str, log_path: Path) -> None:
        self._set_export_running(False)
        self.progress_bar.setValue(0)
        self._load_log_preview(log_path)
        self._active_output_path = None
        self._active_encoder_label = ""
        self.status_label.setText(message)

    def _load_log_preview(self, log_path: Path) -> None:
        if not log_path.exists():
            return
        self.log_output.setPlainText(log_path.read_text(encoding="utf-8"))

    @staticmethod
    def _normalized_output_filename(filename: str, *, extension: str = ".mov") -> str:
        text = filename.strip() or "overlay"
        suffix = extension if extension.startswith(".") else f".{extension}"
        path = Path(text)
        if path.suffix.lower() == suffix.lower():
            return path.name
        if path.suffix:
            return f"{path.stem}{suffix}"
        return f"{path.name}{suffix}"

    def _resolve_canvas_size(self, mode: str) -> tuple[int, int]:
        if self._video_metadata is None:
            raise ValueError("请先读取视频信息以确定 Overlay 分辨率")
        source_width, source_height = self._video_metadata.canvas_size
        if mode == "original":
            return int(source_width), int(source_height)
        if mode == "1080p":
            return _scaled_canvas_size(source_width, source_height, long_edge=1920)
        if mode == "720p":
            return _scaled_canvas_size(source_width, source_height, long_edge=1280)
        raise ValueError(f"不支持的 Overlay 分辨率：{mode}")

    @staticmethod
    def _localize_export_error(message: str) -> str:
        replacements = {
            "ffmpeg not found": "未找到 ffmpeg",
        }
        return replacements.get(message, message)


def _scaled_canvas_size(source_width: int, source_height: int, *, long_edge: int) -> tuple[int, int]:
    width = max(int(source_width), 1)
    height = max(int(source_height), 1)
    if width >= height:
        scaled_width = long_edge
        scaled_height = round(long_edge * height / width)
    else:
        scaled_height = long_edge
        scaled_width = round(long_edge * width / height)
    if scaled_width % 2:
        scaled_width += 1
    if scaled_height % 2:
        scaled_height += 1
    return max(2, scaled_width), max(2, scaled_height)
