from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.interpolator import TelemetryInterpolator
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.infrastructure.render.frame_renderer import FrameRenderer
from kart_overlay.infrastructure.video.video_frame_extractor import VideoFrameExtractor
from kart_overlay.ui.texts import app_text, widget_display_name, widget_key_from_display_name
from kart_overlay.widgets.hud_theme import DEFAULT_CARD_OPACITY, DEFAULT_FONT_SCALE, MIN_FONT_SCALE, draw_checkerboard
from kart_overlay.widgets.widget_factory import build_widgets_from_session, minimum_widget_dimensions, widget_label_pairs


class CanvasPreviewWidget(QWidget):
    widget_selected = Signal(object)

    def __init__(
        self,
        *,
        session: ProjectSession,
        frame_extractor: object | None = None,
    ) -> None:
        super().__init__()
        self._session = session
        self._frame_extractor = frame_extractor or VideoFrameExtractor()
        self._preview_time_sec = 0.0
        self._selected_widget_key: str | None = None
        self._dragging = False
        self._resizing = False
        self._drag_offset = QPoint(0, 0)
        self._active_resize_handle: str | None = None
        self._resize_origin = QPoint(0, 0)
        self._resize_start_size = (0, 0)
        self._overlay_cache_key: tuple[object, ...] | None = None
        self._overlay_cache_image: QImage | None = None
        self._video_reference_cache_path: str | None = None
        self._video_reference_cache_image: QImage | None = None
        self._video_reference_cache_loaded = False
        self.setMinimumSize(480, 270)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._session.widget_layouts_changed.connect(self._handle_widget_layouts_changed)
        self._session.telemetry_changed.connect(self._handle_overlay_source_changed)
        self._session.track_definition_changed.connect(self._handle_overlay_source_changed)
        self._session.track_analysis_changed.connect(self._handle_overlay_source_changed)
        self._session.video_path_changed.connect(self._handle_video_path_changed)
        self._session.video_metadata_changed.connect(self._handle_video_metadata_changed)

    def set_preview_time(self, preview_time_sec: float) -> None:
        self._preview_time_sec = preview_time_sec
        self._invalidate_overlay_cache()
        self.update()

    def set_selected_widget_key(self, widget_key: str | None) -> None:
        self._selected_widget_key = widget_key
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            target_rect = self._target_rect()
            self._draw_preview_background(painter, target_rect)
            self._draw_overlay_vector(painter, target_rect)
            self._draw_canvas_edge_annotations(painter, target_rect)
            self._draw_selection(painter, target_rect)
        finally:
            painter.end()

    def _draw_preview_background(self, painter: QPainter, target_rect: QRect) -> None:
        draw_checkerboard(painter, self.rect())
        reference_image = self._video_reference_image()
        if reference_image is None:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(QRectF(target_rect), reference_image)
        painter.restore()

    def _video_reference_image(self) -> QImage | None:
        video_path = self._session.video_path.strip()
        if not video_path:
            self._video_reference_cache_path = None
            self._video_reference_cache_image = None
            self._video_reference_cache_loaded = False
            return None
        if self._video_reference_cache_path == video_path and self._video_reference_cache_loaded:
            return self._video_reference_cache_image
        self._video_reference_cache_path = video_path
        self._video_reference_cache_loaded = True
        try:
            self._video_reference_cache_image = self._frame_extractor.extract_first_frame(video_path)
        except Exception:
            self._video_reference_cache_image = None
        return self._video_reference_cache_image

    def mousePressEvent(self, event) -> None:
        handle_name = self._resize_handle_at(event.position().toPoint())
        if handle_name is not None:
            widget = self._selected_widget()
            if widget is None:
                return
            self._resizing = True
            self._dragging = False
            self._active_resize_handle = handle_name
            self._resize_origin = event.position().toPoint()
            self._resize_start_size = (int(widget.width), int(widget.height))
            self.update()
            return

        widget = self._widget_at(event.position().toPoint())
        if widget is None:
            self._selected_widget_key = None
            self._dragging = False
            self._resizing = False
            self.widget_selected.emit(None)
            self.update()
            return

        self._selected_widget_key = widget.widget_key
        self.widget_selected.emit(widget.widget_key)
        scale_x, scale_y, target_rect = self._scale_factors()
        bounds = widget.bounds_rect()
        widget_left = target_rect.x() + int(bounds.x() * scale_x)
        widget_top = target_rect.y() + int(bounds.y() * scale_y)
        self._drag_offset = event.position().toPoint() - QPoint(widget_left, widget_top)
        self._dragging = True
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._resizing and self._selected_widget_key is not None:
            self._resize_selected_widget_from_drag(event.position().toPoint())
            return
        if not self._dragging or self._selected_widget_key is None:
            self._update_cursor(event.position().toPoint())
            return

        widget = self._selected_widget()
        if widget is None:
            return

        scale_x, scale_y, target_rect = self._scale_factors()
        canvas_x = int(
            (event.position().x() - target_rect.x() - self._drag_offset.x())
            / max(scale_x, 0.001)
        )
        canvas_y = int(
            (event.position().y() - target_rect.y() - self._drag_offset.y())
            / max(scale_y, 0.001)
        )
        canvas_width, canvas_height = self._canvas_size()
        max_x = max(canvas_width - int(widget.bounds_rect().width()), 0)
        max_y = max(canvas_height - int(widget.bounds_rect().height()), 0)
        self._set_widget_layout(
            self._selected_widget_key,
            x=min(max(0, canvas_x), max_x),
            y=min(max(0, canvas_y), max_y),
        )

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False
        self._resizing = False
        self._active_resize_handle = None
        self._update_cursor(event.position().toPoint())

    def _render_overlay_image(self) -> QImage | None:
        canvas_size = self._canvas_size()
        widgets = build_widgets_from_session(self._session)
        if not widgets:
            return None
        frame = self._preview_frame()
        return FrameRenderer(canvas_size=canvas_size, widgets=widgets).render(frame)

    def _current_overlay_image(self) -> QImage | None:
        cache_key = self._overlay_state_key()
        if self._overlay_cache_key == cache_key and self._overlay_cache_image is not None:
            return self._overlay_cache_image
        overlay_image = self._render_overlay_image()
        self._overlay_cache_key = cache_key
        self._overlay_cache_image = overlay_image
        return overlay_image

    def _preview_frame(self):
        telemetry = self._session.telemetry
        if telemetry is None:
            from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame

            return TelemetryFrame(
                data_elapsed_sec=self._preview_time_sec,
                x_m=None,
                y_m=None,
                speed_kmh=None,
            )
        return TelemetryInterpolator(telemetry).frame_at(
            min(max(self._preview_time_sec, 0.0), telemetry.duration_sec)
        )

    def _widget_at(self, point: QPoint):
        scale_x, scale_y, target_rect = self._scale_factors()
        for widget in reversed(build_widgets_from_session(self._session)):
            bounds = widget.bounds_rect()
            scaled_rect = QRect(
                target_rect.x() + int(bounds.x() * scale_x),
                target_rect.y() + int(bounds.y() * scale_y),
                int(bounds.width() * scale_x),
                int(bounds.height() * scale_y),
            )
            if scaled_rect.contains(point):
                return widget
        return None

    def _draw_selection(self, painter: QPainter, target_rect: QRect) -> None:
        widget = self._selected_widget()
        if widget is None:
            return
        selection_rect = self._widget_preview_rect(widget)
        painter.save()
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRect(selection_rect)
        painter.setBrush(Qt.GlobalColor.white)
        for handle_rect in self.resize_handle_rects().values():
            painter.drawRect(handle_rect)
        painter.restore()

    def resize_handle_rects(self) -> dict[str, QRect]:
        widget = self._selected_widget()
        if widget is None:
            return {}
        rect = self._widget_preview_rect(widget)
        handle_size = 10
        half = handle_size // 2
        return {
            "top_left": QRect(rect.left() - half, rect.top() - half, handle_size, handle_size),
            "top_right": QRect(rect.right() - half, rect.top() - half, handle_size, handle_size),
            "bottom_left": QRect(rect.left() - half, rect.bottom() - half, handle_size, handle_size),
            "bottom_right": QRect(rect.right() - half, rect.bottom() - half, handle_size, handle_size),
        }

    def resize_selected_widget(self, width: int, height: int) -> None:
        if self._selected_widget_key is None:
            return
        layout = self._session.widget_layouts.get(self._selected_widget_key, {})
        min_width, min_height = minimum_widget_dimensions(
            self._selected_widget_key,
            font_scale=float(layout.get("font_scale", DEFAULT_FONT_SCALE)),
        )
        self._set_widget_layout(
            self._selected_widget_key,
            width=max(min_width, int(width)),
            height=max(min_height, int(height)),
        )

    def _canvas_size(self) -> tuple[int, int]:
        if self._session.video_metadata is not None:
            return self._session.video_metadata.canvas_size
        return (1280, 720)

    def _selected_widget(self):
        if self._selected_widget_key is None:
            return None
        for widget in build_widgets_from_session(self._session):
            if widget.widget_key == self._selected_widget_key:
                return widget
        return None

    def _draw_overlay_vector(self, painter: QPainter, target_rect: QRect) -> None:
        widgets = build_widgets_from_session(self._session)
        if not widgets:
            return
        frame = self._preview_frame()
        scale_x, scale_y, _ = self._scale_factors()
        painter.save()
        painter.translate(target_rect.x(), target_rect.y())
        painter.scale(scale_x, scale_y)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for widget in widgets:
            widget.render(painter, frame)
        painter.restore()

    def _overlay_state_key(self) -> tuple[object, ...]:
        telemetry = self._session.telemetry
        telemetry_key: tuple[object, ...] = ("none",)
        if telemetry is not None:
            telemetry_key = (
                len(telemetry.samples),
                round(telemetry.duration_sec, 3),
                telemetry.samples[-1].sample_index if telemetry.samples else -1,
            )
        layout_key = tuple(
            sorted(
                (
                    widget_key,
                    tuple(sorted(layout.items())),
                )
                for widget_key, layout in self._session.widget_layouts.items()
            )
        )
        return (
            round(self._preview_time_sec, 3),
            self._canvas_size(),
            telemetry_key,
            layout_key,
            self._session.track_definition is not None,
            self._session.track_analysis is not None,
        )

    def _invalidate_overlay_cache(self) -> None:
        self._overlay_cache_key = None
        self._overlay_cache_image = None

    def _set_widget_layout(self, widget_key: str, **updates: object) -> None:
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        widget_layouts[widget_key].update(updates)
        self._session.set_widget_layouts(widget_layouts)

    def _handle_widget_layouts_changed(
        self,
        _widget_layouts: dict[str, dict[str, object]],
    ) -> None:
        self._invalidate_overlay_cache()
        self.update()

    def _handle_overlay_source_changed(self, *_args) -> None:
        self._invalidate_overlay_cache()
        self.update()

    def _handle_video_metadata_changed(self, _metadata) -> None:
        self._invalidate_overlay_cache()
        self.update()

    def _handle_video_path_changed(self, _video_path: str) -> None:
        self._invalidate_video_reference_cache()
        self.update()

    def _invalidate_video_reference_cache(self) -> None:
        self._video_reference_cache_path = None
        self._video_reference_cache_image = None
        self._video_reference_cache_loaded = False

    def _target_rect(self) -> QRect:
        canvas_width, canvas_height = self._canvas_size()
        if canvas_width <= 0 or canvas_height <= 0:
            return self.rect()
        aspect = canvas_width / canvas_height
        target_width = self.width()
        target_height = int(target_width / aspect)
        if target_height > self.height():
            target_height = self.height()
            target_width = int(target_height * aspect)
        return QRect(
            (self.width() - target_width) // 2,
            (self.height() - target_height) // 2,
            target_width,
            target_height,
        )

    def _scale_factors(self) -> tuple[float, float, QRect]:
        target_rect = self._target_rect()
        canvas_width, canvas_height = self._canvas_size()
        return (
            target_rect.width() / max(canvas_width, 1),
            target_rect.height() / max(canvas_height, 1),
            target_rect,
        )

    def _widget_preview_rect(self, widget) -> QRect:
        scale_x, scale_y, target_rect = self._scale_factors()
        bounds = widget.bounds_rect()
        return QRect(
            target_rect.x() + int(bounds.x() * scale_x),
            target_rect.y() + int(bounds.y() * scale_y),
            max(1, int(bounds.width() * scale_x)),
            max(1, int(bounds.height() * scale_y)),
        )

    def _resize_handle_at(self, point: QPoint) -> str | None:
        for handle_name, handle_rect in self.resize_handle_rects().items():
            if handle_rect.contains(point):
                return handle_name
        return None

    def _resize_selected_widget_from_drag(self, point: QPoint) -> None:
        widget = self._selected_widget()
        if widget is None or self._active_resize_handle is None:
            return
        scale_x, scale_y, _ = self._scale_factors()
        delta_x = int((point.x() - self._resize_origin.x()) / max(scale_x, 0.001))
        delta_y = int((point.y() - self._resize_origin.y()) / max(scale_y, 0.001))

        start_width, start_height = self._resize_start_size
        next_width = start_width
        next_height = start_height
        if "right" in self._active_resize_handle:
            next_width = start_width + delta_x
        if "left" in self._active_resize_handle:
            next_width = start_width - delta_x
        if "bottom" in self._active_resize_handle:
            next_height = start_height + delta_y
        if "top" in self._active_resize_handle:
            next_height = start_height - delta_y
        self.resize_selected_widget(next_width, next_height)

    def _update_cursor(self, point: QPoint) -> None:
        handle_name = self._resize_handle_at(point)
        if handle_name in {"top_left", "bottom_right"}:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            return
        if handle_name in {"top_right", "bottom_left"}:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            return
        widget = self._widget_at(point)
        if widget is not None:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            return
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def canvas_edge_annotations(self) -> dict[str, str]:
        canvas_width, canvas_height = self._canvas_size()
        return {
            "width": f"{canvas_width} px",
            "height": f"{canvas_height} px",
        }

    def _draw_canvas_edge_annotations(self, painter: QPainter, target_rect: QRect) -> None:
        labels = self.canvas_edge_annotations()
        painter.save()
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRect(target_rect)
        width_label_rect = QRect(
            target_rect.left(),
            max(target_rect.top() - 26, 0),
            target_rect.width(),
            20,
        )
        painter.drawText(width_label_rect, Qt.AlignmentFlag.AlignCenter, labels["width"])
        height_label_rect = QRect(
            min(target_rect.right() + 8, self.width() - 56),
            target_rect.top(),
            52,
            target_rect.height(),
        )
        painter.drawText(height_label_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, labels["height"])
        painter.restore()


class CanvasWorkspace(QWidget):
    def __init__(
        self,
        *,
        session: ProjectSession | None = None,
        frame_extractor: object | None = None,
    ) -> None:
        super().__init__()
        self._session = session or ProjectSession()
        self._selected_widget_key: str | None = None

        self.widget_list = QListWidget()
        for widget_key, display_name in widget_label_pairs():
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, widget_key)
            self.widget_list.addItem(item)
        self.widget_list.currentTextChanged.connect(self.select_widget)
        self.widget_list.installEventFilter(self)

        self.x_input = QSpinBox()
        self.x_input.setRange(0, 3840)
        self.x_input.installEventFilter(self)
        self.y_input = QSpinBox()
        self.y_input.setRange(0, 2160)
        self.y_input.installEventFilter(self)
        self.width_input = QSpinBox()
        self.width_input.setRange(80, 3840)
        self.width_input.installEventFilter(self)
        self.height_input = QSpinBox()
        self.height_input.setRange(40, 2160)
        self.height_input.installEventFilter(self)
        self.background_opacity_input = QSpinBox()
        self.background_opacity_input.setRange(0, 100)
        self.background_opacity_input.setSuffix("%")
        self.background_opacity_input.setValue(DEFAULT_CARD_OPACITY)
        self.background_opacity_input.installEventFilter(self)
        self.background_opacity_input.valueChanged.connect(self._handle_background_opacity_changed)
        self.font_smaller_button = QPushButton("字体 -")
        self.font_smaller_button.clicked.connect(lambda: self._adjust_selected_font_scale(-0.1))
        self.font_larger_button = QPushButton("字体 +")
        self.font_larger_button.clicked.connect(lambda: self._adjust_selected_font_scale(0.1))
        self.font_scale_label = QLabel("字体 100%")
        self.enabled_toggle = QCheckBox(app_text("widget_visible"))
        self.enabled_toggle.toggled.connect(self._handle_enabled_toggled)
        self.hide_widget_button = QPushButton(app_text("hide_widget"))
        self.hide_widget_button.clicked.connect(self.hide_selected_widget)
        self.preview_time_slider = QSlider(Qt.Orientation.Horizontal)
        self.preview_time_slider.setRange(0, 0)
        self.preview_time_slider.valueChanged.connect(self._handle_preview_time_changed)
        self.apply_position_button = QPushButton(app_text("apply_position"))
        self.apply_position_button.clicked.connect(self.apply_selected_widget_geometry)

        self.position_label = QLabel(app_text("position_empty"))
        self.preview_label = QLabel(app_text("canvas_preview_title"))
        self.preview_summary_label = QLabel(app_text("preview_summary_empty"))
        self.preview_time_label = QLabel(app_text("preview_time_default"))
        self.preview_summary_label.setWordWrap(True)
        self.preview_summary_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )

        self.preview_widget = CanvasPreviewWidget(session=self._session, frame_extractor=frame_extractor)
        self.preview_widget.installEventFilter(self)
        self.preview_widget.widget_selected.connect(self._handle_preview_widget_selected)
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.hide_selected_widget)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        form = QFormLayout()
        form.addRow("X", self.x_input)
        form.addRow("Y", self.y_input)
        form.addRow(app_text("canvas_width"), self.width_input)
        form.addRow(app_text("canvas_height"), self.height_input)
        form.addRow("背景透明度", self.background_opacity_input)
        font_scale_row = QHBoxLayout()
        font_scale_row.addWidget(self.font_smaller_button)
        font_scale_row.addWidget(self.font_larger_button)
        font_scale_row.addWidget(self.font_scale_label)
        form.addRow("字体大小", font_scale_row)
        controls_layout.addWidget(QLabel(app_text("canvas_widgets")))
        controls_layout.addWidget(self.widget_list)
        controls_layout.addLayout(form)
        controls_layout.addWidget(self.enabled_toggle)
        controls_layout.addWidget(self.preview_time_label)
        controls_layout.addWidget(self.preview_time_slider)
        controls_layout.addWidget(self.apply_position_button)
        controls_layout.addWidget(self.position_label)
        controls_layout.addStretch(1)
        controls.setMinimumWidth(240)
        controls.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.addWidget(QLabel(app_text("canvas_preview")))
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_summary_label)
        preview_layout.addWidget(self.preview_widget, 1)
        preview_layout.addStretch(1)
        preview.setMinimumWidth(360)
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        splitter = QSplitter()
        splitter.addWidget(controls)
        splitter.addWidget(preview)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 980])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self._session.widget_layouts_changed.connect(self._handle_widget_layouts_changed)
        self._session.telemetry_changed.connect(self._handle_session_telemetry_changed)
        self._handle_widget_layouts_changed(self._session.widget_layouts)
        if self._session.telemetry is not None:
            self._handle_session_telemetry_changed(
                self._session.telemetry,
                self._session.telemetry_source_path,
            )
        self.widget_list.setCurrentRow(0)

    def eventFilter(self, watched, event) -> bool:
        if (
            watched
            in {
                self.widget_list,
                self.preview_widget,
                self.x_input,
                self.y_input,
                self.width_input,
                self.height_input,
                self.background_opacity_input,
            }
            and event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Delete
        ):
            self.hide_selected_widget()
            return True
        return super().eventFilter(watched, event)

    def select_widget(self, widget_name: str) -> None:
        if not widget_name:
            return
        widget_key = self._selected_widget_key_from_ui_value(widget_name)
        if widget_key is None:
            return
        matched_item = self._list_item_for_widget_key(widget_key)
        if matched_item is not None and self.widget_list.currentItem() is not matched_item:
            self.widget_list.blockSignals(True)
            self.widget_list.setCurrentItem(matched_item)
            self.widget_list.blockSignals(False)

        self._selected_widget_key = widget_key
        self.preview_widget.set_selected_widget_key(widget_key)
        layout = self._session.widget_layouts.get(widget_key, {"x": 0, "y": 0})
        width, height = self._widget_dimensions(widget_key)
        self.x_input.setValue(int(layout.get("x", 0)))
        self.y_input.setValue(int(layout.get("y", 0)))
        self.width_input.setValue(width)
        self.height_input.setValue(height)
        self.background_opacity_input.blockSignals(True)
        self.background_opacity_input.setValue(int(layout.get("background_opacity", DEFAULT_CARD_OPACITY)))
        self.background_opacity_input.blockSignals(False)
        self._set_font_scale_label(float(layout.get("font_scale", DEFAULT_FONT_SCALE)))
        self.enabled_toggle.blockSignals(True)
        self.enabled_toggle.setChecked(bool(layout.get("enabled", False)))
        self.enabled_toggle.blockSignals(False)
        self.position_label.setText(f"X={self.x_input.value()}, Y={self.y_input.value()}")

    def move_selected_widget(self, x: int, y: int) -> None:
        if self._ensure_selected_widget_key() is None:
            return
        self._update_selected_widget_layout(
            x=x,
            y=y,
            width=self.width_input.value(),
            height=self.height_input.value(),
        )
        self.position_label.setText(f"X={x}, Y={y}")

    def hide_selected_widget(self) -> None:
        widget_key = self._ensure_selected_widget_key()
        if widget_key is None:
            return
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        widget_layouts[widget_key]["enabled"] = False
        self._session.set_widget_layouts(widget_layouts)

    def apply_selected_widget_geometry(self) -> None:
        if self._ensure_selected_widget_key() is None:
            return
        self._update_selected_widget_layout(
            x=self.x_input.value(),
            y=self.y_input.value(),
            width=self.width_input.value(),
            height=self.height_input.value(),
        )
        self.position_label.setText(
            f"X={self.x_input.value()}, Y={self.y_input.value()}"
        )

    def _update_selected_widget_layout(
        self,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        widget_key = self._ensure_selected_widget_key()
        if widget_key is None:
            return
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        current_layout = widget_layouts[widget_key]
        min_width, min_height = minimum_widget_dimensions(
            widget_key,
            font_scale=float(current_layout.get("font_scale", DEFAULT_FONT_SCALE)),
        )
        widget_layouts[widget_key]["x"] = x
        widget_layouts[widget_key]["y"] = y
        widget_layouts[widget_key]["width"] = max(min_width, int(width))
        widget_layouts[widget_key]["height"] = max(min_height, int(height))
        self._session.set_widget_layouts(widget_layouts)

    def _handle_widget_layouts_changed(
        self,
        widget_layouts: dict[str, dict[str, object]],
    ) -> None:
        summary = ", ".join(
            f"{widget_display_name(name)} ({layout.get('x', 0)}, {layout.get('y', 0)})"
            for name, layout in sorted(widget_layouts.items())
        )
        self.preview_summary_label.setText(summary or app_text("preview_summary_empty"))
        if self._selected_widget_key is not None and self._selected_widget_key in widget_layouts:
            layout = widget_layouts[self._selected_widget_key]
            width, height = self._widget_dimensions(self._selected_widget_key)
            self.x_input.setValue(int(layout.get("x", 0)))
            self.y_input.setValue(int(layout.get("y", 0)))
            self.width_input.setValue(width)
            self.height_input.setValue(height)
            self.background_opacity_input.blockSignals(True)
            self.background_opacity_input.setValue(int(layout.get("background_opacity", DEFAULT_CARD_OPACITY)))
            self.background_opacity_input.blockSignals(False)
            self._set_font_scale_label(float(layout.get("font_scale", DEFAULT_FONT_SCALE)))
            self.enabled_toggle.blockSignals(True)
            self.enabled_toggle.setChecked(bool(layout.get("enabled", False)))
            self.enabled_toggle.blockSignals(False)
        self.preview_widget.update()

    def _handle_session_telemetry_changed(
        self,
        telemetry: TelemetryStore,
        source_path,
    ) -> None:
        self.preview_time_slider.setMaximum(int(round(telemetry.duration_sec * 1000)))
        self.preview_widget.set_preview_time(0.0)

    def _handle_preview_time_changed(self, value: int) -> None:
        preview_time_sec = value / 1000.0
        self.preview_time_label.setText(
            app_text("preview_time_value").format(seconds=preview_time_sec)
        )
        self.preview_widget.set_preview_time(preview_time_sec)

    def _handle_enabled_toggled(self, enabled: bool) -> None:
        widget_key = self._ensure_selected_widget_key()
        if widget_key is None:
            return
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        widget_layouts[widget_key]["enabled"] = enabled
        self._session.set_widget_layouts(widget_layouts)

    def _handle_background_opacity_changed(self, value: int) -> None:
        widget_key = self._ensure_selected_widget_key()
        if widget_key is None:
            return
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        widget_layouts[widget_key]["background_opacity"] = int(value)
        self._session.set_widget_layouts(widget_layouts)

    def _adjust_selected_font_scale(self, delta: float) -> None:
        widget_key = self._ensure_selected_widget_key()
        if widget_key is None:
            return
        widget_layouts = {
            name: dict(layout)
            for name, layout in self._session.widget_layouts.items()
        }
        if widget_key not in widget_layouts:
            return
        current = float(widget_layouts[widget_key].get("font_scale", DEFAULT_FONT_SCALE))
        next_scale = round(max(MIN_FONT_SCALE, current + delta), 2)
        layout = widget_layouts[widget_key]
        layout["font_scale"] = next_scale
        min_width, min_height = minimum_widget_dimensions(widget_key, font_scale=next_scale)
        layout["width"] = max(min_width, int(layout.get("width", min_width) or min_width))
        layout["height"] = max(min_height, int(layout.get("height", min_height) or min_height))
        self._set_font_scale_label(next_scale)
        self._session.set_widget_layouts(widget_layouts)

    def _set_font_scale_label(self, font_scale: float) -> None:
        self.font_scale_label.setText(f"字体 {int(round(font_scale * 100))}%")

    def _handle_preview_widget_selected(self, widget_key: object) -> None:
        if not isinstance(widget_key, str):
            self.widget_list.clearSelection()
            self._selected_widget_key = None
            return
        display_name = widget_display_name(widget_key)
        self.select_widget(display_name)

    def _ensure_selected_widget_key(self) -> str | None:
        if self._selected_widget_key in self._session.widget_layouts:
            return self._selected_widget_key
        current_item = self.widget_list.currentItem()
        if current_item is None:
            return None
        item_key = current_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(item_key, str) or item_key not in self._session.widget_layouts:
            return None
        self._selected_widget_key = item_key
        self.preview_widget.set_selected_widget_key(item_key)
        if not current_item.isSelected():
            self.widget_list.blockSignals(True)
            self.widget_list.setCurrentItem(current_item)
            self.widget_list.blockSignals(False)
        return item_key

    def _selected_widget_key_from_ui_value(self, widget_name: str) -> str | None:
        current_item = self.widget_list.currentItem()
        if current_item is not None and current_item.text() == widget_name:
            item_key = current_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(item_key, str):
                return item_key
        resolved_key = widget_key_from_display_name(widget_name)
        if resolved_key in self._session.widget_layouts:
            return resolved_key
        return None

    def _list_item_for_widget_key(self, widget_key: str) -> QListWidgetItem | None:
        for index in range(self.widget_list.count()):
            item = self.widget_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == widget_key:
                return item
        return None

    def _widget_dimensions(self, widget_key: str) -> tuple[int, int]:
        for widget in build_widgets_from_session(self._session):
            if widget.widget_key == widget_key:
                return int(widget.width), int(widget.height)
        layout = self._session.widget_layouts.get(widget_key, {})
        return int(layout.get("width", 260)), int(layout.get("height", 110))
