import sys
from pathlib import Path

from scripts.build_windows_dist import (
    RUNTIME_DLL_NAMES,
    archive_output_path,
    build_readme_text,
    bundled_runtime_dll_targets,
    bundled_tool_targets,
    ensure_project_root_on_sys_path,
    installer_script_path,
    installer_output_path,
    project_root,
    resolve_inno_setup_compiler,
    resolve_runtime_dlls,
    validate_tool_paths,
)


def test_bundled_tool_targets_use_tools_ffmpeg_bin_layout(tmp_path: Path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffprobe_path = tmp_path / "ffprobe.exe"

    targets = bundled_tool_targets(
        dist_dir=tmp_path / "dist",
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
    )

    assert targets["ffmpeg"] == tmp_path / "dist" / "KartOverlay" / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    assert targets["ffprobe"] == tmp_path / "dist" / "KartOverlay" / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"


def test_validate_tool_paths_requires_existing_binaries(tmp_path: Path):
    try:
        validate_tool_paths(tmp_path / "missing-ffmpeg.exe", tmp_path / "missing-ffprobe.exe")
    except FileNotFoundError as error:
        assert "ffmpeg" in str(error)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_build_readme_mentions_windows_and_bundled_tools():
    text = build_readme_text()

    assert "Windows" in text
    assert "ffmpeg.exe" in text
    assert "ffprobe.exe" in text
    assert "kartoverlay-setup.exe" in text.lower()


def test_bundled_runtime_dll_targets_use_internal_layout(tmp_path: Path):
    runtime_dlls = {
        "libssl-3-x64.dll": tmp_path / "libssl-3-x64.dll",
        "libcrypto-3-x64.dll": tmp_path / "libcrypto-3-x64.dll",
    }

    targets = bundled_runtime_dll_targets(dist_dir=tmp_path / "dist", runtime_dlls=runtime_dlls)

    assert targets["libssl-3-x64.dll"] == tmp_path / "dist" / "KartOverlay" / "_internal" / "libssl-3-x64.dll"
    assert targets["libcrypto-3-x64.dll"] == tmp_path / "dist" / "KartOverlay" / "_internal" / "libcrypto-3-x64.dll"


def test_archive_output_path_uses_zip_suffix(tmp_path: Path):
    archive_path = archive_output_path(dist_dir=tmp_path / "dist")

    assert archive_path == tmp_path / "dist" / "KartOverlay-windows-x64.zip"


def test_resolve_runtime_dlls_reads_from_conda_library_bin(monkeypatch, tmp_path: Path):
    library_bin = tmp_path / "Library" / "bin"
    library_bin.mkdir(parents=True)
    for dll_name in RUNTIME_DLL_NAMES:
        (library_bin / dll_name).write_text("", encoding="utf-8")

    monkeypatch.setattr("scripts.build_windows_dist.sys.prefix", str(tmp_path))

    resolved = resolve_runtime_dlls()

    assert resolved["libssl-3-x64.dll"] == library_bin / "libssl-3-x64.dll"


def test_resolve_runtime_dlls_reads_from_python_dlls_dir(monkeypatch, tmp_path: Path):
    dlls_dir = tmp_path / "DLLs"
    dlls_dir.mkdir(parents=True)
    for dll_name in RUNTIME_DLL_NAMES:
        (dlls_dir / dll_name).write_text("", encoding="utf-8")

    monkeypatch.setattr("scripts.build_windows_dist.sys.prefix", str(tmp_path))

    resolved = resolve_runtime_dlls()

    assert resolved["libssl-3-x64.dll"] == dlls_dir / "libssl-3-x64.dll"


def test_ensure_project_root_on_sys_path_adds_root_once(monkeypatch):
    root = project_root()
    monkeypatch.setattr("scripts.build_windows_dist.sys.path", ["D:\\temp\\child"])

    ensure_project_root_on_sys_path()
    ensure_project_root_on_sys_path()

    assert sys.path[0] == str(root)
    assert sys.path.count(str(root)) == 1


def test_installer_script_path_points_to_packaging_iss():
    assert installer_script_path() == project_root() / "packaging" / "installer.iss"


def test_installer_output_path_points_to_named_installer_exe(tmp_path: Path):
    assert installer_output_path(dist_dir=tmp_path / "dist") == tmp_path / "dist" / "KartOverlay-Setup.exe"


def test_resolve_inno_setup_compiler_prefers_explicit_env(monkeypatch, tmp_path: Path):
    compiler = tmp_path / "ISCC.exe"
    compiler.write_text("", encoding="utf-8")
    monkeypatch.setenv("KART_OVERLAY_INNO_SETUP_PATH", str(compiler))

    assert resolve_inno_setup_compiler() == compiler


def test_installer_script_supports_per_user_install_without_elevation():
    text = installer_script_path().read_text(encoding="utf-8")

    assert "PrivilegesRequired=lowest" in text
    assert "DefaultDirName={localappdata}\\Programs\\KartOverlay" in text
