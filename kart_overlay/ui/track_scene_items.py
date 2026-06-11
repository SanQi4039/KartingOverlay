from math import hypot

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem


class LineHandleItem(QGraphicsEllipseItem):
    def __init__(
        self,
        x: float,
        y: float,
        *,
        endpoint: str,
        accent: QColor,
        on_drag_started,
        on_dragged,
        on_drag_finished,
    ) -> None:
        super().__init__(-6.0, -6.0, 12.0, 12.0)
        self.endpoint = endpoint
        self._accent = QBrush(accent)
        self._active = QBrush(QColor("#8ecae6"))
        self._on_drag_started = on_drag_started
        self._on_dragged = on_dragged
        self._on_drag_finished = on_drag_finished
        self.setPos(x, y)
        self.setBrush(self._accent)
        self.setPen(QPen(Qt.GlobalColor.white, 1.2))
        self.setVisible(False)
        self.setZValue(20)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event) -> None:
        self.setBrush(self._active)
        self._on_drag_started(self.endpoint)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        scene_point = event.scenePos()
        self._on_dragged(self.endpoint, (scene_point.x(), scene_point.y()))
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.setBrush(self._accent)
        self._on_drag_finished()
        event.accept()


class EditableTimingLineItem(QGraphicsLineItem):
    def __init__(
        self,
        *,
        line_key: str,
        label: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: QColor,
        visual_style: str,
        on_selected,
        on_endpoint_pressed,
        on_endpoint_dragged,
        on_endpoint_released,
    ) -> None:
        super().__init__(x1, y1, x2, y2)
        self.line_key = line_key
        self.label = label
        self.visual_style = visual_style
        self.label_item = None
        self.is_selected_visual = False
        self._on_selected = on_selected
        self._on_endpoint_pressed = on_endpoint_pressed
        self._on_endpoint_dragged = on_endpoint_dragged
        self._on_endpoint_released = on_endpoint_released
        self._base_color = color
        self._base_pen = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self._hover_pen = QPen(color.lighter(130), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self._selected_pen = QPen(QColor("#8ecae6"), 3.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self.setPen(self._base_pen)
        self.setZValue(10)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)

        accent = QColor("#4cc9f0")
        self.start_handle = LineHandleItem(
            x1,
            y1,
            endpoint="start",
            accent=accent,
            on_drag_started=self._handle_drag_started,
            on_dragged=self._handle_dragged,
            on_drag_finished=self._on_endpoint_released,
        )
        self.end_handle = LineHandleItem(
            x2,
            y2,
            endpoint="end",
            accent=accent,
            on_drag_started=self._handle_drag_started,
            on_dragged=self._handle_dragged,
            on_drag_finished=self._on_endpoint_released,
        )

    @property
    def handle_count(self) -> int:
        return 2

    def attach_handles(self, scene) -> None:
        scene.addItem(self.start_handle)
        scene.addItem(self.end_handle)

    def set_selected_visual(self, selected: bool) -> None:
        self.is_selected_visual = selected
        self.setPen(self._selected_pen if selected else self._base_pen)
        self.start_handle.setVisible(selected)
        self.end_handle.setVisible(selected)
        self.update()

    def preview_endpoint(self, endpoint: str, x: float, y: float) -> None:
        line = self.line()
        if endpoint == "start":
            self.setLine(x, y, line.x2(), line.y2())
            self.start_handle.setPos(x, y)
        else:
            self.setLine(line.x1(), line.y1(), x, y)
            self.end_handle.setPos(x, y)
        self.update()

    def set_hover_visual(self, hovered: bool) -> None:
        if self.is_selected_visual:
            return
        self.setPen(self._hover_pen if hovered else self._base_pen)
        self.start_handle.setVisible(hovered)
        self.end_handle.setVisible(hovered)
        self.update()

    def select_line(self) -> None:
        self.set_selected_visual(True)
        self._on_selected(self.line_key, self.label)

    def hoverEnterEvent(self, event) -> None:
        self.set_hover_visual(True)
        event.accept()

    def hoverLeaveEvent(self, event) -> None:
        self.set_hover_visual(False)
        event.accept()

    def mousePressEvent(self, event) -> None:
        self.select_line()
        event.accept()

    def shape(self):
        path = QPainterPath(QPointF(self.line().x1(), self.line().y1()))
        path.lineTo(self.line().x2(), self.line().y2())
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.pen().widthF(), 10.0))
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_selected_visual:
            painter.setPen(QPen(self._selected_pen.color(), self._selected_pen.widthF(), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(self.line())

        if self.visual_style == "checker":
            self._paint_checker_line(painter)
        else:
            painter.setPen(QPen(self._base_color, self.pen().widthF(), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(self.line())
        painter.restore()

    def _paint_checker_line(self, painter: QPainter) -> None:
        line = self.line()
        x1 = line.x1()
        y1 = line.y1()
        x2 = line.x2()
        y2 = line.y2()
        length = hypot(x2 - x1, y2 - y1)
        if length <= 0.001:
            return
        dx = (x2 - x1) / length
        dy = (y2 - y1) / length
        segment = 10.0
        distance = 0.0
        index = 0
        while distance < length:
            end_distance = min(length, distance + segment)
            color = QColor("#ffffff") if index % 2 == 0 else QColor("#111111")
            painter.setPen(QPen(color, self.pen().widthF(), Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            painter.drawLine(
                QPointF(x1 + dx * distance, y1 + dy * distance),
                QPointF(x1 + dx * end_distance, y1 + dy * end_distance),
            )
            distance = end_distance
            index += 1

    def _handle_drag_started(self, endpoint: str) -> None:
        self.select_line()
        self._on_endpoint_pressed(self.line_key, self.label, endpoint)

    def _handle_dragged(self, endpoint: str, point: tuple[float, float]) -> None:
        self._on_endpoint_dragged(endpoint, point)
