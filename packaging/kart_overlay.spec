from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path.cwd()

hiddenimports = collect_submodules("kart_overlay.widgets")

datas = []
env_example = ROOT / ".env.local.example"
if env_example.exists():
    datas.append((str(env_example), "."))

block_cipher = None

a = Analysis(
    [str(ROOT / "kart_overlay" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KartOverlay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="KartOverlay",
)
