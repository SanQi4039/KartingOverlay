from itertools import combinations

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.widgets.widget_factory import build_widgets_from_session


def test_default_hud_layout_fits_within_1280x720_canvas_without_overlap():
    session = ProjectSession()

    widgets = build_widgets_from_session(session)
    canvas_width, canvas_height = 1280, 720

    rects: dict[str, tuple[int, int, int, int]] = {}
    for widget in widgets:
        left = int(widget.x)
        top = int(widget.y)
        right = left + int(widget.width)
        bottom = top + int(widget.height)
        assert right <= canvas_width, widget.widget_key
        assert bottom <= canvas_height, widget.widget_key
        rects[widget.widget_key] = (left, top, right, bottom)

    for left_key, right_key in combinations(rects, 2):
        assert not _overlap(rects[left_key], rects[right_key]), (left_key, right_key)


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
