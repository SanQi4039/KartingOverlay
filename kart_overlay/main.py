from dataclasses import dataclass

from PySide6.QtWidgets import QApplication, QMainWindow

from kart_overlay.app import AppBootstrap
from kart_overlay.ui.main_window import create_main_window


@dataclass(frozen=True)
class AppRuntime:
    application: QApplication
    window: QMainWindow


def build_runtime(argv: list[str] | None = None) -> AppRuntime:
    AppBootstrap.build()
    application = QApplication.instance() or QApplication(argv or [])
    window = create_main_window()
    return AppRuntime(application=application, window=window)


def main() -> int:
    runtime = build_runtime()
    runtime.window.show()
    return runtime.application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
