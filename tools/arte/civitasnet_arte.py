"""Remaster 3: imagenes de CivitasNet en la paleta de Civitas (sin degradados de otra aplicacion).

    python tools/arte/civitasnet_arte.py

Regenera game/images/civitasnet/hero_*.png (fondo de cada publicacion segun su estado), el aro de las
historias, el marco del telefono y el boton "Añadir al expediente". Guarda los originales en
tools/arte/respaldo_v1/civitasnet/ la primera vez. Solo interfaz.
"""
import math
import os
import shutil

from PIL import Image, ImageDraw

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR = os.path.join(RAIZ, "game", "images", "civitasnet")
RESPALDO = os.path.join(RAIZ, "tools", "arte", "respaldo_v1", "civitasnet")
S = 2

TINTA = (43, 36, 64, 255)
PAPEL = (251, 246, 238, 255)
LILA = (201, 184, 216, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
AMBAR = (232, 176, 75, 255)

# Fondo y acento de cada estado. Todos oscuros: el texto blanco de la publicacion mantiene contraste AA.
HEROES = {
    "pendiente":   ((58, 47, 88, 255), AMBAR),
    "verificada":  ((26, 92, 84, 255), (95, 200, 184, 255)),
    "cuestionada": ((104, 72, 20, 255), AMBAR),
    "manipulada":  ((110, 34, 56, 255), RUMOR),
    "publicidad":  ((36, 80, 110, 255), LILA),
}


def guardar(img, nombre):
    ruta = os.path.join(DIR, nombre)
    copia = os.path.join(RESPALDO, nombre)
    if os.path.exists(ruta) and not os.path.exists(copia):
        os.makedirs(RESPALDO, exist_ok=True)
        shutil.copy2(ruta, copia)
    img.save(ruta, optimize=True)


def hero(fondo, acento):
    """Cartel plano: color del estado, trama de puntos (semitono) y franja diagonal, como un afiche impreso."""
    W, H = 760 * S, 260 * S
    im = Image.new("RGBA", (W, H), fondo)
    d = ImageDraw.Draw(im)
    claro = tuple(min(255, int(c + (255 - c) * 0.10)) for c in fondo[:3]) + (255,)
    d.polygon([(W * 0.58, 0), (W * 0.78, 0), (W * 0.52, H), (W * 0.32, H)], fill=claro)
    paso = 26 * S
    for j, y in enumerate(range(paso // 2, H, paso)):
        for x in range(paso // 2 + (paso // 2 if j % 2 else 0), W, paso):
            k = max(0.0, (x / W - 0.62) / 0.38) * max(0.0, 1 - y / H * 0.6)
            r = 7 * S * k
            if r > 1:
                d.ellipse([x - r, y - r, x + r, y + r], fill=acento[:3] + (110,))
    d.rectangle([0, 0, 10 * S, H], fill=acento)
    return im.resize((760, 260), Image.LANCZOS)


def aro():
    W = 160 * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(360):
        col = RUMOR if (i // 45) % 2 == 0 else AMBAR
        d.pieslice([0, 0, W - 1, W - 1], i, i + 1.5, fill=col)
    return im.resize((160, 160), Image.LANCZOS)


def marco():
    W = 140 * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, W - 1], radius=50 * S, fill=LILA)
    d.rounded_rectangle([3 * S, 3 * S, W - 1 - 3 * S, W - 1 - 3 * S], radius=47 * S, fill=(15, 10, 26, 255))
    return im.resize((140, 140), Image.LANCZOS)


def boton():
    W, H = 360 * S, 80 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=14 * S, fill=PAPEL)
    d.rounded_rectangle([3 * S, 3 * S, W - 1 - 3 * S, H - 1 - 3 * S], radius=11 * S, fill=VINO)
    return im.resize((360, 80), Image.LANCZOS)


def main():
    for estado, (fondo, acento) in HEROES.items():
        guardar(hero(fondo, acento), "hero_%s.png" % estado)
    guardar(aro(), "circ_grad.png")
    guardar(marco(), "marco_telefono.png")
    guardar(boton(), "boton_expediente.png")
    print("ok: CivitasNet regenerado; originales en", RESPALDO)


if __name__ == "__main__":
    main()
