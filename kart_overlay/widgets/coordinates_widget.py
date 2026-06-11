from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.ui.texts import widget_display_name
from kart_overlay.widgets.base import OverlayWidget
from kart_overlay.widgets.hud_theme import draw_hud_card


class CoordinatesWidget(OverlayWidget):
    widget_key = "coordinates"
    display_name = widget_display_name("coordinates")
    default_width = 340
    default_height = 110

    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        if frame.lat is None or frame.lon is None:
            value = "--"
            subtitle = "暂无定位"
        else:
            value = f"{frame.lat:.5f}, {frame.lon:.5f}"
            subtitle = "经纬度"
        draw_hud_card(
            painter,
            self.bounds_rect(),
            title="坐标",
            value=value,
            subtitle=subtitle,
        )
