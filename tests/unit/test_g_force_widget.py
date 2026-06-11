from PySide6.QtGui import QImage, QPainter

from kart_overlay.domain.telemetry.frame_provider import TelemetryFrame
from kart_overlay.widgets import g_force_widget as g_force_module
from kart_overlay.widgets.g_force_widget import GForceWidget


def test_g_force_widget_is_compact_single_ball_module():
    assert GForceWidget.default_width <= 160
    assert GForceWidget.default_height <= 160
    assert GForceWidget.default_width == GForceWidget.default_height


def test_g_force_widget_does_not_use_generic_hud_card(monkeypatch):
    calls = {"card": 0, "ball": 0}

    def fake_draw_hud_card(*args, **kwargs):
        calls["card"] += 1

    def fake_draw_g_ball(*args, **kwargs):
        calls["ball"] += 1

    monkeypatch.setattr(g_force_module, "draw_hud_card", fake_draw_hud_card, raising=False)
    monkeypatch.setattr(g_force_module, "draw_g_ball", fake_draw_g_ball)

    widget = GForceWidget(x=20, y=20)
    image = QImage(240, 240, QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(image)
    try:
        widget.render(
            painter,
            TelemetryFrame(
                data_elapsed_sec=1.0,
                x_m=0.0,
                y_m=0.0,
                speed_kmh=None,
                accel_long_g=0.35,
                accel_lat_g=-0.45,
            ),
        )
    finally:
        painter.end()

    assert calls["card"] == 0
    assert calls["ball"] == 1
