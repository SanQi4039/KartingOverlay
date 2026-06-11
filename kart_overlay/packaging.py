from pathlib import Path
import sys


def is_frozen_runtime() -> bool:
    return bool(getattr(sys, "frozen", False))


def runtime_root() -> Path:
    if is_frozen_runtime():
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def bundled_tools_bin_dir() -> Path:
    return runtime_root() / "tools" / "ffmpeg" / "bin"
