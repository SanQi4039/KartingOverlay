from PySide6.QtWidgets import QComboBox


COMMON_FPS_VALUES: tuple[str, ...] = ("24", "25", "30", "50", "60")


class FpsComboBox(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self._source_fps: float | None = None
        self.refresh_options(selected_value="60")

    def set_source_fps(self, fps: float | None, *, selected_value: str | None = None) -> None:
        self._source_fps = None if fps is None or fps <= 0 else float(fps)
        self.refresh_options(selected_value=selected_value or self._source_fps_text() or "60")

    def refresh_options(self, *, selected_value: str | None = None) -> None:
        selected = selected_value or self.selected_fps_text()
        self.blockSignals(True)
        self.clear()
        if self._source_fps is not None:
            self.addItem(f"{self._source_fps:.3f}（原视频）", self._source_fps_text())
        for value in COMMON_FPS_VALUES:
            self.addItem(value, value)
        index = self._find_fps_index(selected)
        self.setCurrentIndex(max(index, 0))
        self.blockSignals(False)

    def selected_fps_text(self) -> str:
        data = self.currentData()
        return str(data or self.currentText() or "60")

    def text(self) -> str:
        return self.selected_fps_text()

    def setText(self, value: str) -> None:
        index = self._find_fps_index(value)
        if index < 0 and _is_positive_float(value):
            self.insertItem(0, value, value)
            index = 0
        self.setCurrentIndex(max(index, 0))

    def _source_fps_text(self) -> str | None:
        if self._source_fps is None:
            return None
        return f"{self._source_fps:.6f}"

    def _find_fps_index(self, value: str | float | None) -> int:
        if value is None:
            return -1
        text = str(value).strip()
        if not text:
            return -1
        exact_index = self.findData(text)
        if exact_index >= 0:
            return exact_index
        try:
            requested = float(text)
        except ValueError:
            return -1
        for index in range(self.count()):
            data = self.itemData(index)
            try:
                candidate = float(data)
            except (TypeError, ValueError):
                continue
            if abs(candidate - requested) < 0.001:
                return index
        return -1


def _is_positive_float(value: str) -> bool:
    try:
        return float(value) > 0
    except ValueError:
        return False
