from abc import ABC, abstractmethod

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame


class OverlayWidget(ABC):
    widget_key = "widget"
    display_name = "Widget"
    default_width = 260
    default_height = 110

    def __init__(self, *, x: int, y: int, width: int | None = None, height: int | None = None) -> None:
        self.x = x
        self.y = y
        self.width = self.default_width if width is None else width
        self.height = self.default_height if height is None else height

    @abstractmethod
    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        raise NotImplementedError

    def text_rect(self, width: int = 240, height: int = 44) -> QRect:
        return QRect(self.x, self.y, width, height)

    def bounds_rect(self) -> QRectF:
        return QRectF(self.x, self.y, self.width, self.height)

    def scale_ratio(self, *, base_width: int | None = None, base_height: int | None = None) -> float:
        width_ratio = self.width / max(base_width or self.default_width, 1)
        height_ratio = self.height / max(base_height or self.default_height, 1)
        return max(0.45, min(width_ratio, height_ratio))

    def font_px(self, px: int, *, minimum: int = 10) -> int:
        return max(minimum, int(round(px * self.scale_ratio())))

    def length_px(self, value: float, *, minimum: float = 0.0) -> float:
        return max(minimum, value * self.scale_ratio())
