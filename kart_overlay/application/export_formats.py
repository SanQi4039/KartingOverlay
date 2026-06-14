from dataclasses import dataclass


REFERENCE_PIXELS = 1280 * 720
REFERENCE_FPS = 50.0


@dataclass(frozen=True)
class ExportFormatSpec:
    key: str
    label: str
    extension: str
    description: str
    encoder_label: str
    supports_alpha: bool
    reference_mbps_720p50: float


_EXPORT_FORMATS: tuple[ExportFormatSpec, ...] = (
    ExportFormatSpec(
        key="mov_prores_4444",
        label="MOV ProRes 4444",
        extension=".mov",
        description="透明，剪辑软件兼容性最好，体积最大",
        encoder_label="ProRes 4444 (CPU)",
        supports_alpha=True,
        reference_mbps_720p50=86.0,
    ),
    ExportFormatSpec(
        key="mov_qtrle_alpha",
        label="MOV Animation",
        extension=".mov",
        description="透明，小体量，适合扁平 HUD；复杂画面可能变大",
        encoder_label="MOV Animation alpha (small transparent)",
        supports_alpha=True,
        reference_mbps_720p50=24.0,
    ),
)


def available_export_formats() -> list[ExportFormatSpec]:
    return list(_EXPORT_FORMATS)


def export_format_by_key(key: str | None) -> ExportFormatSpec:
    for spec in _EXPORT_FORMATS:
        if spec.key == key:
            return spec
    return _EXPORT_FORMATS[0]


def estimate_export_bitrate_mbps(
    *,
    export_format_key: str,
    canvas_size: tuple[int, int],
    fps: float,
) -> float:
    spec = export_format_by_key(export_format_key)
    width = max(int(canvas_size[0]), 1)
    height = max(int(canvas_size[1]), 1)
    fps_value = max(float(fps), 0.001)
    pixel_scale = (width * height) / REFERENCE_PIXELS
    fps_scale = fps_value / REFERENCE_FPS
    return spec.reference_mbps_720p50 * pixel_scale * fps_scale


def estimate_export_size_bytes(
    *,
    export_format_key: str,
    canvas_size: tuple[int, int],
    fps: float,
    duration_sec: float,
) -> int:
    bitrate_mbps = estimate_export_bitrate_mbps(
        export_format_key=export_format_key,
        canvas_size=canvas_size,
        fps=fps,
    )
    duration = max(float(duration_sec), 0.0)
    return int(round((bitrate_mbps * 1_000_000 / 8) * duration))


def format_size(size_bytes: int) -> str:
    size = max(int(size_bytes), 0)
    if size >= 1_000_000_000:
        return f"{size / 1_000_000_000:.1f} GB"
    if size >= 1_000_000:
        return f"{size / 1_000_000:.0f} MB"
    return f"{size / 1_000:.0f} KB"


def format_option_label(
    spec: ExportFormatSpec,
    *,
    canvas_size: tuple[int, int],
    fps: float,
    duration_sec: float,
) -> str:
    size_hint = format_size(
        estimate_export_size_bytes(
            export_format_key=spec.key,
            canvas_size=canvas_size,
            fps=fps,
            duration_sec=duration_sec,
        )
    )
    return f"{spec.label}（{spec.description}，约 {size_hint}）"
