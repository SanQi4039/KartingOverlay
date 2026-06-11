from dataclasses import dataclass

from kart_overlay.ui.texts import app_text


@dataclass(frozen=True)
class AppBootstrap:
    app_name: str
    main_window_title: str
    qt_api: str

    @classmethod
    def build(cls) -> "AppBootstrap":
        try:
            import PySide6  # noqa: F401

            qt_api = "PySide6"
        except ImportError:
            import PyQt5  # noqa: F401

            qt_api = "PyQt5"

        return cls(
            app_name=app_text("app_name"),
            main_window_title=app_text("window_title"),
            qt_api=qt_api,
        )
