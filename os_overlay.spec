"""PyInstaller specification used to build the os-overlay executable."""

import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve()
sys.path.insert(0, str(ROOT / "src"))

from os_overlay import __version__  # noqa: E402

ONE_FILE = os.environ.get("OS_OVERLAY_ONEFILE", "0").lower() in ("1", "true", "yes")
DIST = ROOT / "dist" / ("os-overlay-onefile" if ONE_FILE else "os-overlay-onedir")

# Qt modules that are never imported but are still collected by the PySide6 hook.
UNUSED_LIBRARIES = (
    "Qt6Quick",
    "Qt6Quick3D",
    "Qt6QuickControls2",
    "Qt6QuickWidgets",
    "Qt6Qml",
    "Qt6QmlModels",
    "Qt6QmlWorkerScript",
    "Qt6StateMachine",
    "Qt6Pdf",
    "Qt6PdfWidgets",
    "Qt6OpenGL",
    "Qt6OpenGLWidgets",
    "Qt6Charts",
    "Qt6DataVisualization",
    "Qt6Graphs",
    "Qt6WebEngineCore",
    "Qt6WebEngineWidgets",
    "Qt6WebEngineQuick",
    "Qt6Multimedia",
    "Qt6MultimediaWidgets",
    "Qt6SpatialAudio",
    "Qt6SerialPort",
    "Qt6SerialBus",
    "Qt6Sql",
    "Qt6Test",
    "Qt6Help",
    "Qt6UiTools",
    "Qt6Designer",
    "Qt6Bluetooth",
    "Qt6Nfc",
    "Qt6Positioning",
    "Qt6Sensors",
    "Qt6WebChannel",
    "Qt6WebSockets",
    "Qt6HttpServer",
    "Qt6TextToSpeech",
    "Qt6RemoteObjects",
    "Qt6Scxml",
    "Qt6Xml",
    "Qt6Svg",
    "Qt6SvgWidgets",
)

VERSION_PARTS = tuple(int(part) for part in __version__.split(".")[:4]) + (0,) * (
    4 - len(__version__.split("."))
)
VERSION_FILE = ROOT / "build" / "version_info.txt"

EXCLUDES = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtHelp",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNfc",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTest",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
    "matplotlib",
    "numpy",
    "PIL",
    "pytest",
    "tkinter",
    "unittest",
]

VERSION_TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version},
    prodvers={version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'os-overlay contributors'),
          StringStruct('FileDescription', 'os-overlay crosshair overlay'),
          StringStruct('FileVersion', '{version_text}'),
          StringStruct('InternalName', 'os-overlay'),
          StringStruct('LegalCopyright', 'MIT License'),
          StringStruct('OriginalFilename', 'os-overlay.exe'),
          StringStruct('ProductName', 'os-overlay'),
          StringStruct('ProductVersion', '{version_text}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def write_version_file() -> str:
    """Create the Windows version resource file and return its path."""
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        VERSION_TEMPLATE.format(version=VERSION_PARTS, version_text=__version__),
        encoding="utf-8",
    )
    return str(VERSION_FILE)


a = Analysis(
    [str(ROOT / "run_os_overlay.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(ROOT / "assets" / "icon.ico"), "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

kept_binaries = TOC(
    [
        entry
        for entry in a.binaries
        if not any(unused in Path(entry[0]).name for unused in UNUSED_LIBRARIES)
    ]
)

exe_common = dict(
    name="os-overlay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icon.ico"),
    version=write_version_file(),
)

if ONE_FILE:
    # The single file executable is written straight into the dist folder.
    from PyInstaller.config import CONF

    CONF["distpath"] = str(DIST)
    exe = EXE(
        pyz,
        a.scripts,
        kept_binaries,
        a.datas,
        [],
        **exe_common,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **exe_common,
    )
    coll = COLLECT(
        exe,
        kept_binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="os-overlay-onedir",
    )
