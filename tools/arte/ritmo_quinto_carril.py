"""Quinto carril del Duelo de Frecuencias (modo Dificil, tecla Espacio): hexagono ambar.

    python tools/arte/ritmo_quinto_carril.py   ->  game/gui/ritmo/{nota_4, receptor_4, receptor_on_4}.png

Mismo lenguaje que las cuatro formas existentes (110 x 110): nota rellena con borde papel, receptor solo con
contorno del color del carril y receptor encendido relleno mas oscuro con borde papel. La forma distingue el
carril sin depender del color.
"""
import math
import os

from PIL import Image, ImageDraw

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(RAIZ, "game", "gui", "ritmo")
S = 4
PAPEL = (251, 246, 238, 255)
AMBAR = (232, 176, 75, 255)
AMBAR_OSC = (196, 140, 48, 255)


def hexagono(r):
    c = 55 * S
    return [(c + r * S * math.cos(math.radians(a)), c + r * S * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def dibujar(relleno, borde, grosor):
    im = Image.new("RGBA", (110 * S, 110 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if relleno is not None:
        d.polygon(hexagono(50), fill=borde)
        d.polygon(hexagono(50 - grosor), fill=relleno)
    else:
        d.polygon(hexagono(48), fill=borde)
        d.polygon(hexagono(48 - grosor), fill=(0, 0, 0, 0))
    return im.resize((110, 110), Image.LANCZOS)


def main():
    dibujar(AMBAR, PAPEL, 7).save(os.path.join(OUT, "nota_4.png"), optimize=True)
    dibujar(None, AMBAR, 5).save(os.path.join(OUT, "receptor_4.png"), optimize=True)
    dibujar(AMBAR_OSC, PAPEL, 7).save(os.path.join(OUT, "receptor_on_4.png"), optimize=True)
    print("ok:", OUT)


if __name__ == "__main__":
    main()
