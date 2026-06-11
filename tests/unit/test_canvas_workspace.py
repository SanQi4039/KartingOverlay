from PySide6.QtWidgets import QApplication

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.ui.canvas_workspace import CanvasPreviewWidget, CanvasWorkspace
from kart_overlay.ui.texts import app_text, widget_display_name


def test_canvas_workspace_moves_widget_and_updates_shared_session():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.select_widget(widget_display_name("speed"))
    workspace.move_selected_widget(160, 220)

    assert session.widget_layouts["speed"]["x"] == 160
    assert session.widget_layouts["speed"]["y"] == 220
    assert workspace.position_label.text() == "X=160, Y=220"
    app.quit()


def test_canvas_workspace_lists_expanded_widget_set():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    listed = [workspace.widget_list.item(index).text() for index in range(workspace.widget_list.count())]

    assert widget_display_name("speed") in listed
    assert widget_display_name("timer") in listed
    assert widget_display_name("altitude") in listed
    assert widget_display_name("heading") in listed
    assert widget_display_name("g_force") in listed
    assert widget_display_name("mini_track") in listed
    assert widget_display_name("lap_summary") in listed
    assert widget_display_name("best_lap") in listed
    assert widget_display_name("sector_state") in listed
    assert workspace.preview_label.text() == app_text("canvas_preview_title")
    assert workspace.preview_time_label.text() == app_text("preview_time_default")
    app.quit()


def test_canvas_workspace_toggles_widget_enabled_state():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.select_widget(widget_display_name("coordinates"))
    workspace.enabled_toggle.setChecked(True)

    assert session.widget_layouts["coordinates"]["enabled"] is True
    app.quit()


def test_canvas_workspace_hide_button_disables_widget_without_deleting_layout():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.select_widget(widget_display_name("mini_track"))
    original_x = session.widget_layouts["mini_track"]["x"]
    original_y = session.widget_layouts["mini_track"]["y"]
    workspace.hide_widget_button.click()

    assert session.widget_layouts["mini_track"]["enabled"] is False
    assert session.widget_layouts["mini_track"]["x"] == original_x
    assert session.widget_layouts["mini_track"]["y"] == original_y
    assert workspace.enabled_toggle.isChecked() is False
    app.quit()


def test_canvas_workspace_updates_widget_size_in_shared_session():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.select_widget(widget_display_name("speed"))
    workspace.width_input.setValue(420)
    workspace.height_input.setValue(160)
    workspace.apply_position_button.click()

    assert session.widget_layouts["speed"]["width"] == 420
    assert session.widget_layouts["speed"]["height"] == 160
    app.quit()


def test_canvas_workspace_syncs_preview_selection_back_to_controls():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.preview_widget.widget_selected.emit("mini_track")

    assert workspace.widget_list.currentItem().text() == widget_display_name("mini_track")
    assert workspace.x_input.value() == int(session.widget_layouts["mini_track"]["x"])
    assert workspace.y_input.value() == int(session.widget_layouts["mini_track"]["y"])
    assert workspace.enabled_toggle.isChecked() is True
    app.quit()


def test_canvas_workspace_keeps_widget_keys_stable_when_selecting_chinese_label():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace.select_widget(widget_display_name("mini_track"))

    assert workspace._selected_widget_key == "mini_track"
    assert workspace.widget_list.currentItem().text() == widget_display_name("mini_track")
    app.quit()


def test_canvas_workspace_ignores_unknown_widget_labels_without_mutating_layouts():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)
    original_layouts = {
        name: dict(layout)
        for name, layout in session.widget_layouts.items()
    }

    workspace.select_widget("unknown-widget")

    assert workspace._selected_widget_key == "speed"
    assert session.widget_layouts == original_layouts
    assert "unknown-widget" not in session.widget_layouts
    assert workspace.widget_list.currentItem().text() == widget_display_name("speed")
    app.quit()


def test_canvas_workspace_keeps_minimum_width_resizable_with_wrapped_summary():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    assert workspace.preview_summary_label.wordWrap() is True
    assert workspace.preview_summary_label.minimumSizeHint().width() < 500
    assert workspace.minimumSizeHint().width() <= 900

    app.quit()


def test_canvas_workspace_no_longer_shows_video_reference_toggle():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    assert not hasattr(workspace, "video_reference_toggle")

    app.quit()


def test_canvas_workspace_preview_time_label_uses_localized_format():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    workspace = CanvasWorkspace(session=session)

    workspace._handle_preview_time_changed(1250)

    assert "1.250" in workspace.preview_time_label.text()
    assert "Preview time" not in workspace.preview_time_label.text()

    app.quit()


def test_canvas_preview_widget_reuses_cached_overlay_image_without_state_changes(monkeypatch):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    session.set_telemetry(
        TelemetryStore(
            samples=[
                TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0, speed_kmh=40.0),
                TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=5.0, speed_kmh=50.0),
            ]
        )
    )
    preview = CanvasPreviewWidget(session=session)
    render_calls = []

    def fake_render(self, frame):
        from PySide6.QtGui import QImage

        render_calls.append(frame.data_elapsed_sec)
        image = QImage(64, 36, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0xFF335577)
        return image

    monkeypatch.setattr(
        "kart_overlay.ui.canvas_workspace.FrameRenderer.render",
        fake_render,
    )

    preview.set_preview_time(0.5)
    preview._current_overlay_image()
    preview._current_overlay_image()

    assert len(render_calls) == 1
    app.quit()


def test_canvas_preview_widget_exposes_resize_handles_for_selected_widget():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    preview = CanvasPreviewWidget(session=session)
    preview.resize(1280, 720)

    preview.set_selected_widget_key("speed")

    handles = preview.resize_handle_rects()

    assert "bottom_right" in handles
    assert handles["bottom_right"].width() > 0
    app.quit()


def test_canvas_preview_widget_exposes_canvas_edge_annotations():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    preview = CanvasPreviewWidget(session=session)
    preview.resize(1280, 720)

    annotations = preview.canvas_edge_annotations()

    assert annotations["width"] == "1280 px"
    assert annotations["height"] == "720 px"
    app.quit()


def test_canvas_preview_widget_resize_selected_widget_updates_layout():
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    preview = CanvasPreviewWidget(session=session)

    preview.set_selected_widget_key("speed")
    preview.resize_selected_widget(420, 160)

    assert session.widget_layouts["speed"]["width"] == 420
    assert session.widget_layouts["speed"]["height"] == 160
    app.quit()
