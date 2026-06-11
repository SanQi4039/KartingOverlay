from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from kart_overlay.ui.texts import app_text


class WindowChrome(QWidget):
    def __init__(self, host_window: QWidget) -> None:
        super().__init__()
        self._host_window = host_window
        self._drag_offset: QPoint | None = None
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(8)

        self._title_label = QLabel(app_text("window_title"))
        self._title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._title_label)

        self._minimize_button = self._build_button("minimize_button", "_", self._host_window.showMinimized)
        self._maximize_button = self._build_button("maximize_button", "[ ]", self._toggle_maximized)
        self._close_button = self._build_button("close_button", "X", self._host_window.close)

        layout.addWidget(self._minimize_button)
        layout.addWidget(self._maximize_button)
        layout.addWidget(self._close_button)

    def title_text(self) -> str:
        return self._title_label.text()

    def _build_button(self, name: str, text: str, callback) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(name)
        button.setFixedWidth(36)
        button.setFixedHeight(28)
        button.clicked.connect(callback)
        return button

    def _toggle_maximized(self) -> None:
        if self._host_window.isMaximized():
            self._host_window.showNormal()
            return

        self._host_window.showMaximized()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._host_window.isMaximized():
            self._drag_offset = event.globalPosition().toPoint() - self._host_window.frameGeometry().topLeft()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._host_window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)
