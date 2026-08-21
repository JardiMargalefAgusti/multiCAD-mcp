"""Test funcional del servidor MCP por stdio (checklist de buenas practicas).

Lanza el ejecutable con --mcp, hace el handshake MCP real, lista las
herramientas y ejecuta una llamada inocua (manage_session -> list_supported,
que no necesita CAD abierto).

Uso:
    .venv\\Scripts\\python.exe installer\\test_mcp.py
    .venv\\Scripts\\python.exe installer\\test_mcp.py "C:\\ruta\\multiCAD-MCP.exe"

Sin argumento usa dist\\multiCAD-MCP\\multiCAD-MCP.exe del repo.
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

RAIZ = Path(__file__).resolve().parent.parent
POR_DEFECTO = RAIZ / "dist" / "multiCAD-MCP" / "multiCAD-MCP.exe"

ESPERADAS = {
    "manage_session",
    "draw_entities",
    "manage_layers",
    "manage_files",
    "manage_entities",
    "manage_blocks",
    "export_data",
}


async def probar(exe: Path) -> int:
    """Handshake + list_tools + una llamada real. Devuelve codigo de salida."""
    parametros = StdioServerParameters(command=str(exe), args=["--mcp"])

    async with stdio_client(parametros) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()

            herramientas = await sesion.list_tools()
            nombres = {h.name for h in herramientas.tools}
            print(f"Herramientas expuestas ({len(nombres)}): {sorted(nombres)}")

            faltan = ESPERADAS - nombres
            if faltan:
                print(f"FALLO: faltan herramientas: {sorted(faltan)}")
                return 1

            resultado = await sesion.call_tool(
                "manage_session",
                {"operations": '[{"action": "list_supported"}]'},
            )
            texto = "\n".join(
                bloque.text
                for bloque in resultado.content
                if getattr(bloque, "text", None)
            )
            print(f"manage_session/list_supported -> {texto[:400]}")

            if not texto.strip():
                print("FALLO: la llamada no devolvio contenido")
                return 1

    print("OK: el servidor responde correctamente por stdio")
    return 0


def main() -> int:
    """Resuelve el ejecutable y lanza la prueba."""
    exe = Path(sys.argv[1]) if len(sys.argv) > 1 else POR_DEFECTO
    if not exe.exists():
        print(f"No existe el ejecutable: {exe}")
        print("Construyelo antes con: powershell -File installer\\build.ps1")
        return 2
    print(f"Probando {exe}")
    return asyncio.run(probar(exe))


if __name__ == "__main__":
    sys.exit(main())
