from dataclasses import dataclass
from math import atan2, cos, radians, sin

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen


PRIMARY_TEXT = QColor("#f8f9fa")
SECONDARY_TEXT = QColor("#d9e4ec")
ACCENT = QColor("#2fb5ff")
THROTTLE = QColor("#4fe21f")
BRAKE = QColor("#ff3b30")
RPM_WARN = QColor("#ff9f0a")
PANEL_FILL_ALPHA = 0

BG = QColor(10, 16, 22, PANEL_FILL_ALPHA)
BORDER = QColor(47, 181, 255, 90)
TEXT = PRIMARY_TEXT
MUTED = SECONDARY_TEXT
GRID_A = QColor(20, 30, 38)
GRID_B = QColor(28, 40, 50)


@dataclass(frozen=True)
class HudCardMetrics:
    ratio: float
    title_px: int
    value_px: int
    subtitle_px: int
    underline_h: float
    accent_w: float
    accent_h: float
    accent_x1: float
    accent_x2: float
    title_h: float
    value_top: float
    value_h: float
    subtitle_h: float


def hud_card_metrics(*, width: float, height: float) -> HudCardMetrics:
    ratio = max(0.45, min(width / 260.0, height / 110.0))
    return HudCardMetrics(
        ratio=ratio,
        title_px=max(10, int(round(9 * ratio))),
        value_px=max(14, int(round(20 * ratio))),
        subtitle_px=max(9, int(round(8 * ratio))),
        underline_h=max(2.0, 3.0 * ratio),
        accent_w=max(28.0, width * 0.22),
        accent_h=max(16.0, 20.0 * ratio),
        accent_x1=max(36.0, width * 0.26),
        accent_x2=max(42.0, width * 0.28),
        title_h=max(16.0, 20.0 * ratio),
        value_top=max(18.0, 24.0 * ratio),
        value_h=max(24.0, height - max(22.0, 28.0 * ratio)),
        subtitle_h=max(12.0, 16.0 * ratio),
    )


def draw_checkerboard(painter: QPainter, rect: QRect, cell: int = 16) -> None:
    for row in range(0, rect.height(), cell):
        for col in range(0, rect.width(), cell):
            color = GRID_A if ((row // cell) + (col // cell)) % 2 == 0 else GRID_B
            painter.fillRect(rect.x() + col, rect.y() + row, cell, cell, color)


def draw_hud_card(
    painter: QPainter,
    rect: QRectF,
    *,
    title: str,
    value: str,
    subtitle: str = "",
    accent: QColor = ACCENT,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    metrics = hud_card_metrics(width=rect.width(), height=rect.height())
    underline_rect = QRectF(rect.x(), rect.y() + metrics.title_h, metrics.accent_w, metrics.underline_h)
    painter.fillRect(underline_rect, accent)

    painter.setPen(QPen(accent, metrics.underline_h))
    painter.drawLine(
        int(rect.x() + metrics.accent_x1),
        int(rect.y() + 2),
        int(rect.x() + metrics.accent_x2),
        int(rect.y() + metrics.accent_h),
    )

    painter.setPen(MUTED)
    title_font = QFont("Segoe UI", QFont.Weight.Bold)
    title_font.setPixelSize(metrics.title_px)
    title_font.setItalic(True)
    title_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
    painter.setFont(title_font)
    painter.drawText(QRectF(rect.x(), rect.y(), rect.width(), metrics.title_h), title.upper())

    value_rect = QRectF(rect.x(), rect.y() + metrics.value_top, rect.width(), metrics.value_h)
    shadow_font = QFont("Segoe UI", QFont.Weight.Black)
    shadow_font.setPixelSize(metrics.value_px)
    shadow_font.setItalic(True)
    painter.setFont(shadow_font)
    painter.setPen(QColor(0, 0, 0, 130))
    shadow_offset = max(1.0, metrics.ratio)
    painter.drawText(value_rect.translated(shadow_offset, shadow_offset), value)

    painter.setPen(TEXT)
    painter.drawText(value_rect, value)

    if subtitle:
        painter.setPen(MUTED)
        subtitle_font = QFont("Segoe UI", QFont.Weight.DemiBold)
        subtitle_font.setPixelSize(metrics.subtitle_px)
        painter.setFont(subtitle_font)
        painter.drawText(
            QRectF(rect.x(), rect.y() + rect.height() - metrics.subtitle_h, rect.width(), metrics.subtitle_h),
            subtitle,
        )
    painter.restore()


def draw_heading_gauge(painter: QPainter, rect: QRectF, heading_deg: float | None) -> None:
    if heading_deg is None:
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    size = min(rect.width(), rect.height())
    radius = max(18.0, size * 0.22)
    center_x = rect.right() - max(radius + 10.0, rect.width() * 0.16)
    center_y = rect.y() + max(radius + 10.0, rect.height() * 0.38)
    painter.setPen(QPen(BORDER, max(1.0, radius * 0.05)))
    painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))
    angle = radians(heading_deg - 90.0)
    end_x = center_x + cos(angle) * (radius - max(3.0, radius * 0.16))
    end_y = center_y + sin(angle) * (radius - max(3.0, radius * 0.16))
    painter.setPen(QPen(ACCENT, max(1.6, radius * 0.09)))
    painter.drawLine(center_x, center_y, end_x, end_y)
    painter.restore()


def draw_g_ball(painter: QPainter, rect: QRectF, long_g: float | None, lat_g: float | None) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    center_x = rect.center().x()
    center_y = rect.center().y()
    radius = max(26.0, min(rect.width(), rect.height()) * 0.38)
    painter.setPen(QPen(BORDER, max(1.0, radius * 0.04)))
    painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))
    painter.setPen(QPen(MUTED, max(1.0, radius * 0.03), Qt.PenStyle.DashLine))
    painter.drawLine(center_x - radius, center_y, center_x + radius, center_y)
    painter.drawLine(center_x, center_y - radius, center_x, center_y + radius)
    travel = radius * 0.62
    dot_x = center_x + min(max((lat_g or 0.0) * travel, -travel), travel)
    dot_y = center_y - min(max((long_g or 0.0) * travel, -travel), travel)
    painter.setBrush(ACCENT)
    painter.setPen(QPen(TEXT, max(1.0, radius * 0.04)))
    dot_radius = max(5.0, radius * 0.12)
    painter.drawEllipse(QRectF(dot_x - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2))
    painter.restore()


def heading_text(heading_deg: float | None) -> str:
    if heading_deg is None:
        return "--"
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int(((heading_deg % 360.0) + 22.5) // 45) % len(directions)
    return directions[index]


def format_g(value: float | None) -> str:
    return "--" if value is None else f"{value:+.2f} g"


def track_normalize(points: list[tuple[float, float]], rect: QRectF) -> list[tuple[float, float]]:
    if not points:
        return []
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    scale = min((rect.width() - 28) / width, (rect.height() - 28) / height)
    normalized: list[tuple[float, float]] = []
    for x, y in points:
        normalized.append(
            (
                rect.x() + 14 + (x - min_x) * scale,
                rect.y() + rect.height() - 14 - (y - min_y) * scale,
            )
        )
    return normalized
