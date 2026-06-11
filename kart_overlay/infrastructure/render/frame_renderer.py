from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame


class FrameRenderer:
    def __init__(self, *, canvas_size: tuple[int, int], widgets: list[object]) -> None:
        self._canvas_size = canvas_size
        self._widgets = widgets

    def render(self, frame: TelemetryFrame) -> QImage:
        image = QImage(self._canvas_size[0], self._canvas_size[1], QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            for widget in self._widgets:
                widget.render(painter, frame)
        finally:
            painter.end()

        return image

    def render_rgba_bytes(self, frame: TelemetryFrame) -> bytes:
        rgba_image = self.render(frame).convertToFormat(QImage.Format.Format_RGBA8888)
        buffer = rgba_image.bits()
        size = rgba_image.sizeInBytes()
        try:
            return bytes(buffer[:size])
        except TypeError:
            buffer.setsize(size)
            return bytes(buffer)
