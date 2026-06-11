from kart_overlay.widgets.hud_theme import hud_card_metrics
from kart_overlay.widgets.speed_widget import SpeedWidget


def test_overlay_widget_font_px_scales_with_width_and_respects_floor():
    large = SpeedWidget(x=0, y=0, width=420, height=160)
    small = SpeedWidget(x=0, y=0, width=90, height=40)

    assert large.font_px(20, minimum=10) > 20
    assert small.font_px(20, minimum=10) == 10


def test_hud_card_metrics_expand_for_large_widget():
    small = hud_card_metrics(width=90, height=40)
    large = hud_card_metrics(width=420, height=160)

    assert large.value_px > large.title_px
    assert large.value_px > small.value_px
    assert small.title_px >= 10
