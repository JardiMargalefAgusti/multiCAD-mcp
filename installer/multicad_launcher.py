"""Punto de entrada unico de multiCAD-MCP empaquetado como .exe.

Un solo binario, varios modos (patron de BUENAS_PRACTICAS_MCP_INSTALADORES.md):

    (sin argumentos)    Panel grafico: estado, dashboard web, registro manual
    --mcp               Servidor MCP por stdio (lo lanza Claude)
    --dashboard         Dashboard web + navegador, sin panel
    --registrar-mcp     Escribe la entrada en los config de Claude (instalador)
    --desregistrar-mcp  La elimina (desinstalador)
    --version           Version y rutas

El codigo de src/ no se modifica: este launcher lo adapta en tiempo de
ejecucion para que, dentro del .exe, los logs y el config.json vivan en
%LOCALAPPDATA%\\multiCAD-mcp\\ y no en la carpeta temporal del bundle.
"""

import logging
import os
import shutil
import sys
import threading
from pathlib import Path

APP_NAME = "multiCAD-mcp"
DEFAULT_PORT = 8888


# ========== Rutas ==========


def es_frozen() -> bool:
    """True si corremos dentro del .exe de PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Carpeta con el codigo/datos empaquetados (o src/ en desarrollo)."""
    if es_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent / "src"


def user_dir() -> Path:
    """Carpeta de datos del usuario (escribible siempre)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    destino = Path(base) / APP_NAME
    destino.mkdir(parents=True, exist_ok=True)
    return destino


# ========== Guardas de stdio ==========


def guardar_streams() -> None:
    """En un exe windowed sys.stdout/stderr pueden ser None: poner devnull.

    Sin esto, cualquier print o StreamHandler revienta el proceso.
    """
    for nombre in ("stdin", "stdout", "stderr"):
        if getattr(sys, nombre, None) is None:
            modo = "r" if nombre == "stdin" else "w"
            try:
                setattr(sys, nombre, open(os.devnull, modo, encoding="utf-8"))
            except OSError:
                pass


def aviso(mensaje: str) -> None:
    """Mensaje informativo: SIEMPRE por stderr (stdout es del JSON-RPC)."""
    try:
        print(mensaje, file=sys.stderr, flush=True)
    except Exception:
        pass


# ========== Adaptacion del codigo de src/ ==========


def preparar_sys_path() -> None:
    """En desarrollo, src/ e installer/ tienen que estar en sys.path."""
    if es_frozen():
        return
    raiz = Path(__file__).resolve().parent.parent
    for ruta in (raiz / "src", raiz / "installer"):
        if str(ruta) not in sys.path:
            sys.path.insert(0, str(ruta))


def asegurar_config_usuario() -> Path:
    """Copia el config.json empaquetado a la carpeta del usuario la 1a vez.

    Asi el usuario puede editar puerto, nivel de log o carpeta de salida sin
    tocar el interior del .exe (que ademas se borra en cada arranque).
    """
    destino = user_dir() / "config.json"
    if not destino.exists():
        origen = bundle_dir() / "config.json"
        if origen.exists():
            try:
                shutil.copyfile(origen, destino)
            except OSError as error:
                aviso(f"No se pudo crear {destino}: {error}")
    return destino


def parchear_config() -> None:
    """Hace que ConfigManager lea el config.json del usuario."""
    ruta_usuario = asegurar_config_usuario()
    if not ruta_usuario.exists():
        return

    import core.config as modulo_config

    modulo_config.ConfigManager._find_config_file = staticmethod(
        lambda: ruta_usuario
    )
    # El singleton ya se creo al importar el modulo: recargarlo en su sitio.
    modulo_config._config_manager._load_config()


def parchear_logging() -> None:
    """Redirige los logs a %LOCALAPPDATA% y el stream handler a stderr."""
    import mcp_tools.helpers as helpers

    def setup_logging_usuario() -> logging.Logger:
        carpeta = user_dir() / "logs"
        carpeta.mkdir(parents=True, exist_ok=True)
        fichero = carpeta / "multicad_mcp.log"

        from core import get_config

        nivel = getattr(
            logging, get_config().logging_level.upper(), logging.INFO
        )
        logging.basicConfig(
            level=nivel,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                # stderr explicito: stdout es sagrado en modo --mcp
                logging.StreamHandler(sys.stderr),
                logging.FileHandler(fichero, encoding="utf-8"),
            ],
            force=True,
        )
        return logging.getLogger("multicad")

    helpers.setup_logging = setup_logging_usuario


def cargar_servidor():
    """Aplica los parches y devuelve el modulo server ya inicializado."""
    preparar_sys_path()
    parchear_config()
    parchear_logging()
    import server

    return server


# ========== Modos ==========


def modo_mcp() -> int:
    """Servidor MCP por stdio. Nada puede escribir en stdout salvo el protocolo."""
    servidor = cargar_servidor()

    try:
        arrancar_dashboard_en_hilo(servidor)
    except Exception as error:  # el dashboard nunca debe tumbar el MCP
        aviso(f"Dashboard no disponible: {error}")

    servidor.mcp.run(transport="stdio")
    return 0


def arrancar_dashboard_en_hilo(servidor) -> threading.Thread:
    """Lanza el dashboard FastAPI en segundo plano (daemon)."""
    import uvicorn
    from core import get_config

    config = get_config()
    host = config.dashboard.host
    port = config.dashboard.port

    def correr():
        try:
            uvicorn.run(
                servidor.api_app if hasattr(servidor, "api_app") else _api_app(),
                host=host,
                port=port,
                log_level="warning",
            )
        except Exception as error:
            aviso(f"Dashboard detenido: {error}")

    hilo = threading.Thread(target=correr, daemon=True, name="dashboard")
    hilo.start()
    return hilo


def _api_app():
    from web.api import api_app

    return api_app


def modo_dashboard(abrir_navegador: bool = True) -> int:
    """Dashboard web en primer plano."""
    import webbrowser

    servidor = cargar_servidor()
    from core import get_config

    config = get_config()
    url = f"http://{config.dashboard.host}:{config.dashboard.port}/"

    arrancar_dashboard_en_hilo(servidor)
    if abrir_navegador:
        webbrowser.open(url)
    aviso(f"Dashboard en {url} (Ctrl+C para salir)")

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    return 0


def modo_registrar() -> int:
    """Registro en los config de Claude + copia en el log de instalacion."""
    preparar_sys_path()
    import registro_mcp

    lineas: list[str] = []

    def anotar(mensaje: str) -> None:
        lineas.append(str(mensaje))
        aviso(mensaje)

    errores = registro_mcp.registrar(log=anotar)
    _escribir_log_registro("registrar", lineas)
    return errores


def modo_desregistrar() -> int:
    """Baja del servidor en los config de Claude."""
    preparar_sys_path()
    import registro_mcp

    lineas: list[str] = []

    def anotar(mensaje: str) -> None:
        lineas.append(str(mensaje))
        aviso(mensaje)

    errores = registro_mcp.desregistrar(log=anotar)
    _escribir_log_registro("desregistrar", lineas)
    return errores


def _escribir_log_registro(accion: str, lineas: list[str]) -> None:
    """El instalador corre oculto: dejar rastro verificable en disco."""
    import datetime

    try:
        carpeta = user_dir() / "logs"
        carpeta.mkdir(parents=True, exist_ok=True)
        sello = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(carpeta / "registro_mcp.log", "a", encoding="utf-8") as fichero:
            fichero.write(f"\n=== {sello} :: {accion} ===\n")
            fichero.write(f"exe: {sys.executable}\n")
            for linea in lineas:
                fichero.write(f"{linea}\n")
    except OSError:
        pass


def modo_version() -> int:
    """Version y rutas efectivas."""
    preparar_sys_path()
    try:
        sys.path.insert(0, str(bundle_dir()))
        from __version__ import __version__ as version
    except Exception:
        version = "desconocida"
    aviso(f"multiCAD-MCP {version}")
    aviso(f"  ejecutable : {sys.executable}")
    aviso(f"  bundle     : {bundle_dir()}")
    aviso(f"  datos      : {user_dir()}")
    return 0


# ========== Panel grafico (modo por defecto) ==========


def modo_panel() -> int:
    """Ventana minima: estado, dashboard, registro manual, logs."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    preparar_sys_path()
    import registro_mcp

    estado = {"dashboard": False}

    ventana = tk.Tk()
    ventana.title("multiCAD-MCP")
    ventana.geometry("460x290")
    ventana.resizable(False, False)

    marco = ttk.Frame(ventana, padding=16)
    marco.pack(fill="both", expand=True)

    ttk.Label(
        marco, text="multiCAD-MCP", font=("Segoe UI", 15, "bold")
    ).pack(anchor="w")
    ttk.Label(
        marco,
        text="Control de AutoCAD / ZWCAD / GstarCAD / BricsCAD desde Claude",
        foreground="#555555",
        wraplength=420,
    ).pack(anchor="w", pady=(0, 12))

    texto_estado = tk.StringVar()

    def refrescar_estado() -> None:
        if registro_mcp.esta_registrado():
            texto_estado.set(
                "Servidor MCP registrado en Claude.\n"
                "Abre una SESION NUEVA de Claude para que lo detecte."
            )
        else:
            texto_estado.set(
                "El servidor MCP no aparece registrado.\n"
                "Pulsa 'Registrar en Claude' para arreglarlo."
            )

    refrescar_estado()
    ttk.Label(
        marco, textvariable=texto_estado, wraplength=420, justify="left"
    ).pack(anchor="w", pady=(0, 14))

    def abrir_dashboard() -> None:
        import webbrowser

        try:
            from core import get_config

            if not estado["dashboard"]:
                servidor = cargar_servidor()
                arrancar_dashboard_en_hilo(servidor)
                estado["dashboard"] = True
            config = get_config()
            webbrowser.open(
                f"http://{config.dashboard.host}:{config.dashboard.port}/"
            )
        except Exception as error:
            messagebox.showerror("Dashboard", f"No se pudo abrir:\n{error}")

    def registrar_ahora() -> None:
        lineas: list[str] = []
        errores = registro_mcp.registrar(log=lineas.append)
        _escribir_log_registro("registrar (panel)", lineas)
        refrescar_estado()
        resumen = "\n".join(lineas) or "Sin cambios"
        if errores:
            messagebox.showwarning("Registro con avisos", resumen)
        else:
            messagebox.showinfo("Registro completado", resumen)

    def abrir_datos() -> None:
        try:
            os.startfile(str(user_dir()))  # noqa: S606
        except OSError as error:
            messagebox.showerror("Carpeta de datos", str(error))

    botones = ttk.Frame(marco)
    botones.pack(anchor="w")
    ttk.Button(
        botones, text="Abrir dashboard web", command=abrir_dashboard, width=24
    ).grid(row=0, column=0, padx=(0, 8), pady=4)
    ttk.Button(
        botones, text="Registrar en Claude", command=registrar_ahora, width=24
    ).grid(row=0, column=1, pady=4)
    ttk.Button(
        botones, text="Carpeta de datos y logs", command=abrir_datos, width=24
    ).grid(row=1, column=0, padx=(0, 8), pady=4)
    ttk.Button(
        botones, text="Salir", command=ventana.destroy, width=24
    ).grid(row=1, column=1, pady=4)

    ventana.mainloop()
    return 0


# ========== Despacho ==========


def main(argv: list[str] | None = None) -> int:
    """Despacha segun el primer argumento."""
    guardar_streams()
    argumentos = list(sys.argv[1:] if argv is None else argv)
    modo = argumentos[0].lower() if argumentos else ""

    if modo == "--mcp":
        return modo_mcp()
    if modo == "--registrar-mcp":
        return modo_registrar()
    if modo == "--desregistrar-mcp":
        return modo_desregistrar()
    if modo == "--dashboard":
        return modo_dashboard()
    if modo in ("--version", "-v"):
        return modo_version()
    if modo in ("--help", "-h", "/?"):
        aviso(__doc__ or "")
        return 0
    return modo_panel()


if __name__ == "__main__":
    sys.exit(main())
