from kart_overlay.app import AppBootstrap


def test_app_bootstrap_exposes_application_metadata():
    bootstrap = AppBootstrap.build()

    assert bootstrap.app_name == "卡丁车数据叠层"
    assert bootstrap.main_window_title == "卡丁车数据叠层"
    assert bootstrap.qt_api in {"PySide6", "PyQt5"}
