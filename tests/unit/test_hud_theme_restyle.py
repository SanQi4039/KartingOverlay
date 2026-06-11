from PySide6.QtGui import QColor

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.widgets.hud_theme import ACCENT, PANEL_FILL_ALPHA, PRIMARY_TEXT
from kart_overlay.widgets.widget_factory import build_widgets_from_session


def test_hud_theme_matches_lightweight_sticker_palette():
    assert PRIMARY_TEXT == QColor("#f8f9fa")
    assert ACCENT == QColor("#2fb5ff")
    assert PANEL_FILL_ALPHA == 0


def test_widget_factory_builds_chinese_named_widgets_for_overlay():
    session = ProjectSession()

    display_names = {widget.display_name for widget in build_widgets_from_session(session)}

    assert "速度" in display_names
    assert "当前圈" in display_names
    assert "赛道图" in display_names
