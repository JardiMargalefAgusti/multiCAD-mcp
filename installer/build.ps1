# Construye multiCAD-MCP.exe (PyInstaller) y el instalador (Inno Setup).
#
#   powershell -ExecutionPolicy Bypass -File installer\build.ps1
#   powershell -ExecutionPolicy Bypass -File installer\build.ps1 -SoloExe
#
# Resultado: installer\salida\Instalar_multiCAD-MCP.exe

param(
    [switch]$SoloExe,
    [switch]$SinLimpiar
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$instalador = Join-Path $raiz "installer"
$python = Join-Path $raiz ".venv\Scripts\python.exe"
$dist = Join-Path $raiz "dist\multiCAD-MCP"

function Paso($texto) { Write-Host "`n=== $texto ===" -ForegroundColor Cyan }

# ---------- 1. Entorno ----------
Paso "Comprobando entorno"
if (-not (Test-Path $python)) {
    throw "No existe $python. Ejecuta antes: uv sync --dev"
}
& $python -c "import fastmcp, win32com" | Out-Null
if (-not $?) { throw "Faltan dependencias en el .venv. Ejecuta: uv sync --dev" }
Write-Host "Python del proyecto: $((& $python -V))"

$tienePyInstaller = (& $python -c "import importlib.util as u; print(u.find_spec('PyInstaller') is not None)")
if ($tienePyInstaller.Trim() -ne "True") {
    Paso "Instalando PyInstaller en el .venv (no toca pyproject.toml)"
    uv pip install --python $python pyinstaller
    if (-not $?) { throw "No se pudo instalar PyInstaller" }
}

# ---------- 2. Icono ----------
$icono = Join-Path $instalador "icono.ico"
if (-not (Test-Path $icono)) {
    Paso "Generando icono"
    & $python (Join-Path $instalador "crear_icono.py")
}

# ---------- 3. PyInstaller ----------
Paso "Empaquetando con PyInstaller"
if (-not $SinLimpiar) {
    if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
    $build = Join-Path $raiz "build\multiCAD-MCP"
    if (Test-Path $build) { Remove-Item $build -Recurse -Force }
}
Push-Location $raiz
try {
    & $python -m PyInstaller (Join-Path $instalador "multicad.spec") --noconfirm --distpath (Join-Path $raiz "dist") --workpath (Join-Path $raiz "build")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller fallo (codigo $LASTEXITCODE)" }
}
finally { Pop-Location }

$exe = Join-Path $dist "multiCAD-MCP.exe"
if (-not (Test-Path $exe)) { throw "No se genero $exe" }
Write-Host "Ejecutable: $exe" -ForegroundColor Green

# ---------- 4. Humo: el exe arranca ----------
Paso "Comprobacion rapida (--version)"
& $exe --version
Write-Host "(el exe es windowed: la salida de --version va a stderr)"

if ($SoloExe) {
    Write-Host "`nHecho (solo exe). Prueba funcional:" -ForegroundColor Green
    Write-Host "  $python installer\test_mcp.py"
    exit 0
}

# ---------- 5. Inno Setup ----------
Paso "Compilando el instalador con Inno Setup"
$candidatos = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "No se encontro ISCC.exe. Instala Inno Setup 6: winget install JRSoftware.InnoSetup"
}

$salida = Join-Path $instalador "salida"
if (-not (Test-Path $salida)) { New-Item -ItemType Directory -Path $salida | Out-Null }

& $iscc (Join-Path $instalador "instalador.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup fallo (codigo $LASTEXITCODE)" }

$setup = Join-Path $salida "Instalar_multiCAD-MCP.exe"
Paso "Listo"
Write-Host "Instalador: $setup" -ForegroundColor Green
Write-Host "Tamano: $([math]::Round((Get-Item $setup).Length / 1MB, 1)) MB"
Write-Host "`nPrueba funcional del servidor:" -ForegroundColor Yellow
Write-Host "  $python installer\test_mcp.py"
