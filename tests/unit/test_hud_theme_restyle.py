from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.widgets.best_lap_widget import BestLapWidget
from kart_overlay.widgets.coordinates_widget import CoordinatesWidget
from kart_overlay.widgets.g_force_widget import GForceWidget
from kart_overlay.widgets.heading_widget import HeadingWidget
from kart_overlay.widgets.hud_theme import ACCENT, CARD_BORDER, CARD_FILL, CARD_RADIUS, DEFAULT_CARD_OPACITY, PAGE_BG, PANEL_FILL_ALPHA, PRIMARY_TEXT, SECONDARY_TEXT, card_border_for_opacity, card_fill_for_opacity, draw_card_background, draw_card_title, draw_metric_card, draw_value_with_unit, heading_text, hud_card_layout, hud_card_metrics
from kart_overlay.widgets.lap_summary_widget import LapSummaryWidget
from kart_overlay.widgets.mini_track_widget import MiniTrackWidget
from kart_overlay.widgets.sector_state_widget import SectorStateWidget
from kart_overlay.widgets.speed_widget import SpeedWidget
from kart_overlay.widgets.timer_widget import TimerWidget
from kart_overlay.widgets.widget_factory import build_widgets_from_session
from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame


def test_hud_theme_matches_lightweight_sticker_palette():
    assert PAGE_BG == QColor("#02070d")
    assert CARD_FILL == QColor(10, 16, 22, 245)
    assert CARD_BORDER == QColor("#13202d")
    assert PRIMARY_TEXT == QColor("#f8f9fa")
    assert SECONDARY_TEXT == QColor("#8da9c4")
    assert ACCENT == QColor("#2fb5ff")
    assert PANEL_FILL_ALPHA > 0
    assert CARD_RADIUS == 6.0


def test_hud_theme_can_build_card_fill_with_custom_opacity_percent():
    assert DEFAULT_CARD_OPACITY == 96
    assert card_fill_for_opacity(0).alpha() == 0
    assert card_fill_for_opacity(50).alpha() == 128
    assert card_fill_for_opacity(100).alpha() == 255
    assert card_border_for_opacity(0).alpha() == 0
    assert card_border_for_opacity(50).alpha() == 128
    assert card_border_for_opacity(100).alpha() == 255


def test_card_background_opacity_controls_fill_and_border_pixels():
    image = QImage(80, 48, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    try:
        draw_card_background(painter, rect=image.rect(), background_opacity=0)
    finally:
        painter.end()

    assert max(image.pixelColor(x, y).alpha() for x in range(image.width()) for y in range(image.height())) == 0


def test_widget_factory_builds_chinese_named_widgets_for_overlay():
    session = ProjectSession()
    session.set_widget_layouts(
        {
            widget_key: {"enabled": True}
            for widget_key in session.widget_layouts
        }
    )

    display_names = {widget.display_name for widget in build_widgets_from_session(session)}

    assert "速度" in display_names
    assert "当前圈" in display_names
    assert "赛道图" in display_names
    assert "圈已行驶距离" in display_names


def test_hud_card_metrics_support_more_compact_vertical_padding():
    metrics = hud_card_metrics(width=280.0, height=110.0)

    assert metrics.value_px >= 28
    assert 30.0 <= metrics.value_h < 110.0


def test_hud_card_title_and_main_value_are_centered():
    layout = hud_card_layout(QRectF(0.0, 0.0, 180.0, 90.0))
    painter = _FakePainter()

    draw_card_title(painter, layout, "速度")
    draw_value_with_unit(painter, layout, value="88")

    assert painter.draw_calls[0]["alignment"] & Qt.AlignmentFlag.AlignHCenter
    assert painter.draw_calls[1]["alignment"] & Qt.AlignmentFlag.AlignHCenter


def test_metric_widgets_use_compact_sticker_sizing_family():
    assert SpeedWidget.default_width == 136
    assert SpeedWidget.default_height == 72
    assert TimerWidget.default_height == 122
    assert MiniTrackWidget.default_width > SpeedWidget.default_width
    assert CoordinatesWidget.default_height == 122


def test_speed_metric_card_skips_progress_visuals(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = {"gauge": 0}

    def fake_draw_linear_gauge(*args, **kwargs):
        calls["gauge"] += 1

    monkeypatch.setattr("kart_overlay.widgets.hud_theme.draw_linear_gauge", fake_draw_linear_gauge)
    image = QImage(220, 110, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    try:
        draw_metric_card(
            painter,
            SpeedWidget(x=0, y=0).bounds_rect(),
            title=SpeedWidget.display_name,
            value="88",
            unit="km/h",
            progress=0.5,
            tick_labels=("0", "90", "180"),
        )
    finally:
        painter.end()

    assert calls["gauge"] == 0
    app.quit()


def test_hud_copy_uses_clean_titles_and_labels():
    assert LapSummaryWidget.card_title == "圈次"
    assert BestLapWidget.card_title == "最佳圈"
    assert SectorStateWidget.card_title == "分段状态"
    assert MiniTrackWidget.card_title == "迷你赛道地图"
    assert HeadingWidget.card_title == "方向 / 航向"
    assert GForceWidget.label_text == "G 值 (横向)"


def test_metric_widgets_render_with_card_titles_units_and_visuals(monkeypatch):
    captured: list[dict[str, str]] = []
    captured_static: list[dict[str, str]] = []
    captured_dynamic: list[dict[str, str]] = []
    latest_static: dict[str, str] = {}

    def fake_draw_metric_card_static(_painter, _rect, **kwargs):
        captured_static.append(kwargs)
        latest_static.clear()
        latest_static.update(kwargs)

    def fake_draw_metric_card_dynamic(_painter, _rect, **kwargs):
        captured_dynamic.append(kwargs)
        combined = {}
        if "title" in latest_static:
            combined["title"] = latest_static["title"]
        combined.update(kwargs)
        captured.append(combined)

    monkeypatch.setattr("kart_overlay.widgets.speed_widget.draw_metric_card_static", fake_draw_metric_card_static)
    monkeypatch.setattr("kart_overlay.widgets.speed_widget.draw_metric_card_dynamic", fake_draw_metric_card_dynamic)
    monkeypatch.setattr("kart_overlay.widgets.timer_widget.draw_metric_card_static", fake_draw_metric_card_static)
    monkeypatch.setattr("kart_overlay.widgets.timer_widget.draw_metric_card_dynamic", fake_draw_metric_card_dynamic)

    SpeedWidget(x=0, y=0).render(
        None,
        TelemetryFrame(data_elapsed_sec=0.0, x_m=None, y_m=None, speed_kmh=88.8),
    )
    TimerWidget(x=0, y=0).render(
        None,
        TelemetryFrame(
            data_elapsed_sec=12.345,
            x_m=None,
            y_m=None,
            speed_kmh=None,
            lap_time_sec=12.345,
        ),
    )

    assert captured == [
        {
            "title": "速度",
            "value": "89",
            "unit": "km/h",
            "progress": 88.8 / 180.0,
            "progress_color": captured[0]["progress_color"],
            "tick_labels": ("0", "90", "180"),
        },
        {
            "title": "当前圈",
            "value": "12.345",
            "progress": 12.345 / 90.0,
            "progress_color": captured[1]["progress_color"],
        },
    ]


def test_heading_text_uses_chinese_compass_labels():
    assert heading_text(0.0) == "北"
    assert heading_text(45.0) == "东北"
    assert heading_text(90.0) == "东"
    assert heading_text(135.0) == "东南"
    assert heading_text(180.0) == "南"
    assert heading_text(225.0) == "西南"
    assert heading_text(270.0) == "西"
    assert heading_text(315.0) == "西北"


class _FakeFontMetrics:
    def horizontalAdvance(self, text: str) -> int:
        return len(text) * 10


class _FakePainter:
    def __init__(self) -> None:
        self.draw_calls: list[dict[str, object]] = []

    def save(self) -> None:
        pass

    def restore(self) -> None:
        pass

    def setFont(self, _font) -> None:
        pass

    def setPen(self, _pen) -> None:
        pass

    def fontMetrics(self):
        return _FakeFontMetrics()

    def drawText(self, rect, alignment, text) -> None:
        self.draw_calls.append({"rect": rect, "alignment": alignment, "text": text})
