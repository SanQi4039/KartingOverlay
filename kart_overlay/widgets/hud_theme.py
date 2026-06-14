from dataclasses import dataclass
from math import atan2, cos, isfinite, radians, sin

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen


PAGE_BG = QColor("#02070d")
PRIMARY_TEXT = QColor("#f8f9fa")
SECONDARY_TEXT = QColor("#8da9c4")
ACCENT = QColor("#2fb5ff")
POSITIVE = QColor("#4fe21f")
NEGATIVE = QColor("#ff3b30")
WARNING = QColor("#ffb800")
PURPLE = QColor("#a66cff")
THROTTLE = POSITIVE
BRAKE = NEGATIVE
RPM_WARN = WARNING
PANEL_FILL_ALPHA = 245
DEFAULT_CARD_OPACITY = round(PANEL_FILL_ALPHA / 255 * 100)
DEFAULT_FONT_SCALE = 1.0
MIN_FONT_SCALE = 0.7
CARD_RADIUS = 6.0
CARD_PADDING_X = 12.0
CARD_PADDING_Y = 8.0
CARD_GAP = 12

CARD_FILL = QColor(10, 16, 22, PANEL_FILL_ALPHA)
CARD_BORDER = QColor("#13202d")
GAUGE_TRACK = QColor("#0f1926")
GAUGE_EMPTY = QColor(255, 255, 255, 36)
BG = CARD_FILL
BORDER = CARD_BORDER
TEXT = PRIMARY_TEXT
MUTED = SECONDARY_TEXT
GRID_A = QColor(20, 30, 38)
GRID_B = QColor(28, 40, 50)


@dataclass(frozen=True)
class HudCardMetrics:
    ratio: float
    value_px: int
    value_h: float


@dataclass(frozen=True)
class HudCardLayout:
    ratio: float
    inner: QRectF
    title_rect: QRectF
    value_rect: QRectF
    visual_rect: QRectF
    footer_rect: QRectF


def hud_card_metrics(*, width: float, height: float, font_scale: float = DEFAULT_FONT_SCALE) -> HudCardMetrics:
    ratio = effective_visual_ratio(font_scale)
    return HudCardMetrics(
        ratio=ratio,
        value_px=_scaled_font_px(31, ratio, minimum=18),
        value_h=max(_scaled_length(26.0, ratio), 42.0 * ratio),
    )


def draw_checkerboard(painter: QPainter, rect: QRect, cell: int = 16) -> None:
    for y in range(rect.top(), rect.bottom() + 1, cell):
        for x in range(rect.left(), rect.right() + 1, cell):
            col = ((x - rect.left()) // cell + (y - rect.top()) // cell) % 2
            painter.fillRect(QRect(x, y, cell, cell), GRID_A if col == 0 else GRID_B)


def hud_card_layout(rect: QRectF, *, font_scale: float = DEFAULT_FONT_SCALE) -> HudCardLayout:
    metrics = hud_card_metrics(width=rect.width(), height=rect.height(), font_scale=font_scale)
    ratio = metrics.ratio
    pad_x = CARD_PADDING_X * ratio
    pad_y = CARD_PADDING_Y * ratio
    inner = rect.adjusted(pad_x, pad_y, -pad_x, -pad_y)
    title_h = max(_scaled_length(11.0, ratio), 15.0 * ratio)
    value_h = metrics.value_h
    footer_h = max(_scaled_length(10.0, ratio), 14.0 * ratio)
    title_rect = QRectF(inner.x(), inner.y(), inner.width(), title_h)
    value_rect = QRectF(inner.x(), title_rect.bottom() + 2.0 * ratio, inner.width(), value_h)
    footer_rect = QRectF(inner.x(), inner.bottom() - footer_h, inner.width(), footer_h)
    visual_top = value_rect.bottom() + 5.0 * ratio
    visual_bottom = footer_rect.top() - 2.0 * ratio
    visual_rect = QRectF(inner.x(), visual_top, inner.width(), max(_scaled_length(4.0, ratio), visual_bottom - visual_top))
    return HudCardLayout(
        ratio=ratio,
        inner=inner,
        title_rect=title_rect,
        value_rect=value_rect,
        visual_rect=visual_rect,
        footer_rect=footer_rect,
    )


def draw_hud_card(
    painter: QPainter,
    rect: QRectF,
    *,
    title: str,
    value: str,
    subtitle: str = "",
    accent: QColor = ACCENT,
    background_opacity: int | None = None,
    font_scale: float = DEFAULT_FONT_SCALE,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_card_background(painter, rect, background_opacity=background_opacity)
    layout = hud_card_layout(rect, font_scale=font_scale)
    if title:
        draw_card_title(painter, layout, title)
    draw_value_with_unit(painter, layout, value=value, unit=subtitle, color=accent)
    painter.restore()


def card_fill_for_opacity(background_opacity: int | float | None = None) -> QColor:
    if background_opacity is None:
        return QColor(CARD_FILL)
    percent = max(0.0, min(float(background_opacity), 100.0))
    alpha = int(round(percent / 100.0 * 255))
    return QColor(CARD_FILL.red(), CARD_FILL.green(), CARD_FILL.blue(), alpha)


def clamp_font_scale(font_scale: int | float | None = None) -> float:
    if font_scale is None:
        return DEFAULT_FONT_SCALE
    return max(MIN_FONT_SCALE, float(font_scale))


def effective_visual_ratio(font_scale: int | float | None = None) -> float:
    if font_scale is None:
        return DEFAULT_FONT_SCALE
    return max(0.01, float(font_scale))


def _scaled_font_px(base_px: int, ratio: float, *, minimum: int) -> int:
    if ratio < MIN_FONT_SCALE:
        return max(1, int(round(base_px * ratio)))
    return max(minimum, int(round(base_px * ratio)))


def _scaled_length(base: float, ratio: float) -> float:
    if ratio < MIN_FONT_SCALE:
        return max(1.0, base * ratio)
    return base


def card_border_for_opacity(background_opacity: int | float | None = None) -> QColor:
    if background_opacity is None:
        return QColor(CARD_BORDER)
    alpha = card_fill_for_opacity(background_opacity).alpha()
    return QColor(CARD_BORDER.red(), CARD_BORDER.green(), CARD_BORDER.blue(), alpha)


def draw_card_background(painter: QPainter, rect: QRectF, *, background_opacity: int | float | None = None) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(rect.adjusted(1.0, 1.0, -1.0, -1.0), CARD_RADIUS, CARD_RADIUS)
    painter.fillPath(path, card_fill_for_opacity(background_opacity))
    painter.setPen(QPen(card_border_for_opacity(background_opacity), 1.0))
    painter.drawPath(path)
    painter.restore()


def draw_card_title(painter: QPainter, layout: HudCardLayout, title: str) -> None:
    painter.save()
    font = QFont("Roboto Mono")
    font.setPixelSize(_scaled_font_px(12, layout.ratio, minimum=9))
    painter.setFont(font)
    painter.setPen(MUTED)
    painter.drawText(layout.title_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, title)
    painter.restore()


def draw_value_with_unit(
    painter: QPainter,
    layout: HudCardLayout,
    *,
    value: str,
    unit: str = "",
    color: QColor = TEXT,
) -> None:
    painter.save()
    font = QFont("Roboto Mono", QFont.Weight.Bold)
    font.setPixelSize(_scaled_font_px(31, layout.ratio, minimum=18))
    painter.setFont(font)
    painter.setPen(color)
    value_w = painter.fontMetrics().horizontalAdvance(value)
    if not unit:
        painter.drawText(layout.value_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, value)
        painter.restore()
        return

    unit_font = QFont("Roboto Mono")
    unit_font.setPixelSize(_scaled_font_px(12, layout.ratio, minimum=9))
    gap = 5 * layout.ratio
    painter.setFont(unit_font)
    unit_w = painter.fontMetrics().horizontalAdvance(unit)
    group_w = value_w + gap + unit_w
    group_x = layout.value_rect.x() + max(0.0, (layout.value_rect.width() - group_w) / 2.0)
    painter.setFont(font)
    painter.setPen(color)
    painter.drawText(
        QRectF(group_x, layout.value_rect.y(), value_w, layout.value_rect.height()),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        value,
    )
    painter.setFont(unit_font)
    painter.setPen(MUTED)
    unit_x = group_x + value_w + gap
    painter.drawText(
        QRectF(unit_x, layout.value_rect.y() + 6 * layout.ratio, unit_w + 4 * layout.ratio, layout.value_rect.height()),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        unit,
    )
    painter.restore()


def draw_metric_card(
    painter: QPainter,
    rect: QRectF,
    *,
    title: str,
    value: str,
    unit: str = "",
    value_color: QColor = TEXT,
    progress: float | None = None,
    progress_color: QColor = ACCENT,
    tick_labels: tuple[str, ...] = (),
    footer_text: str = "",
    background_opacity: int | None = None,
    font_scale: float = DEFAULT_FONT_SCALE,
) -> None:
    show_progress_visual = metric_progress_visible(unit=unit, tick_labels=tick_labels)
    draw_metric_card_static(
        painter,
        rect,
        title=title,
        unit=unit,
        tick_labels=tick_labels,
        background_opacity=background_opacity,
        font_scale=font_scale,
    )
    draw_metric_card_dynamic(
        painter,
        rect,
        value=value,
        unit=unit,
        value_color=value_color,
        progress=progress,
        progress_color=progress_color,
        tick_labels=tick_labels,
        footer_text="" if tick_labels and show_progress_visual else footer_text,
        font_scale=font_scale,
    )


def metric_progress_visible(*, unit: str = "", tick_labels: tuple[str, ...] = ()) -> bool:
    return not (unit == "km/h" and tick_labels == ("0", "90", "180"))


def draw_metric_card_static(
    painter: QPainter,
    rect: QRectF,
    *,
    title: str,
    unit: str = "",
    tick_labels: tuple[str, ...] = (),
    background_opacity: int | None = None,
    font_scale: float = DEFAULT_FONT_SCALE,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_card_background(painter, rect, background_opacity=background_opacity)
    layout = hud_card_layout(rect, font_scale=font_scale)
    draw_card_title(painter, layout, title)
    if tick_labels and metric_progress_visible(unit=unit, tick_labels=tick_labels):
        draw_scale_labels(painter, layout.footer_rect, tick_labels)
    painter.restore()


def draw_metric_card_dynamic(
    painter: QPainter,
    rect: QRectF,
    *,
    value: str,
    unit: str = "",
    value_color: QColor = TEXT,
    progress: float | None = None,
    progress_color: QColor = ACCENT,
    tick_labels: tuple[str, ...] = (),
    footer_text: str = "",
    font_scale: float = DEFAULT_FONT_SCALE,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    layout = hud_card_layout(rect, font_scale=font_scale)
    draw_value_with_unit(painter, layout, value=value, unit=unit, color=value_color)
    show_progress_visual = metric_progress_visible(unit=unit, tick_labels=tick_labels)
    if progress is not None and show_progress_visual:
        draw_linear_gauge(painter, layout.visual_rect, progress=progress, color=progress_color)
    if footer_text:
        draw_footer_text(painter, layout.footer_rect, footer_text, color=MUTED)
    painter.restore()


def draw_linear_gauge(painter: QPainter, rect: QRectF, *, progress: float, color: QColor = ACCENT) -> None:
    painter.save()
    bar_h = max(4.0, min(7.0, rect.height() * 0.42))
    bar_rect = QRectF(rect.x(), rect.center().y() - bar_h / 2, rect.width(), bar_h)
    painter.setPen(QPen(QColor(255, 255, 255, 52), 1.0))
    painter.setBrush(GAUGE_TRACK)
    painter.drawRoundedRect(bar_rect, bar_h / 2, bar_h / 2)
    clamped = max(0.0, min(progress, 1.0))
    if clamped > 0.0:
        fill_rect = QRectF(bar_rect.x(), bar_rect.y(), bar_rect.width() * clamped, bar_rect.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(fill_rect, bar_h / 2, bar_h / 2)
    painter.restore()


def draw_scale_labels(painter: QPainter, rect: QRectF, labels: tuple[str, ...]) -> None:
    painter.save()
    font = QFont("Roboto Mono")
    font.setPixelSize(max(9, int(round(rect.height() * 0.78))))
    painter.setFont(font)
    painter.setPen(MUTED)
    if len(labels) <= 1:
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, labels[0] if labels else "")
    elif len(labels) == 2:
        painter.drawText(QRectF(rect.x(), rect.y(), rect.width() / 2, rect.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, labels[0])
        painter.drawText(QRectF(rect.center().x(), rect.y(), rect.width() / 2, rect.height()), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, labels[1])
    else:
        painter.drawText(QRectF(rect.x(), rect.y(), rect.width() / 3, rect.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, labels[0])
        painter.drawText(QRectF(rect.x() + rect.width() / 3, rect.y(), rect.width() / 3, rect.height()), Qt.AlignmentFlag.AlignCenter, labels[1])
        painter.drawText(QRectF(rect.x() + rect.width() * 2 / 3, rect.y(), rect.width() / 3, rect.height()), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, labels[-1])
    painter.restore()


def draw_footer_text(painter: QPainter, rect: QRectF, text: str, *, color: QColor = MUTED) -> None:
    painter.save()
    font = QFont("Roboto Mono")
    font.setPixelSize(max(9, int(round(rect.height() * 0.78))))
    painter.setFont(font)
    painter.setPen(color)
    painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, text)
    painter.restore()


def draw_trend_bars(painter: QPainter, rect: QRectF, *, color: QColor, count: int = 22) -> None:
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    gap = max(1.0, rect.width() / (count * 3))
    bar_w = max(2.0, (rect.width() - gap * (count - 1)) / count)
    for index in range(count):
        wave = 0.35 + ((index * 7) % 11) / 18
        h = max(2.0, rect.height() * min(wave, 1.0))
        x = rect.x() + index * (bar_w + gap)
        y = rect.bottom() - h
        painter.setBrush(color)
        painter.drawRect(QRectF(x, y, bar_w, h))
    painter.restore()


def draw_center_g_bar(painter: QPainter, rect: QRectF, *, value: float | None, color_positive: QColor = NEGATIVE, color_negative: QColor = ACCENT) -> None:
    painter.save()
    bar_h = max(5.0, rect.height() * 0.34)
    bar_rect = QRectF(rect.x(), rect.center().y() - bar_h / 2, rect.width(), bar_h)
    painter.setPen(QPen(QColor(255, 255, 255, 44), 1.0))
    painter.setBrush(GAUGE_TRACK)
    painter.drawRect(bar_rect)
    center_x = bar_rect.center().x()
    painter.setPen(QPen(MUTED, 1.0))
    painter.drawLine(center_x, bar_rect.top() - 2.0, center_x, bar_rect.bottom() + 2.0)
    if value is not None and isfinite(value):
        normalized = max(-1.0, min(value / 2.0, 1.0))
        if normalized >= 0:
            fill = QRectF(center_x, bar_rect.y(), (bar_rect.width() / 2) * normalized, bar_rect.height())
            color = color_positive
        else:
            fill_w = (bar_rect.width() / 2) * abs(normalized)
            fill = QRectF(center_x - fill_w, bar_rect.y(), fill_w, bar_rect.height())
            color = color_negative
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(fill)
        painter.setPen(QPen(TEXT, 1.2))
        marker_x = center_x + (bar_rect.width() / 2) * normalized
        painter.drawLine(marker_x, bar_rect.top() - 4.0, marker_x, bar_rect.bottom() + 4.0)
    painter.restore()


def draw_mini_line_chart(painter: QPainter, rect: QRectF, *, color: QColor = ACCENT) -> None:
    painter.save()
    path = QPainterPath()
    points = 18
    for index in range(points):
        x = rect.x() + rect.width() * index / max(points - 1, 1)
        y_ratio = 0.52 + (((index * 5) % 9) - 4) / 16
        y = rect.y() + rect.height() * max(0.1, min(y_ratio, 0.9))
        if index == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    painter.setPen(QPen(QColor(255, 255, 255, 35), 1.0, Qt.PenStyle.DashLine))
    painter.drawLine(rect.left(), rect.center().y(), rect.right(), rect.center().y())
    painter.setPen(QPen(color, max(1.2, rect.height() * 0.08)))
    painter.drawPath(path)
    painter.restore()


def draw_heading_ticks(painter: QPainter, rect: QRectF, *, heading_deg: float | None, color: QColor = POSITIVE) -> None:
    painter.save()
    count = 9
    tick_gap = rect.width() / max(count + 1, 1)
    center = rect.center().x()
    active = 0 if heading_deg is None or not isfinite(heading_deg) else int((heading_deg % 90) / 10) - 4
    for i in range(count):
        offset = i - count // 2
        x = rect.x() + tick_gap * (i + 1)
        h = rect.height() * (0.35 + abs(offset) * 0.04)
        tick_color = color if offset == active else QColor(color.red(), color.green(), color.blue(), 105)
        painter.setPen(QPen(tick_color, 1.2))
        painter.drawLine(x, rect.bottom(), x, rect.bottom() - h)
    painter.setPen(QPen(MUTED, 1.0))
    painter.drawLine(center, rect.bottom(), center, rect.bottom() - rect.height() * 0.85)
    painter.restore()


def draw_lap_progress_card(
    painter: QPainter,
    rect: QRectF,
    *,
    title: str,
    value: str,
    unit: str,
    progress: float | None,
    min_label: str,
    max_label: str,
    accent: QColor = POSITIVE,
    background_opacity: int | None = None,
    font_scale: float = DEFAULT_FONT_SCALE,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_card_background(painter, rect, background_opacity=background_opacity)
    layout = hud_card_layout(rect, font_scale=font_scale)
    draw_card_title(painter, layout, title)
    draw_value_with_unit(painter, layout, value=value, unit=unit)
    if progress is not None:
        draw_linear_gauge(painter, layout.visual_rect, progress=progress, color=accent)
        draw_scale_labels(painter, layout.footer_rect, (min_label, max_label))
    else:
        draw_linear_gauge(painter, layout.visual_rect, progress=0.0, color=accent)
        draw_scale_labels(painter, layout.footer_rect, (min_label, max_label) if max_label else (min_label,))
    painter.restore()


def draw_heading_gauge(painter: QPainter, rect: QRectF, heading_deg: float | None) -> None:
    if heading_deg is None or not isfinite(heading_deg):
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


def draw_heading_arrow(
    painter: QPainter,
    *,
    center_x: float,
    center_y: float,
    heading_deg: float | None,
    length: float,
    color: QColor = ACCENT,
) -> None:
    if heading_deg is None or not isfinite(heading_deg):
        return

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    angle = radians(heading_deg - 90.0)
    end_x = center_x + cos(angle) * length
    end_y = center_y + sin(angle) * length
    painter.setPen(QPen(color, max(1.2, length * 0.18)))
    painter.drawLine(center_x, center_y, end_x, end_y)
    painter.restore()


def heading_text(heading_deg: float | None) -> str:
    if heading_deg is None or not isfinite(heading_deg):
        return "--"
    directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
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
