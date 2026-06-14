from kart_overlay.ui.texts import (
    app_text,
    range_mode_options,
    widget_display_name,
    widget_key_from_display_name,
)
from kart_overlay.widgets.widget_factory import widget_label_pairs, widget_labels


def test_app_text_exposes_only_active_tabs_and_fallbacks_for_removed_sync_tab():
    assert app_text("window_title") != "window_title"
    assert app_text("tab_track") != "tab_track"
    assert app_text("tab_canvas") != "tab_canvas"
    assert app_text("tab_export") != "tab_export"
    assert app_text("tab_sync") == "tab_sync"
    assert app_text("sync_pick") == "sync_pick"
    assert app_text("workflow_status_sync") == "workflow_status_sync"
    assert app_text("missing_key") == "missing_key"


def test_range_mode_options_only_exposes_full_telemetry():
    assert range_mode_options() == [("full_telemetry", app_text("range_mode_full_telemetry"))]


def test_widget_display_name_returns_localized_labels():
    for widget_key in [
        "speed",
        "timer",
        "altitude",
        "height",
        "heading",
        "g_force",
        "g_force_longitudinal",
        "g_force_ball",
        "lap_summary",
        "best_lap",
        "best_lap_gap",
        "lap_distance",
        "sector_state",
        "coordinates",
        "mini_track",
    ]:
        assert widget_display_name(widget_key) != widget_key
    assert widget_display_name("missing_widget") == "missing_widget"


def test_widget_display_name_uses_clean_hud_labels():
    assert widget_display_name("speed") == "速度"
    assert widget_display_name("timer") == "当前圈"
    assert widget_display_name("heading") == "航向"
    assert widget_display_name("g_force") == "G 值（横向）"
    assert widget_display_name("g_force_longitudinal") == "G 值（纵向）"
    assert widget_display_name("height") == "高度（相对起点）"
    assert widget_display_name("lap_summary") == "圈数"
    assert widget_display_name("best_lap") == "最快圈"
    assert widget_display_name("best_lap_gap") == "最快圈差距"
    assert widget_display_name("lap_distance") == "圈已行驶距离"
    assert widget_display_name("sector_state") == "分段状态"
    assert widget_display_name("mini_track") == "赛道图"


def test_widget_key_from_display_name_roundtrips_known_widgets():
    for widget_key in ["speed", "timer", "mini_track"]:
        display_name = widget_display_name(widget_key)
        assert widget_key_from_display_name(display_name) == widget_key
    assert widget_key_from_display_name("missing_label") == "missing_label"


def test_widget_labels_returns_localized_display_names_in_layout_order():
    labels = widget_labels()

    assert labels[0] == widget_display_name("speed")
    assert labels[-1] == widget_display_name("g_force_ball")
    assert widget_display_name("mini_track") in labels
    assert widget_display_name("lap_distance") in labels
    assert len(labels) == 15


def test_widget_label_pairs_keep_stable_keys_and_localized_display_names():
    assert widget_label_pairs()[0] == ("speed", widget_display_name("speed"))
    assert widget_label_pairs()[-1] == ("g_force_ball", widget_display_name("g_force_ball"))
    assert ("mini_track", widget_display_name("mini_track")) in widget_label_pairs()
    assert ("lap_distance", widget_display_name("lap_distance")) in widget_label_pairs()
