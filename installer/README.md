# Instalador .exe de multiCAD-MCP

Empaqueta el servidor MCP en un único `.exe` y lo distribuye con un instalador
que **registra el MCP en Claude automáticamente**. El usuario final solo hace
doble clic: no necesita Python, ni `uv`, ni editar ningún JSON.

Sigue `BUENAS_PRACTICAS_MCP_INSTALADORES.md` de APOGEA.

## Para el usuario final

1. Ejecuta `Instalar_multiCAD-MCP.exe`.
2. **Abre una sesión nueva de Claude** (las que ya tengas abiertas no lo verán).
3. Abre tu CAD y pide, por ejemplo: *"Dibuja un círculo rojo en 50,50 con radio 25"*.

Instala en `%LOCALAPPDATA%\Programs\multiCAD-MCP` (per-user, **sin UAC**), lo
cual es imprescindible: el registro debe correr con el mismo perfil cuyos
config de Claude hay que tocar.

Al desinstalar desde "Agregar o quitar programas", la entrada `multicad` se da
de baja sola y el resto de tus servidores MCP quedan intactos.

## Modos del ejecutable

Un solo binario que despacha según el primer argumento:

| Modo | Uso |
|---|---|
| *(sin argumentos)* | Panel: estado del registro, dashboard web, carpeta de datos |
| `--mcp` | Servidor MCP por stdio (lo lanza Claude) |
| `--dashboard` | Dashboard web + navegador, sin panel |
| `--registrar-mcp` | Escribe la entrada en los config de Claude (lo llama el instalador) |
| `--desregistrar-mcp` | La elimina (lo llama el desinstalador) |
| `--version` | Versión y rutas efectivas |

## Dónde escribe

**Configuración de Claude** (idempotente, con backup fechado, escritura atómica
y preservando el resto de servidores):

- `%USERPROFILE%\.claude.json` → Claude Code / Cowork (siempre)
- `claude_desktop_config.json` → Claude Desktop, en sus tres ubicaciones
  posibles (instalador clásico, Microsoft Store, beta); solo si existen

Clave del servidor: **`multicad`**. Es su identidad: no cambiarla entre
versiones o el usuario acumulará entradas duplicadas.

**Datos del usuario** en `%LOCALAPPDATA%\multiCAD-mcp\`:

- `config.json` — copia editable del config por defecto (puerto del dashboard,
  nivel de log, carpeta de salida, `allow_arbitrary_paths`)
- `logs\multicad_mcp.log` — log del servidor
- `logs\registro_mcp.log` — rastro del registro (el instalador corre oculto)

El launcher parchea en tiempo de ejecución las rutas que `src/` resuelve por
`__file__`, porque dentro del `.exe` apuntarían a la carpeta temporal del
bundle, que se borra en cada arranque. **`src/` no se modifica**, así el fork
sigue siendo fusionable con upstream.

## Compilar

Requisitos: el `.venv` del proyecto (`uv sync --dev`) e
[Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`).
PyInstaller se instala solo en el `.venv`, sin tocar `pyproject.toml`.

```powershell
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

Resultado: `installer\salida\Instalar_multiCAD-MCP.exe` (~40 MB).

Opciones: `-SoloExe` (salta Inno Setup), `-SinLimpiar` (build incremental).

## Verificar antes de distribuir

```powershell
# 1. Test funcional del servidor por stdio (7 herramientas + llamada real)
.venv\Scripts\python.exe installer\test_mcp.py

# 2. Instalación silenciosa
installer\salida\Instalar_multiCAD-MCP.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART

# 3. El servidor conecta de verdad
claude mcp list        # multicad ... √ Connected

# 4. Idempotencia: segunda ejecución actualiza, no duplica
"$env:LOCALAPPDATA\Programs\multiCAD-MCP\multiCAD-MCP.exe" --registrar-mcp
```

## Notas de empaquetado

- **`console=False`**: sin ventana negra cuando Claude arranca el servidor.
  El stdio por tuberías sigue funcionando; `guardar_streams()` pone `devnull`
  si Windows no conecta los descriptores.
- **stdout es sagrado en `--mcp`**: los logs y el banner de FastMCP van a
  `stderr` (`logging.StreamHandler(sys.stderr)` explícito).
- **`mcp.cli` y `fastmcp.cli` se excluyen** del análisis: son la CLI del SDK,
  no se usan y sus imports opcionales (`typer`, `cyclopts`) rompen el build.
- **onedir, no onefile**: arranque rápido, que importa porque Claude lanza el
  proceso en cada sesión.
