from kart_overlay.widgets.hud_theme import hud_card_metrics
from kart_overlay.widgets.speed_widget import SpeedWidget


def test_overlay_widget_font_px_stays_fixed_when_container_resizes():
    large = SpeedWidget(x=0, y=0, width=420, height=160)
    small = SpeedWidget(x=0, y=0, width=90, height=40)

    assert large.font_px(20, minimum=10) == 20
    assert small.font_px(20, minimum=10) == 20
    assert small.font_px(8, minimum=10) == 10


def test_overlay_widget_font_px_uses_explicit_font_scale():
    widget = SpeedWidget(x=0, y=0, width=90, height=40, font_scale=1.25)

    assert widget.font_px(20, minimum=10) == 25
    assert widget.font_scale == 1.25


def test_hud_card_metrics_keep_text_fixed_for_large_widget():
    small = hud_card_metrics(width=90, height=40)
    large = hud_card_metrics(width=420, height=160)

    assert large.value_px == small.value_px == 31
    assert large.value_h == small.value_h == 42.0


def test_hud_card_metrics_scale_text_from_explicit_font_scale():
    metrics = hud_card_metrics(width=420, height=160, font_scale=1.25)

    assert metrics.ratio == 1.25
    assert metrics.value_px == 39
    assert metrics.value_h == 52.5


def test_font_scale_keeps_lower_bound_without_upper_bound():
    tiny = SpeedWidget(x=0, y=0, width=90, height=40, font_scale=0.1)
    huge = SpeedWidget(x=0, y=0, width=90, height=40, font_scale=2.5)
    metrics = hud_card_metrics(width=420, height=160, font_scale=2.5)

    assert tiny.font_scale == 0.7
    assert huge.font_scale == 2.5
    assert metrics.ratio == 2.5
    assert metrics.value_px == 78


def test_speed_widget_minimum_size_is_content_driven():
    widget = SpeedWidget(x=0, y=0, width=20, height=20)

    assert widget.minimum_size() == (136, 72)
