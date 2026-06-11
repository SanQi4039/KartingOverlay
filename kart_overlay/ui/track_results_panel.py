from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kart_overlay.domain.telemetry.store import TelemetryStore
from kart_overlay.domain.timing.lap_detector import LapDetectionResult
from kart_overlay.domain.timing.sector_detector import SectorDetectionResult
from kart_overlay.domain.timing.track_analysis import TrackAnalysisSummary
from kart_overlay.ui.texts import app_text


class TrackResultsPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._telemetry: TelemetryStore | None = None
        self._analysis_summary: TrackAnalysisSummary | None = None
        self._selected_sample = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(10)
        summary_grid.setVerticalSpacing(10)
        self.current_lap_value = self._add_value_card(summary_grid, 0, 0, "当前圈")
        self.best_lap_value = self._add_value_card(summary_grid, 0, 1, app_text("best_lap"))
        self.sector_times_value = self._add_value_card(summary_grid, 1, 0, app_text("best_sector_times"), colspan=2)

        lap_card = QFrame()
        lap_layout = QVBoxLayout(lap_card)
        lap_layout.setContentsMargins(8, 8, 8, 8)
        lap_layout.setSpacing(6)
        lap_layout.addWidget(QLabel("圈速列表"))
        self.lap_list_widget = QListWidget()
        self.lap_list_widget.setAlternatingRowColors(True)
        lap_layout.addWidget(self.lap_list_widget)

        detail_card = QFrame()
        detail_layout = QFormLayout(detail_card)
        self.telemetry_value = QLabel(app_text("workflow_status_not_loaded"))
        self.video_value = QLabel(app_text("workflow_status_not_loaded"))
        self.sample_value = QLabel(app_text("selection_none"))
        self.status_value = QLabel("--")
        self.background_value = QLabel("--")
        for label in (
            self.telemetry_value,
            self.video_value,
            self.sample_value,
            self.status_value,
            self.background_value,
        ):
            label.setWordWrap(True)
        detail_layout.addRow(app_text("workflow_status_telemetry"), self.telemetry_value)
        detail_layout.addRow(app_text("workflow_status_video"), self.video_value)
        detail_layout.addRow("采样点", self.sample_value)
        detail_layout.addRow("状态", self.status_value)
        detail_layout.addRow("背景图", self.background_value)

        layout.addLayout(summary_grid)
        layout.addWidget(lap_card, 1)
        layout.addWidget(detail_card)

    def _add_value_card(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        title: str,
        *,
        colspan: int = 1,
    ) -> QLabel:
        card = QFrame()
        card_layout = QVBoxLayout(card)
        title_label = QLabel(title)
        value_label = QLabel("--")
        value_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        layout.addWidget(card, row, column, 1, colspan)
        return value_label

    def update_analysis(
        self,
        *,
        telemetry: TelemetryStore | None,
        lap_result: LapDetectionResult | None,
        sector_result: SectorDetectionResult | None,
        analysis_summary: TrackAnalysisSummary | None,
        invalid_lap_indexes: set[int] | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._analysis_summary = analysis_summary
        if analysis_summary is None:
            self.current_lap_value.setText("--")
            self.best_lap_value.setText("--")
            self.sector_times_value.setText("--")
            self.lap_list_widget.clear()
            return

        self._refresh_current_lap_value()

        best_lap = analysis_summary.best_lap_time_sec
        self.best_lap_value.setText("--" if best_lap is None else f"{best_lap:.3f} s")

        sector_text = _format_sector_times(analysis_summary.best_sector_times)
        if sector_text == "--" and sector_result is not None and sector_result.sector_crossings:
            sector_text = ", ".join(sorted(sector_result.sector_crossings))
        self.sector_times_value.setText(sector_text)
        self._refresh_lap_list(
            lap_result=lap_result,
            analysis_summary=analysis_summary,
            invalid_lap_indexes=invalid_lap_indexes or set(),
        )

    def update_telemetry(self, telemetry: TelemetryStore | None, source_path: str) -> None:
        self._telemetry = telemetry
        if telemetry is None:
            self.telemetry_value.setText(app_text("workflow_status_not_loaded"))
            return
        source_name = source_path or "Current Session"
        self.telemetry_value.setText(f"{telemetry.sample_count} samples | {source_name}")

    def update_video(self, metadata) -> None:
        if metadata is None:
            self.video_value.setText(app_text("workflow_status_not_loaded"))
            return
        self.video_value.setText(f"{metadata.width}x{metadata.height} | {metadata.fps:.3f} fps")

    def update_selected_sample(self, sample) -> None:
        self._selected_sample = sample
        if sample is None or sample.x_m is None or sample.y_m is None:
            self.sample_value.setText(app_text("selection_none"))
            self._refresh_current_lap_value()
            self._refresh_current_lap_selection()
            return
        lap_text = ""
        if self._analysis_summary is not None:
            lap_number = self._analysis_summary.current_lap_number_at(sample.elapsed_sec)
            lap_text = f" | 第 {lap_number} 圈"
        self.sample_value.setText(
            f"#{sample.sample_index + 1} ({sample.x_m:.2f}, {sample.y_m:.2f}){lap_text}"
        )
        self._refresh_current_lap_value()
        self._refresh_current_lap_selection()

    def update_status(self, message: str) -> None:
        self.status_value.setText(message or "--")

    def update_background_status(self, message: str) -> None:
        self.background_value.setText(message or "--")

    def _refresh_current_lap_value(self) -> None:
        if self._analysis_summary is None:
            self.current_lap_value.setText("--")
            return
        elapsed_sec = None
        if self._selected_sample is not None:
            elapsed_sec = self._selected_sample.elapsed_sec
        elif self._telemetry is not None and self._telemetry.samples:
            elapsed_sec = self._telemetry.samples[-1].elapsed_sec

        if elapsed_sec is None:
            self.current_lap_value.setText("--")
            return

        current_lap = self._analysis_summary.current_lap_time_at(elapsed_sec)
        self.current_lap_value.setText("--" if current_lap is None else f"{current_lap:.3f} s")

    def _refresh_lap_list(
        self,
        *,
        lap_result: LapDetectionResult | None,
        analysis_summary: TrackAnalysisSummary,
        invalid_lap_indexes: set[int],
    ) -> None:
        self.lap_list_widget.clear()
        if lap_result is None:
            return

        current_lap_index = self._current_lap_index(analysis_summary)
        best_lap_index = None if lap_result.best_lap is None else lap_result.best_lap.lap_index
        for lap in lap_result.laps:
            label = f"第 {lap.lap_index} 圈  {lap.lap_time_sec:.3f} s"
            if lap.lap_index == best_lap_index:
                label = f"{label}  最佳"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, lap.lap_index)
            font = QFont(item.font())
            if lap.lap_index == best_lap_index:
                font.setBold(True)
            item.setFont(font)
            if lap.lap_index in invalid_lap_indexes:
                item.setForeground(QBrush(QColor("#7a8594")))
            self.lap_list_widget.addItem(item)

        if current_lap_index is not None:
            self._set_current_lap_row(current_lap_index)

    def _refresh_current_lap_selection(self) -> None:
        if self._analysis_summary is None:
            self.lap_list_widget.setCurrentRow(-1)
            return
        current_lap_index = self._current_lap_index(self._analysis_summary)
        if current_lap_index is None:
            self.lap_list_widget.setCurrentRow(-1)
            return
        self._set_current_lap_row(current_lap_index)

    def _current_lap_index(self, analysis_summary: TrackAnalysisSummary) -> int | None:
        if self._selected_sample is not None:
            return analysis_summary.current_lap_number_at(self._selected_sample.elapsed_sec)
        if self._telemetry is not None and self._telemetry.samples:
            return analysis_summary.current_lap_number_at(self._telemetry.samples[-1].elapsed_sec)
        return None

    def _set_current_lap_row(self, lap_index: int) -> None:
        for row in range(self.lap_list_widget.count()):
            item = self.lap_list_widget.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == lap_index:
                self.lap_list_widget.setCurrentRow(row)
                return
        self.lap_list_widget.setCurrentRow(-1)


def _format_sector_times(values: dict[str, float]) -> str:
    if not values:
        return "--"
    return ", ".join(f"{name} {duration_sec:.3f} s" for name, duration_sec in sorted(values.items()))
