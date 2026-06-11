from pathlib import Path


def test_dependency_manifest_lists_core_packages():
    text = Path("requirements.txt").read_text(encoding="utf-8")

    assert "pytest" in text
    assert "numpy" in text
    assert "pandas" in text
    assert "gpxpy" in text
    assert "PySide6" in text or "PyQt5" in text
