from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import app_text


class TrackInspectorPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QFormLayout(self)

        self.lap_crossings_value = QLabel("0")
        self.lap_count_value = QLabel("0")
        self.last_lap_value = QLabel("--")
        self.best_lap_value = QLabel("--")
        self.sector_summary_value = QLabel("--")
        self.last_sector_times_value = QLabel("--")
        self.best_sector_times_value = QLabel("--")

        layout.addRow(app_text("lap_crossings"), self.lap_crossings_value)
        layout.addRow(app_text("lap_count"), self.lap_count_value)
        layout.addRow(app_text("last_lap"), self.last_lap_value)
        layout.addRow(app_text("best_lap"), self.best_lap_value)
        layout.addRow(app_text("sectors"), self.sector_summary_value)
        layout.addRow(app_text("last_sector_times"), self.last_sector_times_value)
        layout.addRow(app_text("best_sector_times"), self.best_sector_times_value)

    def update_analysis(
        self,
        *,
        lap_result: LapDetectionResult | None,
        sector_result: SectorDetectionResult | None,
        analysis_summary: TrackAnalysisSummary | None = None,
    ) -> None:
        if lap_result is None:
            self.lap_crossings_value.setText("0")
            self.lap_count_value.setText("0")
            self.last_lap_value.setText("--")
            self.best_lap_value.setText("--")
        else:
            self.lap_crossings_value.setText(str(len(lap_result.crossings)))
            self.lap_count_value.setText(str(len(lap_result.laps)))
            self.last_lap_value.setText(
                "--" if not lap_result.laps else f"{lap_result.laps[-1].lap_time_sec:.3f} 秒"
            )
            self.best_lap_value.setText(
                "--" if lap_result.best_lap is None else f"{lap_result.best_lap.lap_time_sec:.3f} 秒"
            )

        if sector_result is None or not sector_result.sector_crossings:
            self.sector_summary_value.setText("--")
        else:
            summary = ", ".join(
                f"{name}: {len(crossings)}"
                for name, crossings in sorted(sector_result.sector_crossings.items())
            )
            self.sector_summary_value.setText(summary)

        if analysis_summary is None:
            self.last_sector_times_value.setText("--")
            self.best_sector_times_value.setText("--")
            return

        self.last_sector_times_value.setText(_format_sector_times(analysis_summary.last_sector_times))
        self.best_sector_times_value.setText(_format_sector_times(analysis_summary.best_sector_times))


def _format_sector_times(values: dict[str, float]) -> str:
    if not values:
        return "--"
    return ", ".join(
        f"{name} {duration_sec:.3f} 秒"
        for name, duration_sec in sorted(values.items())
    )
