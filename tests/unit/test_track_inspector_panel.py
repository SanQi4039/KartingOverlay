from PySide6.QtWidgets import QApplication

from kart_overlay.domain.timing.lap_detector import LapDetectionResult, LapRecord
from kart_overlay.domain.timing.line_crossing import LineCrossing
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary, SectorSplitRecord
from kart_overlay.ui.track_inspector_panel import TrackInspectorPanel


def test_track_inspector_panel_formats_analysis_summary():
    app = QApplication.instance() or QApplication([])
    panel = TrackInspectorPanel()

    panel.update_analysis(
        lap_result=LapDetectionResult(
            crossings=[LineCrossing(cross_time_sec=1.0, ratio=0.5)],
            laps=[LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0)],
            best_lap=LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0),
        ),
        sector_result=SectorDetectionResult(sector_crossings={"S1": [LineCrossing(cross_time_sec=2.0, ratio=0.2)]}),
        analysis_summary=TrackAnalysisSummary(
            lap_result=LapDetectionResult(
                crossings=[LineCrossing(cross_time_sec=1.0, ratio=0.5)],
                laps=[LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0)],
                best_lap=LapRecord(lap_index=1, start_time_sec=0.0, end_time_sec=10.0, lap_time_sec=10.0),
            ),
            sector_result=SectorDetectionResult(sector_crossings={"S1": [LineCrossing(cross_time_sec=2.0, ratio=0.2)]}),
            sector_splits=[
                SectorSplitRecord(
                    lap_index=1,
                    segment_name="S1",
                    start_time_sec=0.0,
                    end_time_sec=2.0,
                    duration_sec=2.0,
                    order=1,
                )
            ],
        ),
    )

    assert panel.lap_count_value.text() == "1"
    assert panel.last_lap_value.text() == "10.000 秒"
    assert panel.best_lap_value.text() == "10.000 秒"
    assert panel.sector_summary_value.text() == "S1: 1"
    assert panel.last_sector_times_value.text() == "S1 2.000 秒"
    assert panel.best_sector_times_value.text() == "S1 2.000 秒"
    app.quit()
