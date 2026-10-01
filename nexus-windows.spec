# -*- mode: python ; coding: utf-8 -*-
# Windows uchun bitta portativ .exe (o'rnatilmaydi):
#   uv run --extra dev pyinstaller nexus-windows.spec --noconfirm
# Natija: dist/Nexus.exe. Sozlamalar (.env, loglar) — %USERPROFILE%\.nexus\ da.
from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = [
    'sounddevice',
    '_sounddevice_data',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.lifespan.off',
]
hiddenimports += collect_submodules('nexus')
hiddenimports += collect_submodules('google.genai')

datas = [('ui', 'ui'), ('.env.example', '.')]
binaries = []
for pkg in ('webview', '_sounddevice_data', 'uiautomation', 'comtypes'):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['nexus/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # macOS-only modullar Windows'da kerak emas
    excludes=['AppKit', 'Foundation', 'Quartz', 'WebKit', 'Vision', 'objc', 'PyObjCTools', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Nexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
)
