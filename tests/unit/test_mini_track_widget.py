import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.widgets import mini_track_widget as mini_track_module
from kart_overlay.widgets.hud_theme import hud_card_layout, track_normalize
from kart_overlay.widgets.mini_track_widget import MiniTrackWidget


def test_mini_track_widget_renders_position_marker_without_heading():
    app = QApplication.instance() or QApplication([])
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )

    image = _render_widget(
        widget,
        TelemetryFrame(
            data_elapsed_sec=1.0,
            x_m=10.0,
            y_m=0.0,
            speed_kmh=40.0,
            heading_deg=None,
        ),
    )

    assert _alpha_scan(image) > 0
    app.quit()


def test_mini_track_widget_ignores_non_finite_heading_values():
    app = QApplication.instance() or QApplication([])
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )

    for value in (float("nan"), float("inf"), float("-inf")):
        image = _render_widget(
            widget,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=10.0,
                y_m=0.0,
                speed_kmh=40.0,
                heading_deg=value,
            ),
        )
        assert _alpha_scan(image) > 0
    app.quit()


def test_mini_track_widget_draws_heading_arrow_when_heading_is_available(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = {"arrow": 0}

    def fake_draw_heading_arrow(*args, **kwargs):
        calls["arrow"] += 1

    monkeypatch.setattr(mini_track_module, "draw_heading_arrow", fake_draw_heading_arrow, raising=False)

    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )
    _render_widget(
        widget,
        TelemetryFrame(
            data_elapsed_sec=1.0,
            x_m=10.0,
            y_m=0.0,
            speed_kmh=40.0,
            heading_deg=90.0,
        ),
    )

    assert calls["arrow"] == 1
    app.quit()


def test_mini_track_widget_anchors_marker_to_track_normalization(monkeypatch):
    app = QApplication.instance() or QApplication([])
    captured: dict[str, float] = {}

    def fake_draw_heading_arrow(*args, **kwargs):
        captured["center_x"] = kwargs["center_x"]
        captured["center_y"] = kwargs["center_y"]

    monkeypatch.setattr(mini_track_module, "draw_heading_arrow", fake_draw_heading_arrow, raising=False)

    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )
    _render_widget(
        widget,
        TelemetryFrame(
            data_elapsed_sec=1.0,
            x_m=10.0,
            y_m=0.0,
            speed_kmh=40.0,
            heading_deg=0.0,
        ),
    )

    layout = hud_card_layout(widget.bounds_rect())
    inner_rect = layout.value_rect.united(layout.visual_rect).adjusted(0.0, 4.0, 0.0, 0.0)
    expected_x, expected_y = track_normalize(widget._track_points, inner_rect)[1]

    assert captured["center_x"] == pytest.approx(expected_x)
    assert captured["center_y"] == pytest.approx(expected_y)
    app.quit()


def test_mini_track_widget_marker_radius_is_larger_and_visual_scale_aware():
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )

    assert widget.marker_radius() == pytest.approx(10.0)

    widget.visual_scale = 0.5

    assert widget.marker_radius() == pytest.approx(5.0)


def test_mini_track_widget_zero_background_opacity_hides_inner_track_panel():
    app = QApplication.instance() or QApplication([])
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[],
        background_opacity=0,
    )

    image = QImage(420, 260, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    try:
        widget.render_static(painter)
    finally:
        painter.end()

    assert image.pixelColor(216, 100).alpha() == 0
    app.quit()


def test_mini_track_widget_exposes_static_and_dynamic_render_paths():
    app = QApplication.instance() or QApplication([])
    widget = MiniTrackWidget(
        x=20,
        y=20,
        track_points=[(0.0, 0.0), (10.0, 0.0), (20.0, 10.0)],
    )
    static_image = QImage(420, 260, QImage.Format.Format_ARGB32_Premultiplied)
    static_image.fill(0)
    static_painter = QPainter(static_image)
    try:
        assert widget.supports_static_render is True
        widget.render_static(static_painter)
    finally:
        static_painter.end()

    dynamic_image = QImage(420, 260, QImage.Format.Format_ARGB32_Premultiplied)
    dynamic_image.fill(0)
    dynamic_painter = QPainter(dynamic_image)
    try:
        widget.render_dynamic(
            dynamic_painter,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=10.0,
                y_m=0.0,
                speed_kmh=40.0,
                heading_deg=None,
            ),
        )
    finally:
        dynamic_painter.end()

    assert _alpha_scan(static_image) > 0
    assert _alpha_scan(dynamic_image) > 0
    app.quit()


def _render_widget(widget: MiniTrackWidget, frame: TelemetryFrame) -> QImage:
    image = QImage(420, 260, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    try:
        widget.render(painter, frame)
    finally:
        painter.end()
    return image


def _alpha_scan(image: QImage) -> int:
    visible = 0
    for y in range(0, image.height(), 4):
        for x in range(0, image.width(), 4):
            if image.pixelColor(x, y).alpha() > 0:
                visible += 1
    return visible
