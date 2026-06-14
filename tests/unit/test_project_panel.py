from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QFileDialog

from kart_overlay.application.project_session import ProjectSession
from kart_overlay.domain.telemetry.models import TelemetrySample
from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.track.models import Point2D, TimingLine, TrackDefinition
from kart_overlay.infrastructure.video.ffprobe_service import VideoMetadata
from kart_overlay.ui.project_panel import ProjectPanel


class FakeTelemetryImportService:
    def __init__(self) -> None:
        self.import_calls: list[str] = []

    def import_file(self, path: str | Path) -> TelemetryStore:
        self.import_calls.append(str(path))
        return TelemetryStore(
            samples=[
                TelemetrySample(sample_index=0, elapsed_sec=0.0, x_m=0.0, y_m=0.0),
                TelemetrySample(sample_index=1, elapsed_sec=1.0, x_m=10.0, y_m=10.0),
            ]
        )


class FakeVideoMetadataService:
    def __init__(self) -> None:
        self.inspect_calls: list[str] = []

    def runtime_status(self) -> dict:
        return {
            "ffmpeg_available": True,
            "ffmpeg_path": "ffmpeg",
            "ffprobe_available": True,
            "ffprobe_path": "ffprobe",
        }

    def inspect(self, path: str | Path) -> VideoMetadata:
        self.inspect_calls.append(str(path))
        return VideoMetadata(
            width=1920,
            height=1080,
            fps=60.0,
            duration_sec=95.0,
            rotation_deg=90,
        )


def test_project_panel_imports_assets_into_shared_session(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    telemetry_path = tmp_path / "sample.gpx"
    telemetry_path.write_text("stub", encoding="utf-8")
    video_path = tmp_path / "sample.mp4"
    video_path.write_text("stub", encoding="utf-8")

    panel.telemetry_path_input.setText(str(telemetry_path))
    panel.video_path_input.setText(str(video_path))
    panel.import_telemetry()
    panel.import_video()

    assert session.telemetry is not None
    assert session.telemetry_source_path == str(telemetry_path)
    assert session.video_path == str(video_path)
    assert session.video_metadata is not None
    assert panel.telemetry_status_label.text()
    assert panel.video_status_label.text()
    app.quit()


def test_project_panel_explains_input_file_purposes():
    app = QApplication.instance() or QApplication([])
    panel = ProjectPanel(
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )

    assert "遥测文件" in panel.telemetry_help_label.text()
    assert "速度" in panel.telemetry_help_label.text()
    assert "视频文件" in panel.video_help_label.text()
    assert "对齐" in panel.video_help_label.text()
    assert "第一帧预览" in panel.video_help_label.text()
    assert "背景图" in panel.background_help_label.text()
    assert "起终点" in panel.background_help_label.text()
    assert "自己截图" in panel.background_help_label.text()
    app.quit()


def test_project_panel_places_file_help_inside_matching_sections():
    app = QApplication.instance() or QApplication([])
    panel = ProjectPanel(
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    main_layout = panel.layout()
    telemetry_layout = panel.telemetry_section.layout()
    background_layout = panel.background_section.layout()
    video_layout = panel.video_section.layout()

    assert main_layout.indexOf(panel.telemetry_help_label) == -1
    assert main_layout.indexOf(panel.background_help_label) == -1
    assert main_layout.indexOf(panel.video_help_label) == -1
    assert telemetry_layout.indexOf(panel.telemetry_import_progress) < telemetry_layout.indexOf(panel.telemetry_help_label)
    assert background_layout.indexOf(panel.background_status_label) < background_layout.indexOf(panel.background_help_label)
    assert video_layout.indexOf(panel.video_import_progress) < video_layout.indexOf(panel.video_help_label)
    app.quit()


def test_project_panel_orders_import_sections_before_project_and_help():
    app = QApplication.instance() or QApplication([])
    panel = ProjectPanel(
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    layout = panel.layout()

    assert layout.indexOf(panel.telemetry_section) < layout.indexOf(panel.background_section)
    assert layout.indexOf(panel.background_section) < layout.indexOf(panel.video_section)
    assert layout.indexOf(panel.video_section) < layout.indexOf(panel.project_section)
    assert layout.indexOf(panel.telemetry_help_label) == -1
    assert layout.indexOf(panel.background_help_label) == -1
    assert layout.indexOf(panel.video_help_label) == -1
    app.quit()


def test_project_panel_browse_background_updates_shared_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    background_path = tmp_path / "track-background.png"
    background_path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(background_path), ""),
    )

    panel._browse_background()

    assert session.background_image_path == str(background_path)
    assert panel.background_path_input.text() == str(background_path)
    assert "track-background.png" in panel.background_status_label.text()
    app.quit()


def test_project_panel_saves_background_image_relative_to_project_when_possible(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    background_path = assets_dir / "track.png"
    background_path.write_text("stub", encoding="utf-8")
    project_path = tmp_path / "demo.kartoverlay"

    session.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
            ),
            background_image_path=str(background_path),
        )
    )

    panel.save_project_to_path(project_path)
    loaded = panel._project_service.load_project(project_path)

    assert loaded.track["background_image_path"] == str(Path("assets") / "track.png")
    app.quit()


def test_project_panel_loads_project_when_background_image_is_missing(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=FakeVideoMetadataService(),
    )
    project_path = tmp_path / "demo.kartoverlay"
    background_path = tmp_path / "missing-track.png"

    session.set_track_definition(
        TrackDefinition(
            start_finish=TimingLine(
                name="Start/Finish",
                start=Point2D(0.0, -5.0),
                end=Point2D(0.0, 5.0),
            ),
            background_image_path=str(background_path),
        )
    )
    panel.save_project_to_path(project_path)

    panel.load_project_from_path(project_path)

    assert session.track_definition is not None
    assert session.track_definition.background_image_path == str(background_path)
    app.quit()


def test_project_panel_browse_telemetry_imports_immediately_and_reimports_same_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    telemetry_service = FakeTelemetryImportService()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=telemetry_service,
        video_metadata_service=FakeVideoMetadataService(),
    )
    telemetry_path = tmp_path / "sample.gpx"
    telemetry_path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(telemetry_path), ""),
    )

    panel._browse_telemetry()
    panel._browse_telemetry()

    assert session.telemetry is not None
    assert session.telemetry_source_path == str(telemetry_path)
    assert telemetry_service.import_calls == [str(telemetry_path), str(telemetry_path)]
    assert panel.telemetry_import_progress.value() == 100
    app.quit()


def test_project_panel_browse_video_imports_immediately_and_reimports_same_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    app = QApplication.instance() or QApplication([])
    session = ProjectSession()
    video_service = FakeVideoMetadataService()
    panel = ProjectPanel(
        session=session,
        telemetry_import_service=FakeTelemetryImportService(),
        video_metadata_service=video_service,
    )
    video_path = tmp_path / "sample.mp4"
    video_path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(video_path), ""),
    )

    panel._browse_video()
    panel._browse_video()

    assert session.video_path == str(video_path)
    assert session.video_metadata is not None
    assert video_service.inspect_calls == [str(video_path), str(video_path)]
    assert panel.video_import_progress.value() == 100
    app.quit()
