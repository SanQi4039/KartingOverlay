from pathlib import Path
import os
import shutil
import subprocess
import sys


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_project_root_on_sys_path() -> Path:
    root = project_root()
    root_text = str(root)
    if root_text in sys.path:
        sys.path.remove(root_text)
    sys.path.insert(0, root_text)
    return root


ensure_project_root_on_sys_path()

from kart_overlay.config import ExternalToolsConfig

APP_NAME = "KartOverlay"
ARCHIVE_NAME = "KartOverlay-windows-x64"
INSTALLER_BASENAME = "KartOverlay-Setup"
RUNTIME_DLL_NAMES = (
    "libbz2.dll",
    "libcrypto-3-x64.dll",
    "libexpat.dll",
    "liblzma.dll",
    "libssl-3-x64.dll",
)

def packaged_output_dir(*, dist_dir: Path) -> Path:
    return dist_dir / APP_NAME


def archive_output_path(*, dist_dir: Path) -> Path:
    return dist_dir / f"{ARCHIVE_NAME}.zip"


def installer_script_path() -> Path:
    return project_root() / "packaging" / "installer.iss"


def installer_output_path(*, dist_dir: Path) -> Path:
    return dist_dir / f"{INSTALLER_BASENAME}.exe"


def resolve_inno_setup_compiler() -> Path:
    explicit_path = os.getenv("KART_OVERLAY_INNO_SETUP_PATH", "").strip()
    if explicit_path:
        return Path(explicit_path)

    default_candidates = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    for candidate in default_candidates:
        if candidate.exists():
            return candidate
    return Path("ISCC.exe")


def bundled_tool_targets(*, dist_dir: Path, ffmpeg_path: Path, ffprobe_path: Path) -> dict[str, Path]:
    bin_dir = packaged_output_dir(dist_dir=dist_dir) / "tools" / "ffmpeg" / "bin"
    return {
        "ffmpeg": bin_dir / ffmpeg_path.name,
        "ffprobe": bin_dir / ffprobe_path.name,
    }


def validate_tool_paths(ffmpeg_path: Path, ffprobe_path: Path) -> None:
    missing = [str(path) for path in (ffmpeg_path, ffprobe_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing packaged tools: {', '.join(missing)}")


def resolve_runtime_dlls() -> dict[str, Path]:
    conda_prefix = Path(sys.prefix)
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for dll_name in RUNTIME_DLL_NAMES:
        candidate = _resolve_runtime_dll(dll_name=dll_name, prefix=conda_prefix)
        if candidate.exists():
            resolved[dll_name] = candidate
        else:
            missing.append(dll_name)
    if missing:
        raise FileNotFoundError(f"Missing runtime DLLs: {', '.join(missing)}")
    return resolved


def _resolve_runtime_dll(*, dll_name: str, prefix: Path) -> Path:
    for directory in _runtime_dll_search_dirs(prefix=prefix):
        candidate = directory / dll_name
        if candidate.exists():
            return candidate
    cached = _find_conda_cached_dll(dll_name)
    if cached is not None:
        return cached
    return prefix / "Library" / "bin" / dll_name


def _runtime_dll_search_dirs(*, prefix: Path) -> list[Path]:
    dirs: list[Path] = []
    explicit = os.getenv("KART_OVERLAY_RUNTIME_DLL_DIR", "").strip()
    if explicit:
        dirs.append(Path(explicit))
    dirs.extend(
        [
            prefix / "Library" / "bin",
            prefix / "DLLs",
            prefix,
        ]
    )
    conda_prefix = os.getenv("CONDA_PREFIX", "").strip()
    if conda_prefix:
        conda_path = Path(conda_prefix)
        dirs.extend([conda_path / "Library" / "bin", conda_path / "DLLs"])
    return dirs


def _find_conda_cached_dll(dll_name: str) -> Path | None:
    package_cache = Path.home() / ".conda" / "pkgs"
    if not package_cache.exists():
        return None
    matches = sorted(
        package_cache.glob(f"*/Library/bin/{dll_name}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def build_readme_text() -> str:
    return (
        "KartOverlay packaged build for Windows.\n"
        "\n"
        "Trial run checklist:\n"
        f"1. Build {INSTALLER_BASENAME}.exe from the packaged folder contents.\n"
        f"2. Install KartOverlay through {INSTALLER_BASENAME}.exe on a Windows machine.\n"
        "3. Run KartOverlay from the installed shortcut or install directory.\n"
        "4. Import telemetry and video, then confirm track, canvas, and export.\n"
        "\n"
        "Bundled tools:\n"
        "- ffmpeg.exe\n"
        "- ffprobe.exe\n"
        "\n"
        "Bundled runtime support DLLs:\n"
        "- libssl-3-x64.dll\n"
        "- libcrypto-3-x64.dll\n"
        "- libexpat.dll\n"
        "- liblzma.dll\n"
        "- libbz2.dll\n"
        "\n"
        "This build targets Windows only.\n"
    )


def copy_bundled_tools(*, dist_dir: Path, ffmpeg_path: Path, ffprobe_path: Path) -> None:
    targets = bundled_tool_targets(dist_dir=dist_dir, ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
    sources = {
        "ffmpeg": ffmpeg_path,
        "ffprobe": ffprobe_path,
    }
    for name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sources[name], target)


def bundled_runtime_dll_targets(*, dist_dir: Path, runtime_dlls: dict[str, Path]) -> dict[str, Path]:
    internal_dir = packaged_output_dir(dist_dir=dist_dir) / "_internal"
    return {
        dll_name: internal_dir / source_path.name
        for dll_name, source_path in runtime_dlls.items()
    }


def copy_runtime_dlls(*, dist_dir: Path, runtime_dlls: dict[str, Path]) -> None:
    targets = bundled_runtime_dll_targets(dist_dir=dist_dir, runtime_dlls=runtime_dlls)
    for dll_name, source_path in runtime_dlls.items():
        target = targets[dll_name]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)


def write_packaged_readme(*, dist_dir: Path) -> Path:
    readme_path = packaged_output_dir(dist_dir=dist_dir) / "README-Packaged.txt"
    readme_path.write_text(build_readme_text(), encoding="utf-8")
    return readme_path


def create_distribution_archive(*, dist_dir: Path) -> Path:
    archive_base = archive_output_path(dist_dir=dist_dir).with_suffix("")
    output_path = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=dist_dir,
            base_dir=APP_NAME,
        )
    )
    return output_path


def run_inno_setup(*, root: Path, dist_dir: Path) -> None:
    compiler_path = resolve_inno_setup_compiler()
    script_path = installer_script_path()
    command = [
        str(compiler_path),
        f"/O{dist_dir}",
        f"/F{installer_output_path(dist_dir=dist_dir).stem}",
        str(script_path),
    ]
    try:
        subprocess.run(command, check=True, cwd=root)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Inno Setup compiler not found: {compiler_path}. "
            "Install Inno Setup 6 or set KART_OVERLAY_INNO_SETUP_PATH."
        ) from error


def run_pyinstaller(*, root: Path, dist_dir: Path, build_dir: Path) -> None:
    spec_path = root / "packaging" / "kart_overlay.spec"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        str(spec_path),
    ]
    subprocess.run(command, check=True, cwd=root)


def main() -> int:
    tools = ExternalToolsConfig.from_env()
    ffmpeg_path = Path(tools.ffmpeg_path)
    ffprobe_path = Path(tools.ffprobe_path)
    validate_tool_paths(ffmpeg_path, ffprobe_path)
    runtime_dlls = resolve_runtime_dlls()

    root = project_root()
    dist_dir = root / "dist"
    build_dir = root / "build" / "pyinstaller"

    run_pyinstaller(root=root, dist_dir=dist_dir, build_dir=build_dir)
    copy_bundled_tools(dist_dir=dist_dir, ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
    copy_runtime_dlls(dist_dir=dist_dir, runtime_dlls=runtime_dlls)
    write_packaged_readme(dist_dir=dist_dir)
    create_distribution_archive(dist_dir=dist_dir)
    try:
        run_inno_setup(root=root, dist_dir=dist_dir)
    except FileNotFoundError as error:
        print(f"Installer skipped: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
