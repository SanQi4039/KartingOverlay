from pathlib import Path
from types import SimpleNamespace

from kart_overlay.config import _default_binary_candidates
from kart_overlay.packaging import runtime_root


def test_runtime_root_uses_executable_directory_when_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "kart_overlay.packaging.sys",
        SimpleNamespace(frozen=True, executable=str(tmp_path / "KartOverlay.exe")),
    )

    assert runtime_root() == tmp_path


def test_default_binary_candidates_prefer_bundled_tools_when_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("kart_overlay.config._runtime_root", lambda: tmp_path)
    monkeypatch.setattr("kart_overlay.config._is_frozen_runtime", lambda: True)
    monkeypatch.setattr("kart_overlay.config.os.name", "nt")
    monkeypatch.delenv("CONDA_PREFIX", raising=False)

    candidates = _default_binary_candidates("ffmpeg")

    assert candidates[0] == tmp_path / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"


def test_app_paths_use_localappdata_and_documents_on_windows(monkeypatch, tmp_path: Path):
    local_app_data = tmp_path / "LocalAppData"
    profile = tmp_path / "UserProfile"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("USERPROFILE", str(profile))

    from kart_overlay.app_paths import default_projects_dir, user_data_dir

    assert user_data_dir() == local_app_data / "KartOverlay"
    assert default_projects_dir() == profile / "Documents" / "KartOverlay Projects"
