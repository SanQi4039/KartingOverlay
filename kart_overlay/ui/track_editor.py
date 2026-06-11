from dataclasses import dataclass, field, replace
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
)

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import TrackAnalysisBuilder, TrackAnalysisSummary
from kart_overlay.domain.track.models import DisplayTransform, Point2D, SectorLine, TimingLine, TrackDefinition
from kart_overlay.ui.texts import (
    app_text,
    track_endpoint_display_name,
    track_line_display_name,
    track_mode_status,
)
from kart_overlay.ui.track_scene_items import EditableTimingLineItem, LineHandleItem


@dataclass(frozen=True)
class TrackEditorAnalysisState:
    lap_result: LapDetectionResult | None = None
    sector_result: SectorDetectionResult = field(default_factory=lambda: SectorDetectionResult(sector_crossings={}))
    summary: TrackAnalysisSummary | None = None


class TrackEditor(QGraphicsView):
    analysis_changed = Signal()
    sample_selected = Signal(object)
    status_changed = Signal(str)
    track_definition_changed = Signal(object)
    edit_mode_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._telemetry: TelemetryStore | None = None
        self._track_definition: TrackDefinition | None = None
        self._display_transform = DisplayTransform()
        self._background_image_path = ""
        self._background_opacity = 0.55
        self._edit_mode = "view"
        self._analysis_builder = TrackAnalysisBuilder()
        self._analysis_state: TrackEditorAnalysisState | None = None
        self._pending_points: list[Point2D] = []
        self._pending_preview_point: Point2D | None = None
        self._background_item: QGraphicsPixmapItem | None = None
        self._track_path_item: QGraphicsPathItem | None = None
        self._pending_preview_item: QGraphicsPathItem | None = None
        self._background_status_message = app_text("background_not_loaded")
        self._selected_sample = None
        self._editable_items: list[EditableTimingLineItem] = []
        self._selected_line_key: str | None = None
        self._status_message = ""
        self._pending_endpoint_drag: tuple[str, str, tuple[float, float]] | None = None
        self._overlay_pan_origin_view: QPoint | None = None
        self._overlay_pan_origin_transform: DisplayTransform | None = None
        self._overlay_rotate_origin_x: int | None = None
        self._overlay_rotate_origin_rotation = 0.0
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setBackgroundBrush(QColor("#11161f"))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._apply_mode_interaction()
        self._set_status_message(track_mode_status("view"))

    @property
    def track_definition(self) -> TrackDefinition | None:
        return self._track_definition

    @property
    def analysis_state(self) -> TrackEditorAnalysisState | None:
        return self._analysis_state

    @property
    def selected_sample(self):
        return self._selected_sample

    @property
    def selected_line_key(self) -> str | None:
        return self._selected_line_key

    @property
    def status_message(self) -> str:
        return self._status_message

    @property
    def edit_mode(self) -> str:
        return self._edit_mode

    @property
    def display_transform(self) -> DisplayTransform:
        return self._display_transform

    @property
    def background_image_path(self) -> str:
        return self._background_image_path

    @property
    def background_status_message(self) -> str:
        return self._background_status_message

    @property
    def has_background_image(self) -> bool:
        return self._background_item is not None

    @property
    def has_pending_preview_line(self) -> bool:
        return self._pending_preview_item is not None

    @property
    def has_track_path(self) -> bool:
        return self._track_path_item is not None

    def load_telemetry(self, telemetry: TelemetryStore) -> None:
        self._telemetry = telemetry
        self._selected_sample = None
        self._selected_line_key = None
        self._pending_points = []
        self._pending_preview_point = None
        self._refresh_analysis()
        self._render()

    def set_track_definition(self, track_definition: TrackDefinition) -> None:
        self._track_definition = track_definition
        self._display_transform = track_definition.display_transform
        self._background_image_path = track_definition.background_image_path
        self._refresh_analysis()
        self._render()
        self.track_definition_changed.emit(self._track_definition)

    def set_edit_mode(self, mode: str) -> None:
        if mode not in {"view", "start_finish", "sector"}:
            raise ValueError(f"Unsupported edit mode: {mode}")
        self._edit_mode = mode
        self._pending_points = []
        self._pending_preview_point = None
        self._apply_mode_interaction()
        self._set_status_message(track_mode_status(mode))
        self.edit_mode_changed.emit(mode)

    def set_selected_sample(self, sample) -> None:
        self._selected_sample = sample
        self.sample_selected.emit(sample)
        self._render()

    def update_pending_preview(self, point: tuple[float, float]) -> None:
        if self._edit_mode not in {"start_finish", "sector"} or len(self._pending_points) != 1:
            self._pending_preview_point = None
            self._render(fit_view=False)
            return
        self._pending_preview_point = Point2D(*point)
        self._render(fit_view=False)

    def set_background_image_path(self, image_path: str | Path) -> None:
        self._background_image_path = str(image_path)
        self._background_status_message = app_text("background_loaded").format(
            name=Path(self._background_image_path).name
        )
        self._sync_track_definition()
        self._render()

    def clear_background_image(self) -> None:
        self._background_image_path = ""
        self._background_status_message = app_text("background_not_loaded")
        self._sync_track_definition()
        self._render()

    def reset_background_transform(self) -> None:
        self._update_display_transform(
            translate_x=0.0,
            translate_y=0.0,
            rotation_deg=0.0,
            scale=1.0,
        )

    def set_background_opacity(self, opacity: float) -> None:
        self._background_opacity = max(0.05, min(opacity, 1.0))
        self._render(fit_view=False)

    def select_nearest_sample(self, point: tuple[float, float]):
        if self._telemetry is None or not self._telemetry.samples:
            return None

        target_x, target_y = point
        candidates = [
            sample
            for sample in self._telemetry.samples
            if sample.x_m is not None and sample.y_m is not None
        ]
        if not candidates:
            return None

        selected = min(
            candidates,
            key=lambda sample: (sample.x_m - target_x) ** 2 + (sample.y_m - target_y) ** 2,
        )
        self._selected_sample = selected
        self.sample_selected.emit(selected)
        self._render()
        return selected

    def commit_line_from_points(self, start: tuple[float, float], end: tuple[float, float]) -> None:
        start_point = Point2D(*start)
        end_point = Point2D(*end)

        if self._edit_mode == "start_finish":
            self._track_definition = TrackDefinition(
                start_finish=TimingLine(
                    name="Start/Finish",
                    start=start_point,
                    end=end_point,
                    direction="positive_to_negative",
                ),
                sectors=[] if self._track_definition is None else self._track_definition.sectors,
                display_transform=self._display_transform,
                background_image_path=self._background_image_path,
            )
        elif self._edit_mode == "sector":
            if self._track_definition is None:
                raise ValueError("Start/finish line must be defined before adding sectors.")
            next_order = len(self._track_definition.sectors) + 1
            sectors = list(self._track_definition.sectors)
            sectors.append(
                SectorLine(
                    name=f"S{next_order}",
                    start=start_point,
                    end=end_point,
                    direction="negative_to_positive",
                    order=next_order,
                )
            )
            self._track_definition = TrackDefinition(
                start_finish=self._track_definition.start_finish,
                sectors=sectors,
                display_transform=self._display_transform,
                background_image_path=self._background_image_path,
            )
        else:
            raise ValueError(f"Unsupported edit mode: {self._edit_mode}")

        self._refresh_analysis()
        self._render()
        self.track_definition_changed.emit(self._track_definition)

    def handle_scene_click(self, point: tuple[float, float]) -> None:
        self._pending_points.append(Point2D(*point))
        self._pending_preview_point = None
        if len(self._pending_points) < 2:
            self._render(fit_view=False)
            return

        start_point, end_point = self._pending_points[:2]
        self._pending_points = []
        self.commit_line_from_points((start_point.x, start_point.y), (end_point.x, end_point.y))
        self.set_edit_mode("view")

    def move_line_endpoint(self, line_kind: str, endpoint: str, point: tuple[float, float]) -> None:
        if self._track_definition is None:
            raise ValueError("Track definition is not set.")

        new_point = Point2D(*point)
        if line_kind == "start_finish":
            line = self._track_definition.start_finish
            updated = TimingLine(
                name=line.name,
                start=new_point if endpoint == "start" else line.start,
                end=new_point if endpoint == "end" else line.end,
                direction=line.direction,
                min_speed_kmh=line.min_speed_kmh,
                cooldown_time_sec=line.cooldown_time_sec,
                cooldown_distance_m=line.cooldown_distance_m,
            )
            self._track_definition = TrackDefinition(
                start_finish=updated,
                sectors=self._track_definition.sectors,
                display_transform=self._display_transform,
                background_image_path=self._background_image_path,
            )
        elif line_kind.startswith("sector:"):
            sector_name = line_kind.split(":", 1)[1]
            sectors: list[SectorLine] = []
            for sector in self._track_definition.sectors:
                if sector.name != sector_name:
                    sectors.append(sector)
                    continue
                sectors.append(
                    SectorLine(
                        name=sector.name,
                        start=new_point if endpoint == "start" else sector.start,
                        end=new_point if endpoint == "end" else sector.end,
                        direction=sector.direction,
                        min_speed_kmh=sector.min_speed_kmh,
                        cooldown_time_sec=sector.cooldown_time_sec,
                        cooldown_distance_m=sector.cooldown_distance_m,
                        order=sector.order,
                    )
                )
            self._track_definition = TrackDefinition(
                start_finish=self._track_definition.start_finish,
                sectors=sectors,
                display_transform=self._display_transform,
                background_image_path=self._background_image_path,
            )
        else:
            raise ValueError(f"Unsupported line kind: {line_kind}")

        self._refresh_analysis()
        self._render()
        self.track_definition_changed.emit(self._track_definition)

    def editable_items(self) -> list[EditableTimingLineItem]:
        return list(self._editable_items)

    def drag_selected_endpoint(self, endpoint: str, point: tuple[float, float]) -> None:
        item = self._selected_item()
        if item is None:
            return
        self._pending_endpoint_drag = (item.line_key, endpoint, point)
        mapped_point = self._map_track_point(QPointF(point[0], -point[1]))
        item.preview_endpoint(endpoint, mapped_point.x(), mapped_point.y())
        self._set_status_message("释放后将重新计算计时")

    def _drag_selected_endpoint_scene(self, endpoint: str, point: tuple[float, float]) -> None:
        item = self._selected_item()
        if item is None:
            return
        canonical_point = self._scene_to_track_point(QPointF(point[0], point[1]))
        self._pending_endpoint_drag = (item.line_key, endpoint, canonical_point)
        item.preview_endpoint(endpoint, point[0], point[1])
        self._set_status_message("释放后将重新计算计时")

    def finish_endpoint_drag(self) -> None:
        if self._pending_endpoint_drag is None:
            return
        line_key, endpoint, point = self._pending_endpoint_drag
        self._pending_endpoint_drag = None
        self.move_line_endpoint(line_key, endpoint, point)
        self._set_status_message(self._build_recalculated_message())

    def delete_selected_line(self) -> None:
        if self._track_definition is None or self._selected_line_key is None:
            self._set_status_message(app_text("no_selected_sector_line"))
            return
        if not self._selected_line_key.startswith("sector:"):
            self._set_status_message(app_text("only_sector_lines_deletable"))
            return

        sector_name = self._selected_line_key.split(":", 1)[1]
        sectors = [sector for sector in self._track_definition.sectors if sector.name != sector_name]
        self._track_definition = TrackDefinition(
            start_finish=self._track_definition.start_finish,
            sectors=sectors,
            display_transform=self._display_transform,
            background_image_path=self._background_image_path,
        )
        self._selected_line_key = None
        self._refresh_analysis()
        self._render()
        self._set_status_message(self._build_recalculated_message())
        self.track_definition_changed.emit(self._track_definition)

    def reset_start_finish(self) -> None:
        self._track_definition = None
        self._selected_line_key = None
        self._pending_points = []
        self._pending_endpoint_drag = None
        self._refresh_analysis()
        self._render()
        self._set_status_message(app_text("start_finish_reset_done"))
        self.track_definition_changed.emit(self._track_definition)

    def nudge_display_transform(self, *, delta_x: float = 0.0, delta_y: float = 0.0) -> None:
        self._update_display_transform(
            translate_x=self._display_transform.translate_x + delta_x,
            translate_y=self._display_transform.translate_y + delta_y,
            fit_view=False,
        )

    def scale_display_transform(self, factor: float) -> None:
        self._update_display_transform(
            scale=self._display_transform.scale * factor,
            fit_view=False,
        )

    def rotate_display_transform(self, delta_deg: float) -> None:
        self._update_display_transform(
            rotation_deg=self._display_transform.rotation_deg + delta_deg,
            fit_view=False,
        )

    def mousePressEvent(self, event) -> None:
        if self._is_interactive_scene_item(event.position().toPoint()):
            super().mousePressEvent(event)
            return
        if self._edit_mode in {"start_finish", "sector"}:
            scene_point = self.mapToScene(event.position().toPoint())
            self.handle_scene_click(self._scene_to_track_point(scene_point))
            event.accept()
            return
        if self._edit_mode == "view" and self.has_background_image:
            if event.button() == Qt.MouseButton.LeftButton:
                self._overlay_pan_origin_view = event.position().toPoint()
                self._overlay_pan_origin_transform = self._display_transform
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            if event.button() == Qt.MouseButton.RightButton:
                self._overlay_rotate_origin_x = event.position().toPoint().x()
                self._overlay_rotate_origin_rotation = self._display_transform.rotation_deg
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._edit_mode in {"start_finish", "sector"} and len(self._pending_points) == 1:
            scene_point = self.mapToScene(event.position().toPoint())
            self.update_pending_preview(self._scene_to_track_point(scene_point))
            event.accept()
            return
        if self._overlay_pan_origin_view is not None and self._overlay_pan_origin_transform is not None:
            origin_scene = self.mapToScene(self._overlay_pan_origin_view)
            current_scene = self.mapToScene(event.position().toPoint())
            delta_scene = current_scene - origin_scene
            self._update_display_transform(
                translate_x=self._overlay_pan_origin_transform.translate_x + delta_scene.x(),
                translate_y=self._overlay_pan_origin_transform.translate_y - delta_scene.y(),
                fit_view=False,
            )
            event.accept()
            return
        if self._overlay_rotate_origin_x is not None:
            delta_x = event.position().toPoint().x() - self._overlay_rotate_origin_x
            self._update_display_transform(
                rotation_deg=self._overlay_rotate_origin_rotation + (delta_x * 0.25),
                fit_view=False,
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._overlay_pan_origin_view is not None or self._overlay_rotate_origin_x is not None:
            self._overlay_pan_origin_view = None
            self._overlay_pan_origin_transform = None
            self._overlay_rotate_origin_x = None
            self._apply_mode_interaction()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:
        if (
            self._edit_mode == "view"
            and self.has_background_image
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            factor = 1.08 if event.angleDelta().y() > 0 else 1.0 / 1.08
            self.scale_display_transform(factor)
            event.accept()
            return
        super().wheelEvent(event)

    def _render(self, *, fit_view: bool = True) -> None:
        previous_transform = self.transform()
        self._scene.clear()
        self._background_item = None
        self._track_path_item = None
        self._pending_preview_item = None
        self._editable_items = []

        canonical_points: list[QPointF] = []
        if self._telemetry is not None:
            canonical_points = [
                QPointF(sample.x_m, -sample.y_m)
                for sample in self._telemetry.samples
                if sample.x_m is not None and sample.y_m is not None
            ]

        canonical_bounds = QRectF(-160.0, -120.0, 320.0, 240.0)
        if canonical_points:
            canonical_path = QPainterPath(canonical_points[0])
            for point in canonical_points[1:]:
                canonical_path.lineTo(point)
            canonical_bounds = canonical_path.boundingRect()

        transformed_bounds = self._display_transform_rect(canonical_bounds)
        if canonical_points:
            mapped_points = [self._map_track_point(point) for point in canonical_points]
            transformed_path = QPainterPath(mapped_points[0])
            for point in mapped_points[1:]:
                transformed_path.lineTo(point)
            transformed_bounds = transformed_path.boundingRect()
            item = QGraphicsPathItem(transformed_path)
            pen = QPen(QColor("#2ad1a3"))
            pen.setWidthF(2.0)
            item.setPen(pen)
            self._scene.addItem(item)
            self._track_path_item = item

        if self._background_image_path:
            self._render_background(canonical_bounds)

        if self._track_definition is not None:
            self._add_line("start_finish", self._track_definition.start_finish, QColor("#ffb703"))
            for sector in self._track_definition.sectors:
                self._add_line(f"sector:{sector.name}", sector, QColor("#fb8500"))

        if self._selected_sample is not None and self._selected_sample.x_m is not None and self._selected_sample.y_m is not None:
            mapped_sample = self._map_track_point(QPointF(self._selected_sample.x_m, -self._selected_sample.y_m))
            marker = QGraphicsEllipseItem(
                mapped_sample.x() - 4.0,
                mapped_sample.y() - 4.0,
                8.0,
                8.0,
            )
            marker_pen = QPen(QColor("#8ecae6"))
            marker_pen.setWidthF(1.5)
            marker.setPen(marker_pen)
            marker.setBrush(QColor("#219ebc"))
            self._scene.addItem(marker)

        if len(self._pending_points) == 1 and self._pending_preview_point is not None:
            start_point = self._pending_points[0]
            mapped_start = self._map_track_point(QPointF(start_point.x, -start_point.y))
            mapped_end = self._map_track_point(QPointF(self._pending_preview_point.x, -self._pending_preview_point.y))
            preview_path = QPainterPath(mapped_start)
            preview_path.lineTo(mapped_end)
            preview_item = QGraphicsPathItem(preview_path)
            preview_pen = QPen(QColor("#8ecae6"))
            preview_pen.setWidthF(2.0)
            preview_pen.setStyle(Qt.PenStyle.DashLine)
            preview_item.setPen(preview_pen)
            preview_item.setZValue(18)
            self._scene.addItem(preview_item)
            self._pending_preview_item = preview_item

        scene_rect = transformed_bounds
        if self._background_item is not None:
            scene_rect = scene_rect.united(self._background_item.sceneBoundingRect())
        scene_rect = scene_rect.adjusted(-24.0, -24.0, 24.0, 24.0)
        self._scene.setSceneRect(scene_rect)
        if fit_view:
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.setTransform(previous_transform)

    def _render_background(self, track_bounds: QRectF) -> None:
        pixmap = QPixmap(self._background_image_path)
        if pixmap.isNull():
            self._background_status_message = app_text("background_load_failed").format(
                name=Path(self._background_image_path).name
            )
            return

        background_rect = self._fit_background_rect(track_bounds=track_bounds, pixmap=pixmap)
        self._background_item = QGraphicsPixmapItem(pixmap)
        self._background_item.setOpacity(self._background_opacity)
        self._background_item.setZValue(-100)
        base_scale = background_rect.height() / max(float(pixmap.height()), 1.0)
        self._background_item.setScale(base_scale)
        self._background_item.setPos(background_rect.left(), background_rect.top())
        self._scene.addItem(self._background_item)
        self._background_status_message = app_text("background_loaded").format(
            name=Path(self._background_image_path).name
        )

    def _add_line(self, line_key: str, line_definition, color: QColor) -> None:
        visual_style = "checker" if line_key == "start_finish" else "sector"
        start_point = self._map_track_point(QPointF(line_definition.start.x, -line_definition.start.y))
        end_point = self._map_track_point(QPointF(line_definition.end.x, -line_definition.end.y))
        line_item = EditableTimingLineItem(
            line_key=line_key,
            label=line_definition.name,
            x1=start_point.x(),
            y1=start_point.y(),
            x2=end_point.x(),
            y2=end_point.y(),
            color=color,
            visual_style=visual_style,
            on_selected=self._handle_line_item_selected,
            on_endpoint_pressed=self._handle_endpoint_pressed,
            on_endpoint_dragged=self._drag_selected_endpoint_scene,
            on_endpoint_released=self.finish_endpoint_drag,
        )
        self._scene.addItem(line_item)
        line_item.attach_handles(self._scene)
        if line_key == self._selected_line_key:
            line_item.set_selected_visual(True)
        self._editable_items.append(line_item)

    def _handle_line_item_selected(self, line_key: str, label: str) -> None:
        self._selected_line_key = line_key
        for item in self._editable_items:
            item.set_selected_visual(item.line_key == line_key)
        self._set_status_message(f"已选中：{track_line_display_name(label)}")

    def _selected_item(self) -> EditableTimingLineItem | None:
        for item in self._editable_items:
            if item.line_key == self._selected_line_key:
                return item
        return None

    def _handle_endpoint_pressed(self, line_key: str, label: str, endpoint: str) -> None:
        self._handle_line_item_selected(line_key, label)
        self._set_status_message(f"已选中：{track_line_display_name(label)} {track_endpoint_display_name(endpoint)}")

    def _build_recalculated_message(self) -> str:
        summary = self._analysis_state.summary if self._analysis_state is not None else None
        best_text = "--"
        if summary is not None and summary.best_lap_time_sec is not None:
            best_text = f"{summary.best_lap_time_sec:.3f} s"
        return f"重新计算：最佳圈 {best_text}"

    def _is_interactive_scene_item(self, position) -> bool:
        item = self.itemAt(position)
        while item is not None:
            if isinstance(item, (EditableTimingLineItem, LineHandleItem)):
                return True
            item = item.parentItem()
        return False

    def _set_status_message(self, message: str) -> None:
        self._status_message = message
        self.status_changed.emit(message)

    def _refresh_analysis(self) -> None:
        if self._telemetry is None or self._track_definition is None:
            self._analysis_state = None
            self.analysis_changed.emit()
            return

        summary = self._analysis_builder.build(store=self._telemetry, track_definition=self._track_definition)
        self._analysis_state = TrackEditorAnalysisState(
            lap_result=summary.lap_result,
            sector_result=summary.sector_result,
            summary=summary,
        )
        self.analysis_changed.emit()

    def _sync_track_definition(self) -> None:
        if self._track_definition is None:
            self.track_definition_changed.emit(None)
            return
        self._track_definition = TrackDefinition(
            start_finish=self._track_definition.start_finish,
            sectors=list(self._track_definition.sectors),
            display_transform=self._display_transform,
            background_image_path=self._background_image_path,
        )
        self.track_definition_changed.emit(self._track_definition)

    def _update_display_transform(
        self,
        *,
        translate_x: float | None = None,
        translate_y: float | None = None,
        rotation_deg: float | None = None,
        scale: float | None = None,
        fit_view: bool = True,
    ) -> None:
        self._display_transform = replace(
            self._display_transform,
            translate_x=self._display_transform.translate_x if translate_x is None else translate_x,
            translate_y=self._display_transform.translate_y if translate_y is None else translate_y,
            rotation_deg=self._display_transform.rotation_deg if rotation_deg is None else rotation_deg,
            scale=self._display_transform.scale if scale is None else max(scale, 0.1),
        )
        self._sync_track_definition()
        self._render(fit_view=fit_view)

    def _display_qtransform(self) -> QTransform:
        transform = QTransform()
        transform.translate(self._display_transform.translate_x, -self._display_transform.translate_y)
        transform.rotate(self._display_transform.rotation_deg)
        transform.scale(self._display_transform.scale, self._display_transform.scale)
        return transform

    def _map_track_point(self, point: QPointF) -> QPointF:
        return self._display_qtransform().map(point)

    def _scene_to_track_point(self, point: QPointF) -> tuple[float, float]:
        inverse, ok = self._display_qtransform().inverted()
        mapped = inverse.map(point) if ok else point
        return mapped.x(), -mapped.y()

    def _display_transform_rect(self, rect: QRectF) -> QRectF:
        return self._display_qtransform().mapRect(rect)

    def _apply_mode_interaction(self) -> None:
        if self._edit_mode in {"start_finish", "sector"}:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
            return
        if self.has_background_image or self._background_image_path:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            return
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    @staticmethod
    def _fit_background_rect(*, track_bounds: QRectF, pixmap: QPixmap) -> QRectF:
        target_width = max(track_bounds.width() * 1.35, 160.0)
        target_height = max(track_bounds.height() * 1.35, 120.0)
        pixmap_width = max(float(pixmap.width()), 1.0)
        pixmap_height = max(float(pixmap.height()), 1.0)
        scale = max(target_width / pixmap_width, target_height / pixmap_height)
        scaled_width = pixmap_width * scale
        scaled_height = pixmap_height * scale
        center = track_bounds.center()
        return QRectF(
            center.x() - scaled_width / 2.0,
            center.y() - scaled_height / 2.0,
            scaled_width,
            scaled_height,
        )
