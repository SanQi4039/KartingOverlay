from dataclasses import dataclass
from time import perf_counter

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame


@dataclass(frozen=True)
class FrameRenderResult:
    data: bytes
    render_ms: float
    to_bytes_ms: float

    @property
    def total_frame_ms(self) -> float:
        return self.render_ms + self.to_bytes_ms


class FrameRenderer:
    def __init__(self, *, canvas_size: tuple[int, int], widgets: list[object]) -> None:
        self._canvas_size = canvas_size
        self._widgets = widgets
        self._image = QImage(canvas_size[0], canvas_size[1], QImage.Format.Format_RGBA8888)
        self._static_widgets = [
            widget for widget in widgets if getattr(widget, "supports_static_render", False)
        ]
        self._dynamic_widgets = [
            widget for widget in widgets if getattr(widget, "supports_static_render", False)
        ]
        self._full_render_widgets = [
            widget for widget in widgets if not getattr(widget, "supports_static_render", False)
        ]
        self._static_layer: QImage | None = None

    def render(self, frame: TelemetryFrame) -> QImage:
        image = self._image
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            if self._static_widgets:
                painter.drawImage(0, 0, self._render_static_layer())
            for widget in self._full_render_widgets:
                widget.render(painter, frame)
            for widget in self._dynamic_widgets:
                widget.render_dynamic(painter, frame)
        finally:
            painter.end()

        return image

    def _render_static_layer(self) -> QImage:
        if self._static_layer is not None:
            return self._static_layer
        layer = QImage(self._canvas_size[0], self._canvas_size[1], QImage.Format.Format_RGBA8888)
        layer.fill(Qt.GlobalColor.transparent)
        painter = QPainter(layer)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            for widget in self._static_widgets:
                widget.render_static(painter)
        finally:
            painter.end()
        self._static_layer = layer
        return layer

    def render_rgba_bytes(self, frame: TelemetryFrame) -> bytes:
        return self.render_rgba_bytes_with_metrics(frame).data

    def render_rgba_bytes_with_metrics(self, frame: TelemetryFrame) -> FrameRenderResult:
        render_started = perf_counter()
        image = self.render(frame)
        render_ms = (perf_counter() - render_started) * 1000.0
        bytes_started = perf_counter()
        data = _qimage_to_rgba_bytes(image, width=self._canvas_size[0], height=self._canvas_size[1])
        to_bytes_ms = (perf_counter() - bytes_started) * 1000.0
        return FrameRenderResult(data=data, render_ms=render_ms, to_bytes_ms=to_bytes_ms)


def _qimage_to_rgba_bytes(image: QImage, *, width: int, height: int) -> bytes:
    rgba_image = image if image.format() == QImage.Format.Format_RGBA8888 else image.convertToFormat(
        QImage.Format.Format_RGBA8888
    )
    bytes_per_line = rgba_image.bytesPerLine()
    expected_stride = width * 4
    buffer = rgba_image.bits()
    size = rgba_image.sizeInBytes()
    if bytes_per_line == expected_stride:
        try:
            return bytes(buffer[:size])
        except TypeError:
            buffer.setsize(size)
            return bytes(buffer)
    try:
        raw = bytes(buffer[:size])
    except TypeError:
        buffer.setsize(size)
        raw = bytes(buffer)
    rows = [
        raw[row * bytes_per_line : row * bytes_per_line + expected_stride]
        for row in range(height)
    ]
    return b"".join(rows)
