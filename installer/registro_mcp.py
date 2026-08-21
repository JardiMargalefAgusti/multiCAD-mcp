"""Registro automatico del servidor MCP de multiCAD en los config de Claude.

Sigue el patron de los demas MCP de APOGEA (Transcriptor, AutodeskForma-mcp,
GWS_Assistant): idempotente, con backup fechado, escritura atomica y
preservando el resto de servidores del usuario.

Destinos:
  1. %USERPROFILE%\\.claude.json                      -> Claude Code (ambito user)
  2. claude_desktop_config.json (si existe Desktop)   -> Claude Desktop, en sus
     tres ubicaciones posibles (instalador clasico, Microsoft Store, beta).

Lo invoca el instalador (multiCAD-MCP.exe --registrar-mcp) y el desinstalador
(--desregistrar-mcp).
"""

import datetime
import glob
import json
import os
import sys
from pathlib import Path

# Identidad estable del servidor: NO cambiar entre versiones o el usuario
# acumulara entradas duplicadas en su configuracion.
NOMBRE_SERVIDOR = "multicad"


def _comando_servidor() -> dict:
    """Entrada mcpServers apuntando a esta instalacion."""
    if getattr(sys, "frozen", False):
        return {
            "type": "stdio",
            "command": sys.executable,
            "args": ["--mcp"],
            "env": {},
        }
    # Modo desarrollo: python del .venv + este mismo launcher
    raiz = Path(__file__).resolve().parent.parent
    python = raiz / ".venv" / "Scripts" / "python.exe"
    launcher = Path(__file__).resolve().parent / "multicad_launcher.py"
    return {
        "type": "stdio",
        "command": str(python),
        "args": [str(launcher), "--mcp"],
        "env": {},
    }


def _configs_destino(solo_existentes: bool) -> list[Path]:
    """Rutas de configuracion de Claude que hay que tocar."""
    rutas: list[Path] = []
    perfil = os.environ.get("USERPROFILE")
    if perfil:
        rutas.append(Path(perfil) / ".claude.json")  # Claude Code: siempre

    candidatas_desktop: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidatas_desktop.append(
            Path(appdata) / "Claude" / "claude_desktop_config.json"
        )
    local = os.environ.get("LOCALAPPDATA")
    if local:
        patron = str(
            Path(local)
            / "Packages"
            / "Claude_*"
            / "LocalCache"
            / "Roaming"
            / "Claude"
            / "claude_desktop_config.json"
        )
        candidatas_desktop.extend(sorted(Path(p) for p in glob.glob(patron)))
    if perfil:
        candidatas_desktop.append(
            Path(perfil) / ".config" / "Claude" / "claude_desktop_config.json"
        )

    # Desktop solo se toca si esa instalacion existe (archivo o carpeta padre)
    for ruta in candidatas_desktop:
        if ruta.exists() or ruta.parent.exists():
            rutas.append(ruta)

    if solo_existentes:
        rutas = [r for r in rutas if r.exists()]
    return rutas


def _leer(ruta: Path) -> dict:
    if not ruta.exists():
        return {}
    crudo = ruta.read_text(encoding="utf-8").strip()
    return json.loads(crudo) if crudo else {}


def _escribir_con_backup(ruta: Path, datos: dict) -> None:
    """Backup fechado + escritura atomica (tmp + replace)."""
    if ruta.exists():
        sello = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = ruta.with_name(f"{ruta.stem}.BACKUP_{sello}{ruta.suffix}")
        respaldo.write_bytes(ruta.read_bytes())
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporal.replace(ruta)


def _variantes_de_caja(servidores: dict) -> list[str]:
    """Claves que son este mismo servidor escrito con otra caja.

    JSON distingue mayusculas, asi que quien registro el MCP a mano siguiendo
    el README (clave 'multiCAD', apuntando al .venv del repo) acabaria con dos
    servidores compitiendo por el mismo CAD. Esas claves son nuestras: se
    migran. Cualquier otra entrada del usuario no se toca jamas.
    """
    return [
        clave
        for clave in servidores
        if clave != NOMBRE_SERVIDOR and clave.lower() == NOMBRE_SERVIDOR
    ]


def registrar(log=print) -> int:
    """Crea o actualiza la entrada 'multicad'. Devuelve numero de errores."""
    errores = 0
    for ruta in _configs_destino(solo_existentes=False):
        try:
            datos = _leer(ruta)
        except json.JSONDecodeError as error:
            log(f"AVISO {ruta}: JSON invalido ({error}); no se toca")
            errores += 1
            continue
        if not isinstance(datos, dict):
            log(f"AVISO {ruta}: la raiz no es un objeto JSON; no se toca")
            errores += 1
            continue
        servidores = datos.setdefault("mcpServers", {})
        if not isinstance(servidores, dict):
            log(f"AVISO {ruta}: mcpServers no es un objeto; no se toca")
            errores += 1
            continue
        accion = "actualizado" if NOMBRE_SERVIDOR in servidores else "registrado"
        for antigua in _variantes_de_caja(servidores):
            del servidores[antigua]
            log(f"   migrada la entrada manual anterior '{antigua}' en {ruta}")
        servidores[NOMBRE_SERVIDOR] = _comando_servidor()
        _escribir_con_backup(ruta, datos)
        log(
            f"OK {NOMBRE_SERVIDOR} {accion} en {ruta} "
            f"({len(servidores) - 1} otros servidores preservados)"
        )
    log("Reinicia Claude (sesion nueva) para que detecte el servidor.")
    return errores


def desregistrar(log=print) -> int:
    """Elimina la entrada 'multicad' dejando el resto intacto."""
    errores = 0
    for ruta in _configs_destino(solo_existentes=True):
        try:
            datos = _leer(ruta)
        except json.JSONDecodeError:
            continue
        if not isinstance(datos, dict):
            continue
        servidores = datos.get("mcpServers")
        if not isinstance(servidores, dict):
            continue
        # Nuestra clave en cualquier caja: 'multicad', 'multiCAD', 'MultiCad'...
        a_borrar = [
            clave for clave in servidores if clave.lower() == NOMBRE_SERVIDOR
        ]
        if not a_borrar:
            continue
        for clave in a_borrar:
            del servidores[clave]
        _escribir_con_backup(ruta, datos)
        log(f"OK {', '.join(a_borrar)} eliminado de {ruta}")
    return errores


def esta_registrado() -> bool:
    """True si la entrada existe en el config de Claude Code."""
    perfil = os.environ.get("USERPROFILE")
    if not perfil:
        return False
    ruta = Path(perfil) / ".claude.json"
    try:
        datos = _leer(ruta)
    except (json.JSONDecodeError, OSError):
        return False
    servidores = datos.get("mcpServers") if isinstance(datos, dict) else None
    if not isinstance(servidores, dict):
        return False
    return any(clave.lower() == NOMBRE_SERVIDOR for clave in servidores)


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "registrar"
    sys.exit(desregistrar() if accion == "desregistrar" else registrar())
