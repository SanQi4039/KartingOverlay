from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kart_overlay.app_paths import ensure_default_projects_dir
from kart_overlay.application.import_telemetry_service import TelemetryImportService
from kart_overlay.application.project_service import ProjectService
from kart_overlay.application.project_session import ProjectSession
from kart_overlay.application.video_metadata_service import VideoMetadataService
from kart_overlay.domain.project import ProjectDocument
from kart_overlay.domain.track.models import DisplayTransform, Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.texts import app_text


class ProjectPanel(QWidget):
    def __init__(
        self,
        *,
        session: ProjectSession | None = None,
        telemetry_import_service: TelemetryImportService | None = None,
        video_metadata_service: VideoMetadataService | None = None,
        project_service: ProjectService | None = None,
    ) -> None:
        super().__init__()
        self._session = session or ProjectSession()
        self._telemetry_import_service = telemetry_import_service or TelemetryImportService()
        self._video_metadata_service = video_metadata_service or VideoMetadataService()
        self._project_service = project_service or ProjectService()

        self.telemetry_path_input = QLineEdit()
        self.background_path_input = QLineEdit()
        self.video_path_input = QLineEdit()
        self.background_path_input.setReadOnly(True)
        self.telemetry_status_label = QLabel(app_text("telemetry_not_loaded"))
        self.background_status_label = QLabel(app_text("background_not_loaded"))
        self.video_status_label = QLabel(app_text("video_not_loaded"))
        self.project_status_label = QLabel(app_text("project_not_loaded"))
        self.telemetry_help_label = QLabel("遥测文件：提供速度、位置、圈速等数据，是组件显示和赛道分析的主要数据来源。")
        self.video_help_label = QLabel("视频文件：用于时间对齐，并在画布编辑页显示第一帧预览，方便判断组件大小和位置。")
        self.background_help_label = QLabel("背景图：用于赛道编辑中确定起终点和分段线位置；可以从视频或地图里自己截图后导入。")
        self.telemetry_import_progress = QProgressBar()
        self.video_import_progress = QProgressBar()
        for label in (
            self.telemetry_status_label,
            self.background_status_label,
            self.video_status_label,
            self.project_status_label,
            self.telemetry_help_label,
            self.video_help_label,
            self.background_help_label,
        ):
            label.setWordWrap(True)
        for progress_bar in (self.telemetry_import_progress, self.video_import_progress):
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setTextVisible(False)

        self.browse_telemetry_button = QPushButton(app_text("browse_telemetry"))
        self.browse_background_button = QPushButton(app_text("browse_background"))
        self.browse_video_button = QPushButton(app_text("browse_video"))
        self.save_project_button = QPushButton(app_text("save_project"))
        self.load_project_button = QPushButton(app_text("load_project"))

        self.browse_telemetry_button.clicked.connect(self._browse_telemetry)
        self.browse_background_button.clicked.connect(self._browse_background)
        self.browse_video_button.clicked.connect(self._browse_video)
        self.save_project_button.clicked.connect(self._save_project)
        self.load_project_button.clicked.connect(self._load_project)

        self.telemetry_section = self._build_file_section(
            title="遥测数据",
            file_label=app_text("telemetry_file"),
            path_input=self.telemetry_path_input,
            browse_button=self.browse_telemetry_button,
            status_label=self.telemetry_status_label,
            progress_bar=self.telemetry_import_progress,
            help_label=self.telemetry_help_label,
        )
        self.background_section = self._build_file_section(
            title="背景图",
            file_label="背景图文件",
            path_input=self.background_path_input,
            browse_button=self.browse_background_button,
            status_label=self.background_status_label,
            help_label=self.background_help_label,
        )
        self.video_section = self._build_file_section(
            title="视频",
            file_label=app_text("video_file"),
            path_input=self.video_path_input,
            browse_button=self.browse_video_button,
            status_label=self.video_status_label,
            progress_bar=self.video_import_progress,
            help_label=self.video_help_label,
        )
        self.project_section = self._build_project_section()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(app_text("project_workflow")))
        layout.addWidget(self.telemetry_section)
        layout.addWidget(self.background_section)
        layout.addWidget(self.video_section)
        layout.addWidget(self.project_section)
        layout.addStretch(1)

        self._session.video_path_changed.connect(self._handle_session_video_path_changed)
        self._session.background_image_path_changed.connect(self._handle_session_background_image_path_changed)

    def _build_file_section(
        self,
        *,
        title: str,
        file_label: str,
        path_input: QLineEdit,
        browse_button: QPushButton,
        status_label: QLabel,
        progress_bar: QProgressBar | None = None,
        help_label: QLabel | None = None,
    ) -> QWidget:
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 4, 0, 4)
        section_layout.setSpacing(6)
        section_layout.addWidget(QLabel(title))
        form = QFormLayout()
        form.addRow(file_label, path_input)
        section_layout.addLayout(form)
        section_layout.addWidget(browse_button)
        section_layout.addWidget(status_label)
        if progress_bar is not None:
            section_layout.addWidget(progress_bar)
        if help_label is not None:
            section_layout.addWidget(help_label)
        return section

    def _build_project_section(self) -> QWidget:
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 4, 0, 4)
        section_layout.setSpacing(6)
        section_layout.addWidget(QLabel("项目"))
        project_actions = QHBoxLayout()
        project_actions.addWidget(self.save_project_button)
        project_actions.addWidget(self.load_project_button)
        section_layout.addLayout(project_actions)
        section_layout.addWidget(self.project_status_label)
        return section

    def default_project_directory(self) -> str:
        return str(ensure_default_projects_dir())

    def import_telemetry(self) -> None:
        telemetry_path = self.telemetry_path_input.text().strip()
        if not telemetry_path:
            self.telemetry_status_label.setText("遥测：未选择文件")
            self.telemetry_import_progress.setValue(0)
            return

        self._begin_import_progress(self.telemetry_import_progress)
        try:
            telemetry = self._telemetry_import_service.import_file(telemetry_path)
        except Exception as exc:
            self.telemetry_status_label.setText(f"遥测导入失败：{exc}")
            self.telemetry_import_progress.setValue(0)
            return

        self._session.set_telemetry(telemetry, source_path=telemetry_path)
        self.telemetry_status_label.setText(
            f"遥测已导入：{Path(telemetry_path).name}（{telemetry.sample_count} 个采样点）"
        )
        self.telemetry_import_progress.setValue(100)

    def import_video(self) -> None:
        video_path = self.video_path_input.text().strip()
        if not video_path:
            self.video_status_label.setText("视频：未选择文件")
            self.video_import_progress.setValue(0)
            return

        self._begin_import_progress(self.video_import_progress)
        try:
            metadata = self._video_metadata_service.inspect(video_path)
        except Exception as exc:
            self.video_status_label.setText(f"视频导入失败：{exc}")
            self.video_import_progress.setValue(0)
            return

        self._session.set_video_path(video_path)
        self._session.set_video_metadata(metadata)
        self.video_status_label.setText(
            f"视频已导入：{Path(video_path).name}（{metadata.width}x{metadata.height}，{metadata.fps:.3f} fps）"
        )
        self.video_import_progress.setValue(100)

    def _browse_telemetry(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            app_text("select_telemetry_file"),
            self.default_project_directory(),
            app_text("telemetry_file_filter"),
        )
        if path:
            self.telemetry_path_input.setText(path)
            self.import_telemetry()

    def _browse_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            app_text("select_video_file"),
            self.default_project_directory(),
            app_text("video_file_filter"),
        )
        if path:
            self.video_path_input.setText(path)
            self.import_video()

    def _browse_background(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            app_text("select_background_file"),
            self.default_project_directory(),
            app_text("background_file_filter"),
        )
        if path:
            self.background_path_input.setText(path)
            self._session.set_background_image_path(path)
            self.background_status_label.setText(
                app_text("background_loaded").format(name=Path(path).name)
            )

    def _handle_session_video_path_changed(self, video_path: str) -> None:
        if self.video_path_input.text().strip() == video_path:
            return
        self.video_path_input.setText(video_path)

    def _handle_session_background_image_path_changed(self, image_path: str) -> None:
        self.background_path_input.setText(image_path)
        if image_path:
            self.background_status_label.setText(
                app_text("background_loaded").format(name=Path(image_path).name)
            )
            return
        self.background_status_label.setText(app_text("background_not_loaded"))

    @staticmethod
    def _begin_import_progress(progress_bar: QProgressBar) -> None:
        progress_bar.setValue(5)
        QApplication.processEvents()

    def save_project_to_path(self, project_path: str | Path) -> None:
        project_path = Path(project_path)
        document = ProjectDocument(
            schema_version="1.0",
            project_name=project_path.stem or "kart_overlay_project",
            video={
                "path": self._session.video_path,
                "metadata": _serialize_video_metadata(self._session.video_metadata),
            },
            telemetry={
                "path": self._session.telemetry_source_path,
            },
            track=_serialize_track_definition(
                self._session.track_definition,
                project_path=project_path,
                background_image_path=self._session.background_image_path,
            ),
            canvas={
                "widget_count": len(self._session.widget_layouts),
            },
            widgets=[
                {"name": name, **layout}
                for name, layout in sorted(self._session.widget_layouts.items())
            ],
            export={**self._session.export_settings},
        )
        self._project_service.save_project(project_path, document)
        self.project_status_label.setText(f"项目已保存：{project_path.name}")

    def load_project_from_path(self, project_path: str | Path) -> None:
        project_path = Path(project_path)
        document = self._project_service.load_project(project_path)

        telemetry_path = str(document.telemetry.get("path", ""))
        if telemetry_path:
            self.telemetry_path_input.setText(telemetry_path)
            telemetry = self._telemetry_import_service.import_file(telemetry_path)
            self._session.set_telemetry(telemetry, source_path=telemetry_path)
            self.telemetry_status_label.setText(
                f"遥测已导入：{Path(telemetry_path).name}（{telemetry.sample_count} 个采样点）"
            )
            self.telemetry_import_progress.setValue(100)

        video_path = str(document.video.get("path", ""))
        if video_path:
            self.video_path_input.setText(video_path)
            metadata = self._video_metadata_service.inspect(video_path)
            self._session.set_video_path(video_path)
            self._session.set_video_metadata(metadata)
            self.video_status_label.setText(
                f"视频已导入：{Path(video_path).name}（{metadata.width}x{metadata.height}，{metadata.fps:.3f} fps）"
            )
            self.video_import_progress.setValue(100)

        track_definition = _deserialize_track_definition(document.track, project_path=project_path)
        background_image_path = _resolve_project_path(
            str(document.track.get("background_image_path", "")),
            project_path=project_path,
        )
        if background_image_path:
            self._session.set_background_image_path(background_image_path)
        if track_definition is not None:
            self._session.set_track_definition(track_definition)

        widget_layouts: dict[str, dict[str, object]] = {}
        for widget_payload in document.widgets:
            if "name" not in widget_payload:
                continue
            layout: dict[str, object] = {
                "x": int(widget_payload.get("x", 0)),
                "y": int(widget_payload.get("y", 0)),
                "width": int(widget_payload.get("width", 0)) or None,
                "height": int(widget_payload.get("height", 0)) or None,
                "enabled": bool(widget_payload.get("enabled", True)),
            }
            if "background_opacity" in widget_payload:
                layout["background_opacity"] = int(widget_payload.get("background_opacity", 0))
            if "font_scale" in widget_payload:
                layout["font_scale"] = float(widget_payload.get("font_scale", 1.0))
            widget_layouts[str(widget_payload["name"])] = layout
        if widget_layouts:
            self._session.set_widget_layouts(widget_layouts)

        if document.export:
            self._session.set_export_settings(document.export)

        self.project_status_label.setText(f"项目已加载：{project_path.name}")

    def _save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            app_text("save_project_dialog"),
            self.default_project_directory(),
            app_text("project_file_filter"),
        )
        if path:
            self.save_project_to_path(path)

    def _load_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            app_text("load_project_dialog"),
            self.default_project_directory(),
            app_text("project_file_filter"),
        )
        if path:
            self.load_project_from_path(path)


def _serialize_video_metadata(metadata) -> dict:
    if metadata is None:
        return {}
    return {
        "width": metadata.width,
        "height": metadata.height,
        "fps": metadata.fps,
        "duration_sec": metadata.duration_sec,
        "rotation_deg": metadata.rotation_deg,
        "is_variable_frame_rate": metadata.is_variable_frame_rate,
    }


def _serialize_point(point: Point2D) -> dict:
    return {"x": point.x, "y": point.y}


def _serialize_timing_line(line: TimingLine) -> dict:
    return {
        "name": line.name,
        "start": _serialize_point(line.start),
        "end": _serialize_point(line.end),
        "direction": line.direction,
        "min_speed_kmh": line.min_speed_kmh,
        "cooldown_time_sec": line.cooldown_time_sec,
        "cooldown_distance_m": line.cooldown_distance_m,
    }


def _serialize_track_definition(
    track_definition: TrackDefinition | None,
    *,
    project_path: Path,
    background_image_path: str = "",
) -> dict:
    if track_definition is None:
        if not background_image_path:
            return {}
        return {
            "background_image_path": _serialize_project_path(
                background_image_path,
                project_path=project_path,
            ),
        }
    return {
        "start_finish": _serialize_timing_line(track_definition.start_finish),
        "sectors": [
            {**_serialize_timing_line(sector), "order": sector.order}
            for sector in track_definition.sectors
        ],
        "display_transform": {
            "translate_x": track_definition.display_transform.translate_x,
            "translate_y": track_definition.display_transform.translate_y,
            "rotation_deg": track_definition.display_transform.rotation_deg,
            "scale": track_definition.display_transform.scale,
        },
        "background_image_path": _serialize_project_path(
            track_definition.background_image_path or background_image_path,
            project_path=project_path,
        ),
    }


def _deserialize_point(payload: dict) -> Point2D:
    return Point2D(x=float(payload["x"]), y=float(payload["y"]))


def _deserialize_track_definition(payload: dict, *, project_path: Path) -> TrackDefinition | None:
    if not payload or "start_finish" not in payload:
        return None
    start_finish_payload = payload["start_finish"]
    start_finish = TimingLine(
        name=start_finish_payload["name"],
        start=_deserialize_point(start_finish_payload["start"]),
        end=_deserialize_point(start_finish_payload["end"]),
        direction=start_finish_payload.get("direction", "any"),
        min_speed_kmh=float(start_finish_payload.get("min_speed_kmh", 0.0)),
        cooldown_time_sec=float(start_finish_payload.get("cooldown_time_sec", 0.0)),
        cooldown_distance_m=float(start_finish_payload.get("cooldown_distance_m", 0.0)),
    )
    sectors = [
        SectorLine(
            name=sector_payload["name"],
            start=_deserialize_point(sector_payload["start"]),
            end=_deserialize_point(sector_payload["end"]),
            direction=sector_payload.get("direction", "any"),
            min_speed_kmh=float(sector_payload.get("min_speed_kmh", 0.0)),
            cooldown_time_sec=float(sector_payload.get("cooldown_time_sec", 0.0)),
            cooldown_distance_m=float(sector_payload.get("cooldown_distance_m", 0.0)),
            order=int(sector_payload.get("order", 0)),
        )
        for sector_payload in payload.get("sectors", [])
    ]
    display_transform_payload = payload.get("display_transform", {})
    return TrackDefinition(
        start_finish=start_finish,
        sectors=sectors,
        display_transform=DisplayTransform(
            translate_x=float(display_transform_payload.get("translate_x", 0.0)),
            translate_y=float(display_transform_payload.get("translate_y", 0.0)),
            rotation_deg=float(display_transform_payload.get("rotation_deg", 0.0)),
            scale=float(display_transform_payload.get("scale", 1.0)),
        ),
        background_image_path=_resolve_project_path(
            str(payload.get("background_image_path", "")),
            project_path=project_path,
        ),
    )


def _serialize_project_path(path_text: str, *, project_path: Path) -> str:
    if not path_text:
        return ""
    candidate = Path(path_text)
    try:
        return str(candidate.resolve().relative_to(project_path.parent.resolve()))
    except ValueError:
        return str(candidate)


def _resolve_project_path(path_text: str, *, project_path: Path) -> str:
    if not path_text:
        return ""
    candidate = Path(path_text)
    if candidate.is_absolute():
        return str(candidate)
    return str((project_path.parent / candidate).resolve())
