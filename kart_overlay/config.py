from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from kart_overlay.app_paths import ensure_user_data_dir
from kart_overlay.packaging import is_frozen_runtime, runtime_root


def _env_candidate_paths() -> list[Path]:
    candidates = [Path(".env.local")]
    try:
        candidates.append(ensure_user_data_dir() / ".env.local")
    except Exception:
        pass
    return candidates


def _load_local_env() -> None:
    for env_path in _env_candidate_paths():
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_local_env()


def _runtime_root() -> Path:
    return runtime_root()


def _is_frozen_runtime() -> bool:
    return is_frozen_runtime()


def _default_binary_candidates(binary_name: str) -> list[Path]:
    executable_name = binary_name
    if os.name == "nt" and not executable_name.lower().endswith(".exe"):
        executable_name = f"{executable_name}.exe"

    candidates: list[Path] = []
    if _is_frozen_runtime():
        candidates.append(_runtime_root() / "tools" / "ffmpeg" / "bin" / executable_name)

    conda_prefix = os.getenv("CONDA_PREFIX", "").strip()
    if conda_prefix:
        base = Path(conda_prefix)
        candidates.extend(
            [
                base / "Library" / "bin" / executable_name,
                base / "Scripts" / executable_name,
                base / "bin" / executable_name,
            ]
        )

    workspace_root = _runtime_root()
    candidates.extend(
        [
            workspace_root / "tools" / "ffmpeg" / "bin" / executable_name,
            workspace_root / executable_name,
            Path("C:/ffmpeg/bin") / executable_name,
            Path("D:/ffmpeg/bin") / executable_name,
        ]
    )
    return candidates


def _resolve_binary_path(*, env_var: str, binary_name: str) -> str:
    explicit_path = os.getenv(env_var, "").strip()
    if explicit_path:
        return explicit_path

    detected_path = shutil.which(binary_name)
    if detected_path:
        return detected_path

    for candidate in _default_binary_candidates(binary_name):
        if candidate.exists():
            return str(candidate)

    return binary_name


def binary_path_available(binary_path: str) -> bool:
    if not binary_path:
        return False

    candidate = Path(binary_path)
    if candidate.exists():
        return True

    return shutil.which(binary_path) is not None


@dataclass(frozen=True)
class ExternalToolsConfig:
    ffmpeg_path: str
    ffprobe_path: str
    ffmpeg_available: bool
    ffprobe_available: bool

    @classmethod
    def from_env(cls) -> "ExternalToolsConfig":
        ffmpeg_path = _resolve_binary_path(
            env_var="KART_OVERLAY_FFMPEG_PATH",
            binary_name="ffmpeg",
        )
        ffprobe_path = _resolve_binary_path(
            env_var="KART_OVERLAY_FFPROBE_PATH",
            binary_name="ffprobe",
        )
        return cls(
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            ffmpeg_available=binary_path_available(ffmpeg_path),
            ffprobe_available=binary_path_available(ffprobe_path),
        )
