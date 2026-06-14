from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import (
    NEGATIVE,
    POSITIVE,
    TEXT,
    draw_card_background,
    draw_card_title,
    draw_heading_arrow,
    hud_card_layout,
    track_normalize,
)


class MiniTrackWidget(OverlayWidget):
    widget_key = "mini_track"
    display_name = widget_display_name("mini_track")
    card_title = "迷你赛道地图"
    default_width = 392
    default_height = 122
    supports_static_render = True

    def __init__(
        self,
        *,
        x: int,
        y: int,
        track_points: list[tuple[float, float]] | None = None,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, background_opacity=background_opacity, font_scale=font_scale)
        self._track_points = track_points or []
        self._bounds = _point_bounds(self._track_points)
        self._cached_inner_key: tuple[float, float, float, float] | None = None
        self._cached_path: QPainterPath | None = None
        self._cached_scale = 1.0

    def render_static(self, painter: QPainter) -> None:
        rect = self.bounds_rect()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_card_background(painter, rect, **self.background_kwargs())
        layout = self._layout()
        draw_card_title(painter, layout, self.card_title)
        inner_rect = self._track_inner_rect()
        painter.setPen(QPen(self._track_panel_border_color(), 1.0))
        painter.setBrush(self._track_panel_fill_color())
        painter.drawRoundedRect(inner_rect, 4.0, 4.0)

        if not self._track_points:
            painter.restore()
            return

        path = self._track_path(inner_rect)
        if path is None:
            painter.restore()
            return

        painter.setPen(QPen(TEXT, self.length_px(2.0, minimum=1.2)))
        painter.drawPath(path)
        painter.restore()

    def render_dynamic(self, painter: QPainter, frame: TelemetryFrame) -> None:
        inner_rect = self._track_inner_rect()
        if self._track_points:
            self._track_path(inner_rect)
        if frame.x_m is not None and frame.y_m is not None:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            current = self._normalize_current_point(frame.x_m, frame.y_m, inner_rect)
            if current is not None:
                current_x, current_y = current
                radius = self.marker_radius()
                painter.setPen(QPen(TEXT, self.length_px(1.0, minimum=1.0)))
                painter.setBrush(NEGATIVE)
                painter.drawEllipse(
                    QRectF(current_x - radius, current_y - radius, radius * 2.0, radius * 2.0)
                )
                draw_heading_arrow(
                    painter,
                    center_x=current_x,
                    center_y=current_y,
                    heading_deg=frame.heading_deg,
                    length=self.length_px(14.0, minimum=8.0),
                    color=POSITIVE,
                )
            painter.restore()

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        self.render_static(painter)
        self.render_dynamic(painter, frame)

    def _layout(self):
        return hud_card_layout(self.bounds_rect(), font_scale=self.effective_font_scale)

    def _track_inner_rect(self) -> QRectF:
        layout = self._layout()
        return layout.value_rect.united(layout.visual_rect).adjusted(0.0, 4.0, 0.0, 0.0)

    def marker_radius(self) -> float:
        return self.length_px(10.0, minimum=6.0)

    def _track_panel_fill_color(self) -> QColor:
        alpha = int(round(max(0, min(self.background_opacity, 100)) / 100.0 * 220))
        return QColor(16, 29, 41, alpha)

    def _track_panel_border_color(self) -> QColor:
        alpha = int(round(max(0, min(self.background_opacity, 100)) / 100.0 * 28))
        return QColor(255, 255, 255, alpha)

    def _normalize_current_point(
        self,
        x_m: float,
        y_m: float,
        rect: QRectF,
    ) -> tuple[float, float] | None:
        if self._bounds is None:
            return None
        min_x, _, min_y, _ = self._bounds
        scale = self._cached_scale
        return (
            rect.x() + 14 + (x_m - min_x) * scale,
            rect.y() + rect.height() - 14 - (y_m - min_y) * scale,
        )

    def _track_path(self, rect: QRectF) -> QPainterPath | None:
        key = (rect.x(), rect.y(), rect.width(), rect.height())
        if self._cached_path is not None and self._cached_inner_key == key:
            return self._cached_path
        normalized = track_normalize(self._track_points, rect)
        if len(normalized) < 2 or self._bounds is None:
            self._cached_path = None
            self._cached_inner_key = key
            return None
        min_x, max_x, min_y, max_y = self._bounds
        width = max(max_x - min_x, 1.0)
        height = max(max_y - min_y, 1.0)
        self._cached_scale = min((rect.width() - 28) / width, (rect.height() - 28) / height)
        path = QPainterPath()
        path.moveTo(*normalized[0])
        for point in normalized[1:]:
            path.lineTo(*point)
        self._cached_path = path
        self._cached_inner_key = key
        return path


def _point_bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    return (
        min(point[0] for point in points),
        max(point[0] for point in points),
        min(point[1] for point in points),
        max(point[1] for point in points),
    )
