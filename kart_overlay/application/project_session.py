from pathlib import Path
import os

from PySide6.QtCore import QObject, Signal

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.domain.track.models import TrackDefinition
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.widgets.widget_factory import default_widget_layouts


def _default_output_dir() -> str:
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                desktop_value, _ = winreg.QueryValueEx(key, "Desktop")
            desktop_path = Path(os.path.expandvars(str(desktop_value)))
            if desktop_path.exists():
                return str(desktop_path)
        except OSError:
            pass
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return str(desktop)
    drive_desktop = Path("D:/Desktop")
    if drive_desktop.exists():
        return str(drive_desktop)
    return str(Path.home())


def default_export_settings() -> dict[str, str]:
    return {
        "output_dir": _default_output_dir(),
        "output_filename": "overlay",
        "fps": "60",
        "overlay_resolution_mode": "original",
        "range_mode": "full_telemetry",
        "format": "mov_prores_4444",
    }


class ProjectSession(QObject):
    telemetry_changed = Signal(object, object)
    video_path_changed = Signal(str)
    video_metadata_changed = Signal(object)
    track_definition_changed = Signal(object)
    background_image_path_changed = Signal(str)
    track_analysis_changed = Signal(object)
    widget_layouts_changed = Signal(object)
    export_settings_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.telemetry: TelemetryStore | None = None
        self.telemetry_source_path: str = ""
        self.video_path: str = ""
        self.video_metadata: VideoMetadata | None = None
        self.track_definition: TrackDefinition | None = None
        self.background_image_path: str = ""
        self.track_analysis: TrackAnalysisSummary | None = None
        self.widget_layouts: dict[str, dict[str, object]] = default_widget_layouts()
        self.export_settings: dict[str, str] = default_export_settings()

    def set_telemetry(
        self,
        telemetry: TelemetryStore,
        *,
        source_path: str | Path | None = None,
    ) -> None:
        source_text = str(source_path or "")
        self.telemetry = telemetry
        self.telemetry_source_path = source_text
        self.track_analysis = None
        self.telemetry_changed.emit(telemetry, source_text)
        self.track_analysis_changed.emit(self.track_analysis)

    def set_video_path(self, video_path: str | Path) -> None:
        self.video_path = str(video_path)
        self.video_path_changed.emit(self.video_path)

    def set_video_metadata(self, metadata: VideoMetadata) -> None:
        self.video_metadata = metadata
        self.video_metadata_changed.emit(metadata)

    def set_track_definition(self, track_definition: TrackDefinition | None) -> None:
        self.track_definition = track_definition
        if track_definition is not None:
            self.background_image_path = track_definition.background_image_path
        self.track_analysis = None
        self.track_analysis_changed.emit(self.track_analysis)
        self.background_image_path_changed.emit(self.background_image_path)
        self.track_definition_changed.emit(track_definition)

    def set_background_image_path(self, image_path: str | Path) -> None:
        self.background_image_path = str(image_path)
        self.background_image_path_changed.emit(self.background_image_path)

    def set_track_analysis(self, track_analysis: TrackAnalysisSummary | None) -> None:
        self.track_analysis = track_analysis
        self.track_analysis_changed.emit(track_analysis)

    def set_widget_layouts(self, widget_layouts: dict[str, dict[str, object]]) -> None:
        merged = default_widget_layouts()
        for name, layout in widget_layouts.items():
            merged.setdefault(name, {})
            merged[name].update(dict(layout))
        self.widget_layouts = merged
        self.widget_layouts_changed.emit(self.widget_layouts)

    def set_export_settings(self, export_settings: dict[str, object]) -> None:
        merged = default_export_settings()
        for name, value in export_settings.items():
            merged[name] = str(value)
        merged["range_mode"] = "full_telemetry"
        self.export_settings = merged
        self.export_settings_changed.emit(self.export_settings)
