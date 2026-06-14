from kart_overlay.application.export_formats import (
    available_export_formats,
    estimate_export_size_bytes,
    export_format_by_key,
    format_option_label,
)


def test_export_formats_include_small_transparent_options_with_size_hints():
    formats = available_export_formats()
    keys = [item.key for item in formats]

    assert keys == ["mov_prores_4444", "mov_qtrle_alpha"]
    assert all(item.supports_alpha for item in formats)
    assert export_format_by_key("mov_prores_4444").extension == ".mov"
    assert export_format_by_key("mov_qtrle_alpha").extension == ".mov"

    labels = [
        format_option_label(item, canvas_size=(1280, 720), fps=50.0, duration_sec=25 * 60)
        for item in formats
    ]

    assert all("透明" in label for label in labels)
    assert all("约" in label for label in labels)
    assert "小体量" in labels[-1]


def test_export_size_estimate_scales_by_resolution_fps_and_duration():
    prores_720p50_25min = estimate_export_size_bytes(
        export_format_key="mov_prores_4444",
        canvas_size=(1280, 720),
        fps=50.0,
        duration_sec=25 * 60,
    )
    prores_1080p50_25min = estimate_export_size_bytes(
        export_format_key="mov_prores_4444",
        canvas_size=(1920, 1080),
        fps=50.0,
        duration_sec=25 * 60,
    )
    qtrle_720p50_25min = estimate_export_size_bytes(
        export_format_key="mov_qtrle_alpha",
        canvas_size=(1280, 720),
        fps=50.0,
        duration_sec=25 * 60,
    )

    assert round(prores_720p50_25min / 1_000_000_000, 1) == 16.1
    assert prores_1080p50_25min > prores_720p50_25min * 2.2
    assert qtrle_720p50_25min < prores_720p50_25min / 3
