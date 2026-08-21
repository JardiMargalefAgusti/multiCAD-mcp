"""Genera installer/icono.ico (no requiere herramientas externas, solo Pillow).

Uso:  .venv\\Scripts\\python.exe installer\\crear_icono.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

NAVY = (10, 22, 51, 255)
AZUL = (31, 122, 224, 255)
BLANCO = (245, 248, 255, 255)

LADO = 1024
DESTINO = Path(__file__).resolve().parent / "icono.ico"


def crear() -> Path:
    """Dibuja el icono a 1024 px y lo guarda como .ico multi-resolucion."""
    lienzo = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(lienzo)

    # Fondo redondeado corporativo
    dibujo.rounded_rectangle(
        [(0, 0), (LADO - 1, LADO - 1)], radius=int(LADO * 0.22), fill=NAVY
    )

    centro = LADO // 2
    radio = int(LADO * 0.27)
    grosor = int(LADO * 0.045)

    # Diana de precision (metafora CAD): circulo + cruz de ejes
    dibujo.ellipse(
        [
            (centro - radio, centro - radio),
            (centro + radio, centro + radio),
        ],
        outline=AZUL,
        width=grosor,
    )
    largo = int(LADO * 0.40)
    dibujo.line(
        [(centro - largo, centro), (centro + largo, centro)],
        fill=BLANCO,
        width=int(grosor * 0.6),
    )
    dibujo.line(
        [(centro, centro - largo), (centro, centro + largo)],
        fill=BLANCO,
        width=int(grosor * 0.6),
    )

    # Punto de insercion
    punto = int(LADO * 0.055)
    dibujo.ellipse(
        [
            (centro - punto, centro - punto),
            (centro + punto, centro + punto),
        ],
        fill=BLANCO,
    )

    tamanos = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    lienzo.save(DESTINO, format="ICO", sizes=tamanos)
    return DESTINO


if __name__ == "__main__":
    print(f"Icono creado: {crear()}")
