# -*- mode: python ; coding: utf-8 -*-
"""Spec de PyInstaller para multiCAD-MCP.

Construir desde la raiz del repo:
    .venv\\Scripts\\python.exe -m PyInstaller installer\\multicad.spec --noconfirm

Genera dist\\multiCAD-MCP\\multiCAD-MCP.exe (modo onedir: arranque rapido, que
importa porque Claude lanza el proceso en cada sesion).
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

RAIZ = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(RAIZ, "src")
ICONO = os.path.join(SPECPATH, "icono.ico")

# ---------- Datos que el codigo busca por __file__ ----------
datas = [
    (os.path.join(SRC, "config.json"), "."),
    (os.path.join(SRC, "web", "static"), os.path.join("web", "static")),
    (os.path.join(SRC, "ui", "templates"), os.path.join("ui", "templates")),
]

binaries = []
hiddenimports = [
    # paquetes propios de src/ (importados estaticamente por server.py)
    "server",
    "__version__",
    "core",
    "adapters",
    "adapters.adapter_manager",
    "adapters.autocad_adapter",
    "adapters.mixins",
    "mcp_tools",
    "mcp_tools.tools",
    "web.api",
    "ui.resources",
    # registro del MCP (lo llama el launcher por nombre)
    "registro_mcp",
    # COM de Windows
    "win32com",
    "win32com.client",
    "pythoncom",
    "pywintypes",
    "win32timezone",
    # panel grafico
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
]

# ---------- SDK MCP y servidor web ----------
# Los subpaquetes .cli son la interfaz de linea de comandos del SDK (typer /
# cyclopts): no se usan aqui y sus imports opcionales rompen el analisis.
EXCLUIR_SUBMODULOS = ("mcp.cli", "fastmcp.cli", "fastmcp.client.auth.cli")


def _sin_cli(nombre: str) -> bool:
    return not nombre.startswith(EXCLUIR_SUBMODULOS)


for paquete in ("mcp", "fastmcp"):
    paquete_datas, paquete_binarios, paquete_hidden = collect_all(
        paquete, filter_submodules=_sin_cli, on_error="ignore"
    )
    datas += paquete_datas
    binaries += paquete_binarios
    hiddenimports += paquete_hidden

hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("openpyxl")

a = Analysis(
    [os.path.join(SPECPATH, "multicad_launcher.py")],
    pathex=[SRC, SPECPATH],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "mypy", "ruff", "mkdocs", "matplotlib", "numpy.testing"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="multiCAD-MCP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # windowed: sin ventana negra cuando Claude arranca el servidor por stdio
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICONO if os.path.exists(ICONO) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="multiCAD-MCP",
)
