from abc import ABC, abstractmethod
from math import ceil

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.widgets.hud_theme import DEFAULT_CARD_OPACITY, DEFAULT_FONT_SCALE, clamp_font_scale


class OverlayWidget(ABC):
    widget_key = "widget"
    display_name = "Widget"
    default_width = 260
    default_height = 110

    def __init__(
        self,
        *,
        x: int,
        y: int,
        width: int | None = None,
        height: int | None = None,
        background_opacity: int | None = None,
        font_scale: float | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.default_width if width is None else width
        self.height = self.default_height if height is None else height
        self.background_opacity = DEFAULT_CARD_OPACITY if background_opacity is None else _clamp_opacity(background_opacity)
        self.font_scale = clamp_font_scale(font_scale)
        self.visual_scale = 1.0

    @abstractmethod
    def render(self, painter: QPainter, frame: TelemetryFrame) -> None:
        raise NotImplementedError

    def text_rect(self, width: int = 240, height: int = 44) -> QRect:
        return QRect(self.x, self.y, width, height)

    def bounds_rect(self) -> QRectF:
        return QRectF(self.x, self.y, self.width, self.height)

    def scale_ratio(self, *, base_width: int | None = None, base_height: int | None = None) -> float:
        return self.effective_font_scale

    @property
    def effective_font_scale(self) -> float:
        return self.font_scale * max(0.01, float(getattr(self, "visual_scale", 1.0)))

    def font_px(self, px: int, *, minimum: int = 10) -> int:
        return max(_scaled_minimum(minimum, self.visual_scale), int(round(px * self.effective_font_scale)))

    def length_px(self, value: float, *, minimum: float = 0.0) -> float:
        visual_scale = max(0.01, float(getattr(self, "visual_scale", 1.0)))
        return max(float(minimum) * visual_scale, value * visual_scale)

    @classmethod
    def minimum_dimensions(cls, *, font_scale: float = DEFAULT_FONT_SCALE) -> tuple[int, int]:
        scale = clamp_font_scale(font_scale)
        return (
            max(cls.default_width, int(ceil(cls.default_width * scale))),
            max(cls.default_height, int(ceil(cls.default_height * scale))),
        )

    def minimum_size(self) -> tuple[int, int]:
        return self.minimum_dimensions(font_scale=self.font_scale)

    def background_kwargs(self) -> dict[str, int]:
        if self.background_opacity == DEFAULT_CARD_OPACITY:
            return {}
        return {"background_opacity": self.background_opacity}

    def text_kwargs(self) -> dict[str, float]:
        effective_font_scale = self.effective_font_scale
        if effective_font_scale == DEFAULT_FONT_SCALE:
            return {}
        return {"font_scale": effective_font_scale}

    def card_kwargs(self) -> dict[str, int | float]:
        return {**self.background_kwargs(), **self.text_kwargs()}


def _clamp_opacity(value: int) -> int:
    return max(0, min(int(value), 100))


def _scaled_minimum(value: int, visual_scale: float) -> int:
    scale = max(0.01, float(visual_scale))
    return max(1, int(round(value * scale)))
