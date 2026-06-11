from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.ui.texts import app_text
from kart_overlay.ui.track_editor import TrackEditor
from kart_overlay.ui.track_inspector_panel import TrackInspectorPanel
from kart_overlay.ui.track_results_panel import TrackResultsPanel


class TrackWorkspace(QWidget):
    def __init__(self, *, session: ProjectSession | None = None) -> None:
        super().__init__()
        self._session = session or ProjectSession()
        self._suppress_slider_sync = False

        self.editor = TrackEditor()
        self.inspector = TrackInspectorPanel()
        self.results_panel = TrackResultsPanel()

        self.view_button = QPushButton(app_text("view_mode"))
        self.start_finish_button = QPushButton(app_text("start_finish_mode"))
        self.sector_button = QPushButton(app_text("sector_mode"))
        for button in (self.view_button, self.start_finish_button, self.sector_button):
            button.setCheckable(True)

        self.import_background_button = QPushButton("导入背景图")
        self.replace_background_button = QPushButton("替换背景图")
        self.clear_background_button = QPushButton("清除背景图")
        self.delete_selected_button = QPushButton("删除分段线")
        self.reset_start_finish_button = QPushButton("重置起终线")
        self.reset_background_transform_button = QPushButton("重置对齐")
        self.nudge_up_button = QPushButton("上移")
        self.nudge_down_button = QPushButton("下移")
        self.nudge_left_button = QPushButton("左移")
        self.nudge_right_button = QPushButton("右移")
        self.precise_zoom_in_button = QPushButton("放大")
        self.precise_zoom_out_button = QPushButton("缩小")
        self.rotate_left_button = QPushButton("左旋")
        self.rotate_right_button = QPushButton("右旋")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(15, 100)
        self.opacity_slider.setValue(55)
        self.point_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_slider.setRange(0, 0)
        self.point_slider.setSingleStep(1)
        self.point_index_label = QLabel("点 0 / 0")
        self.point_lap_label = QLabel("第 1 圈")

        self.editor_status_label = self.results_panel.status_value
        self.background_status_label = self.results_panel.background_value

        self.view_button.clicked.connect(lambda: self._set_mode("view"))
        self.start_finish_button.clicked.connect(lambda: self._set_mode("start_finish"))
        self.sector_button.clicked.connect(lambda: self._set_mode("sector"))
        self.import_background_button.clicked.connect(self._import_background_image)
        self.replace_background_button.clicked.connect(self._replace_background_image)
        self.clear_background_button.clicked.connect(self._clear_background_image)
        self.delete_selected_button.clicked.connect(self._delete_selected_line)
        self.reset_start_finish_button.clicked.connect(self._reset_start_finish)
        self.reset_background_transform_button.clicked.connect(self._reset_background_transform)
        self.nudge_up_button.clicked.connect(lambda: self._nudge_background(0.0, 1.0))
        self.nudge_down_button.clicked.connect(lambda: self._nudge_background(0.0, -1.0))
        self.nudge_left_button.clicked.connect(lambda: self._nudge_background(-1.0, 0.0))
        self.nudge_right_button.clicked.connect(lambda: self._nudge_background(1.0, 0.0))
        self.precise_zoom_in_button.clicked.connect(lambda: self._nudge_scale(1.01))
        self.precise_zoom_out_button.clicked.connect(lambda: self._nudge_scale(1.0 / 1.01))
        self.rotate_left_button.clicked.connect(lambda: self._nudge_rotation(-0.5))
        self.rotate_right_button.clicked.connect(lambda: self._nudge_rotation(0.5))
        self.opacity_slider.valueChanged.connect(self._update_background_opacity)
        self.point_slider.valueChanged.connect(self._handle_point_slider_changed)

        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(8, 8, 8, 8)
        results_layout.setSpacing(8)
        results_layout.addWidget(self.results_panel)
        results_layout.addWidget(self.inspector, 1)
        results_container.setMinimumWidth(340)

        self.operation_bar = self._build_operation_bar()
        self.operation_bar.setMinimumHeight(160)

        self.slider_bar = self._build_slider_bar()

        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_splitter.addWidget(results_container)
        self.top_splitter.addWidget(self.editor)
        self.top_splitter.setHandleWidth(10)
        self.top_splitter.setChildrenCollapsible(False)
        self.top_splitter.setStretchFactor(1, 1)
        self.top_splitter.setSizes([420, 1080])

        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        bottom_layout.addWidget(self.slider_bar)
        bottom_layout.addWidget(self.operation_bar)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(bottom_container)
        self.main_splitter.setHandleWidth(10)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setSizes([780, 210])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.main_splitter)

        self.editor.analysis_changed.connect(self._sync_analysis_panel)
        self.editor.sample_selected.connect(self._handle_editor_sample_selected)
        self.editor.status_changed.connect(self._handle_editor_status_changed)
        self.editor.track_definition_changed.connect(self._handle_editor_track_definition_changed)
        self.editor.edit_mode_changed.connect(self._handle_editor_mode_changed)
        self._session.telemetry_changed.connect(self._handle_session_telemetry_changed)
        self._session.video_metadata_changed.connect(self._handle_session_video_metadata_changed)
        self._session.track_definition_changed.connect(self._handle_session_track_definition_changed)

        self.results_panel.update_status(self.editor.status_message)
        self.results_panel.update_background_status(self.editor.background_status_message)
        self.results_panel.update_telemetry(self._session.telemetry, self._session.telemetry_source_path)
        self.results_panel.update_video(self._session.video_metadata)
        self._refresh_background_status()
        self._handle_editor_mode_changed(self.editor.edit_mode)

    def load_telemetry(self, telemetry: TelemetryStore) -> None:
        self.editor.load_telemetry(telemetry)
        self._configure_point_slider(telemetry)
        self._sync_analysis_panel()
        self._refresh_background_status()

    def set_background_image_path(self, image_path: str | Path) -> None:
        self.editor.set_background_image_path(image_path)
        self._refresh_background_status()

    def _set_mode(self, mode: str) -> None:
        target_mode = "view" if self.editor.edit_mode == mode and mode != "view" else mode
        self.editor.set_edit_mode(target_mode)
        self.results_panel.update_status(self.editor.status_message)

    def _sync_analysis_panel(self) -> None:
        state = self.editor.analysis_state
        self.inspector.update_analysis(
            lap_result=None if state is None else state.lap_result,
            sector_result=None if state is None else state.sector_result,
            analysis_summary=None if state is None else state.summary,
        )
        self.results_panel.update_analysis(
            telemetry=self._session.telemetry or getattr(self.editor, "_telemetry", None),
            lap_result=None if state is None else state.lap_result,
            sector_result=None if state is None else state.sector_result,
            analysis_summary=None if state is None else state.summary,
        )
        self._session.set_track_definition(self.editor.track_definition)
        self._session.set_track_analysis(None if state is None else state.summary)
        self.results_panel.update_status(self.editor.status_message)
        self._refresh_background_status()
        self._refresh_point_labels()

    def _handle_editor_status_changed(self, message: str) -> None:
        self.results_panel.update_status(message)

    def _handle_editor_track_definition_changed(self, track_definition) -> None:
        self._session.set_track_definition(track_definition)
        state = self.editor.analysis_state
        self._session.set_track_analysis(None if state is None else state.summary)
        self._refresh_background_status()
        self._refresh_point_labels()

    def _handle_editor_mode_changed(self, mode: str) -> None:
        self.view_button.setChecked(mode == "view")
        self.start_finish_button.setChecked(mode == "start_finish")
        self.sector_button.setChecked(mode == "sector")

    def _handle_session_telemetry_changed(self, telemetry, source_path) -> None:
        self.results_panel.update_telemetry(telemetry, source_path)
        self.load_telemetry(telemetry)

    def _handle_session_track_definition_changed(self, track_definition) -> None:
        if track_definition is None or track_definition == self.editor.track_definition:
            return
        self.editor.set_track_definition(track_definition)
        self._refresh_background_status()

    def _handle_session_video_metadata_changed(self, metadata) -> None:
        self.results_panel.update_video(metadata)

    def _handle_editor_sample_selected(self, sample) -> None:
        if sample is None:
            return
        self._set_slider_from_sample(sample)
        self.results_panel.update_selected_sample(sample)
        self._refresh_point_labels()

    def _delete_selected_line(self) -> None:
        self.editor.delete_selected_line()
        self._sync_analysis_panel()

    def _reset_start_finish(self) -> None:
        self.editor.reset_start_finish()
        self._sync_analysis_panel()

    def _nudge_background(self, delta_x: float, delta_y: float) -> None:
        self.editor.nudge_display_transform(delta_x=delta_x, delta_y=delta_y)
        self._sync_analysis_panel()

    def _nudge_scale(self, factor: float) -> None:
        scale_method = getattr(self.editor, "scale_display_transform", None)
        if callable(scale_method):
            scale_method(factor)
        self._sync_analysis_panel()

    def _nudge_rotation(self, delta_deg: float) -> None:
        rotate_method = getattr(self.editor, "rotate_display_transform", None)
        if callable(rotate_method):
            rotate_method(delta_deg)
        self._sync_analysis_panel()

    def _reset_background_transform(self) -> None:
        self.editor.reset_background_transform()
        self._refresh_background_status()

    def _update_background_opacity(self, value: int) -> None:
        self.editor.set_background_opacity(value / 100.0)
        self._refresh_background_status()

    def _import_background_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择背景图",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All files (*)",
        )
        if path:
            self.set_background_image_path(path)

    def _replace_background_image(self) -> None:
        self._import_background_image()

    def _clear_background_image(self) -> None:
        self.editor.clear_background_image()
        self._refresh_background_status()

    def _refresh_background_status(self) -> None:
        self.results_panel.update_background_status(self.editor.background_status_message)

    def _build_slider_bar(self) -> QWidget:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        layout.addWidget(self.point_lap_label)
        layout.addWidget(self.point_slider, 1)
        layout.addWidget(self.point_index_label)
        return frame

    def _build_operation_bar(self) -> QWidget:
        operation_bar = QFrame()
        layout = QHBoxLayout(operation_bar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.addWidget(
            self._build_group(
                "模式",
                [
                    [self.view_button, self.start_finish_button, self.sector_button],
                ],
            )
        )
        layout.addWidget(
            self._build_group(
                "背景图",
                [
                    [self.import_background_button, self.replace_background_button],
                    [self.clear_background_button, self.reset_background_transform_button],
                    [QLabel("透明度"), self.opacity_slider],
                ],
            )
        )
        layout.addWidget(self._build_track_adjust_group())
        layout.addWidget(
            self._build_group(
                "线操作",
                [
                    [self.delete_selected_button],
                    [self.reset_start_finish_button],
                ],
            )
        )
        layout.addStretch(1)
        return operation_bar

    def _build_track_adjust_group(self) -> QWidget:
        frame = QFrame()
        group_layout = QVBoxLayout(frame)
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(6)
        group_layout.addWidget(QLabel("轨迹微调"))

        remote_grid = QGridLayout()
        remote_grid.setHorizontalSpacing(6)
        remote_grid.setVerticalSpacing(6)
        remote_grid.addWidget(self.nudge_up_button, 0, 1)
        remote_grid.addWidget(self.nudge_left_button, 1, 0)
        remote_grid.addWidget(self.nudge_down_button, 1, 1)
        remote_grid.addWidget(self.nudge_right_button, 1, 2)
        remote_grid.addWidget(self.precise_zoom_in_button, 0, 3)
        remote_grid.addWidget(self.precise_zoom_out_button, 1, 3)
        remote_grid.addWidget(self.rotate_left_button, 0, 4)
        remote_grid.addWidget(self.rotate_right_button, 1, 4)
        group_layout.addLayout(remote_grid)
        return frame

    def _build_group(self, title: str, rows: list[list[QWidget]]) -> QWidget:
        frame = QFrame()
        group_layout = QVBoxLayout(frame)
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(6)
        group_layout.addWidget(QLabel(title))
        for row_widgets in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)
            for widget in row_widgets:
                row_layout.addWidget(widget)
            group_layout.addLayout(row_layout)
        return frame

    def _configure_point_slider(self, telemetry: TelemetryStore | None) -> None:
        if telemetry is None or not telemetry.samples:
            self.point_slider.setRange(0, 0)
            self.point_slider.setValue(0)
            self.point_index_label.setText("点 0 / 0")
            self.point_lap_label.setText("第 1 圈")
            self.results_panel.update_selected_sample(None)
            return

        self.point_slider.setRange(0, telemetry.sample_count - 1)
        self._suppress_slider_sync = True
        self.point_slider.setValue(telemetry.sample_count - 1)
        self._suppress_slider_sync = False
        self.editor.set_selected_sample(telemetry.samples[-1])

    def _set_slider_from_sample(self, sample) -> None:
        if sample is None:
            return
        self._suppress_slider_sync = True
        self.point_slider.setValue(sample.sample_index)
        self._suppress_slider_sync = False

    def _handle_point_slider_changed(self, index: int) -> None:
        if self._suppress_slider_sync:
            return
        telemetry = self._session.telemetry or getattr(self.editor, "_telemetry", None)
        if telemetry is None or not telemetry.samples:
            return
        clamped_index = max(0, min(index, telemetry.sample_count - 1))
        self.editor.set_selected_sample(telemetry.samples[clamped_index])

    def _refresh_point_labels(self) -> None:
        telemetry = self._session.telemetry or getattr(self.editor, "_telemetry", None)
        sample = self.editor.selected_sample
        if telemetry is None or not telemetry.samples or sample is None:
            total = 0 if telemetry is None else telemetry.sample_count
            self.point_index_label.setText(f"点 0 / {total}")
            self.point_lap_label.setText("第 1 圈")
            return

        self.point_index_label.setText(f"点 {sample.sample_index + 1} / {telemetry.sample_count}")
        summary = self.editor.analysis_state.summary if self.editor.analysis_state is not None else None
        lap_number = 1 if summary is None else summary.current_lap_number_at(sample.elapsed_sec)
        self.point_lap_label.setText(f"第 {lap_number} 圈")
