import os
from pathlib import Path


APP_NAME = "KartOverlay"
PROJECTS_DIR_NAME = "KartOverlay Projects"


def user_data_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / APP_NAME


def default_projects_dir() -> Path:
    base = Path(os.getenv("USERPROFILE", Path.home()))
    return base / "Documents" / PROJECTS_DIR_NAME


def ensure_user_data_dir() -> Path:
    path = user_data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_default_projects_dir() -> Path:
    path = default_projects_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path
