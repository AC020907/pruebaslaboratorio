"""Arte de Central de Emergencias (mapa ilustrado de Ciudad Nova y sprites), reproducible.

    python tools/arte/central_arte.py

Escribe game/images/central/*.png. El mapa sale del MISMO grafo que usa el motor (clases/CentralEmergencias.py):
cada calle dibujada es una arista y cada cruce un vertice, asi que lo que se ve y lo que se calcula coinciden.
Estilo de Civitas: formas planas, contorno de tinta, paleta de la interfaz. Se dibuja al doble y se reduce.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "game"))
from clases import CentralEmergencias as C  # noqa: E402

OUT = os.path.join(RAIZ, "game", "images", "central")
FUENTE = os.path.join(RAIZ, "game", "fonts", "Roboto-Regular.ttf")
FINA = os.path.join(RAIZ, "game", "fonts", "Roboto-Light.ttf")
S = 2
W, H = 1360, 900

TINTA = (43, 36, 64, 255)
PAPEL = (251, 246, 238, 255)
SUELO = (236, 228, 216, 255)
LILA = (201, 184, 216, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
TEAL = (47, 158, 143, 255)
AMBAR = (232, 176, 75, 255)
FRENO = (61, 126, 166, 255)
RIO = (120, 170, 200, 255)
PARQUE = (150, 196, 160, 255)
CALLE = (250, 247, 242, 255)
AVENIDA = (255, 252, 246, 255)

BARRIO_COLOR = {   # tejados de cada barrio: el jugador los distingue de un vistazo
    "Norte": ((196, 176, 214), (170, 148, 196)),
    "Medios": ((222, 170, 182), (198, 140, 158)),
    "Centro": ((236, 204, 150), (214, 178, 120)),
    "Alcaldía": ((160, 190, 214), (128, 164, 196)),
    "Oeste": ((150, 200, 190), (120, 176, 166)),
    "Sur": ((232, 186, 160), (210, 156, 128)),
}

random.seed(20261123)


def f(px, fina=False):
    return ImageFont.truetype(FINA if fina else FUENTE, int(px * S))


def lienzo(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def guardar(img, nombre):
    os.makedirs(OUT, exist_ok=True)
    w, h = img.size
    img = img.resize((w // S, h // S), Image.LANCZOS)
    img.save(os.path.join(OUT, nombre + ".png"), optimize=True)
    return img


def s(*v):
    return [x * S for x in v]


def nodo(i):
    x, y, _b = C.NODOS[i]
    return x, y


def mapa():
    img = lienzo(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle(s(0, 0, W, H), fill=SUELO)
    # Rio entre las filas 3 y 4 (solo lo cruzan los puentes).
    y3 = max(C.NODOS[k][1] for k in range(len(C.NODOS)) if 21 <= k <= 27)
    y4 = min(C.NODOS[k][1] for k in range(28, 35))
    ry0, ry1 = y3 + 48, y4 - 44
    pts = []
    for x in range(-20, W + 40, 40):
        pts.append((x, ry0 + 10 * math.sin(x / 140.0)))
    pts += [(x, ry1 + 10 * math.sin(x / 160.0 + 1)) for x in range(W + 40, -60, -40)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=RIO, outline=TINTA, width=4 * S)
    for k in range(10):
        x = 60 + k * 135
        yy = (ry0 + ry1) / 2 + 12 * math.sin(k)
        d.arc(s(x, yy - 10, x + 60, yy + 10), 200, 340, fill=(200, 226, 240, 255), width=3 * S)
    texto_rio = "RÍO NOVA"
    d.text(s(40, (ry0 + ry1) / 2 - 12), texto_rio, font=f(20, True), fill=(230, 244, 250, 255))
    # Manzanas entre calles: bloques de edificios con el color del barrio, o parques.
    cols = sorted(set(n[0] for n in C.NODOS))
    filas = sorted(set(n[1] for n in C.NODOS))
    xs = [C._COLS[k] for k in range(len(C._COLS))]
    ys = [C._FILAS[k] for k in range(len(C._FILAS))]
    parques = {(1, 0), (4, 1), (0, 3), (5, 2)}
    bandas = [(ys[k] + 22, ys[k + 1] - 22, k) for k in range(3)] + [(ys[4] + 22, H - 14, 4)]
    for y0, y1, cf in bandas:
        for cc in range(len(xs) - 1):
            x0, x1 = xs[cc] + 22, xs[cc + 1] - 22
            barrio = "Sur" if cf == 4 else C._barrio(cc + 1, cf + 1)
            if (cc, cf) in parques:
                d.rounded_rectangle(s(x0, y0, x1, y1), radius=18 * S, fill=PARQUE, outline=TINTA, width=3 * S)
                for _ in range(9):
                    tx, ty = random.uniform(x0 + 25, x1 - 25), random.uniform(y0 + 25, y1 - 25)
                    r = random.uniform(11, 18)
                    d.ellipse(s(tx - r, ty - r + 4, tx + r, ty + r + 4), fill=(110, 160, 124, 255))
                    d.ellipse(s(tx - r, ty - r, tx + r, ty + r), fill=(128, 178, 140, 255), outline=TINTA, width=2 * S)
                continue
            claro, oscuro = BARRIO_COLOR[barrio]
            d.rounded_rectangle(s(x0, y0, x1, y1), radius=10 * S, fill=(228, 219, 206, 255), outline=TINTA, width=3 * S)
            # Edificios: rectangulos con sombra plana hacia abajo a la derecha.
            bx = x0 + 10
            while bx < x1 - 30:
                bw = random.randint(34, 62)
                bw = min(bw, x1 - 10 - bx)
                by = y0 + 10
                while by < y1 - 26:
                    bh = random.randint(30, 56)
                    bh = min(bh, y1 - 10 - by)
                    d.rectangle(s(bx + 5, by + 5, bx + bw + 3, by + bh + 3), fill=(190, 180, 172, 255))
                    col = claro if random.random() < 0.6 else oscuro
                    d.rectangle(s(bx, by, bx + bw - 2, by + bh - 2), fill=col + (255,), outline=TINTA, width=2 * S)
                    if random.random() < 0.5:
                        d.rectangle(s(bx + 6, by + 6, bx + 14, by + 14), fill=(255, 255, 255, 150))
                    by += bh + 6
                bx += bw + 6
    # Calles: contorno de tinta y relleno; avenidas mas anchas con linea central.
    for i, (a, b, tipo, _n) in enumerate(C.CALLES):
        xa, ya = nodo(a)
        xb, yb = nodo(b)
        ancho = {"avenida": 30, "calle": 22, "puente": 24}[tipo]
        d.line(s(xa, ya, xb, yb), fill=TINTA, width=(ancho + 7) * S)
    for k in range(len(C.NODOS)):
        x, y = nodo(k)
        d.ellipse(s(x - 18, y - 18, x + 18, y + 18), fill=TINTA)
    for i, (a, b, tipo, _n) in enumerate(C.CALLES):
        xa, ya = nodo(a)
        xb, yb = nodo(b)
        ancho = {"avenida": 30, "calle": 22, "puente": 24}[tipo]
        d.line(s(xa, ya, xb, yb), fill=AVENIDA if tipo == "avenida" else (CALLE if tipo == "calle" else (226, 216, 200, 255)),
               width=ancho * S)
    for k in range(len(C.NODOS)):
        x, y = nodo(k)
        d.ellipse(s(x - 14, y - 14, x + 14, y + 14), fill=CALLE)
    for i, (a, b, tipo, _n) in enumerate(C.CALLES):
        xa, ya = nodo(a)
        xb, yb = nodo(b)
        largo = math.hypot(xb - xa, yb - ya)
        ux, uy = (xb - xa) / largo, (yb - ya) / largo
        if tipo == "avenida":
            t = 22
            while t < largo - 22:
                d.line(s(xa + ux * t, ya + uy * t, xa + ux * (t + 14), ya + uy * (t + 14)), fill=AMBAR, width=3 * S)
                t += 28
        if tipo == "puente":
            px, py = -uy, ux
            for lado in (-1, 1):
                d.line(s(xa + px * 15 * lado + ux * 18, ya + py * 15 * lado + uy * 18,
                         xb + px * 15 * lado - ux * 18, yb + py * 15 * lado - uy * 18), fill=TINTA, width=4 * S)
    # Nombres de barrio.
    etiquetas = {"BARRIO NORTE": (150, 28), "MEDIOS": (1040, 28), "CENTRO": (610, 318), "ALCALDÍA": (1000, 505),
                 "OESTE": (120, 505), "BARRIO SUR": (575, 850)}
    for t, (x, y) in etiquetas.items():
        bb = d.textbbox((0, 0), t, font=f(22, True))
        tw, th = (bb[2] - bb[0]) / S, (bb[3] - bb[1]) / S
        d.rounded_rectangle(s(x - 12, y - 6, x + tw + 12, y + th + 12), radius=8 * S, fill=PAPEL, outline=TINTA, width=2 * S)
        d.text(s(x, y), t, font=f(22, True), fill=TINTA)
    # Los hospitales se dibujan en vivo (con sus camas libres) sobre el mapa.
    x, y = nodo(C.AMBULANCIAS[0][1])
    d.rounded_rectangle(s(x + 22, y + 22, x + 110, y + 64), radius=6 * S, fill=(214, 224, 236, 255), outline=TINTA, width=3 * S)
    d.text(s(x + 34, y + 32), "BASE 12", font=f(16), fill=TINTA)
    d.rectangle(s(0, 0, W - 1, H - 1), outline=TINTA, width=6 * S)
    return guardar(img, "mapa")


def ambulancia():
    img = lienzo(64, 32)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(s(2, 3, 62, 29), radius=6 * S, fill=(246, 242, 246, 255), outline=TINTA, width=3 * S)
    d.rectangle(s(4, 13, 60, 19), fill=RUMOR)
    d.rounded_rectangle(s(44, 6, 58, 26), radius=4 * S, fill=(92, 82, 128, 255), outline=TINTA, width=2 * S)
    d.rectangle(s(20, 8, 28, 24), fill=RUMOR)
    d.rectangle(s(16, 12, 32, 20), fill=RUMOR)
    return guardar(img, "ambulancia")


def auto(nombre, color):
    img = lienzo(34, 18)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(s(1, 2, 33, 16), radius=5 * S, fill=color, outline=TINTA, width=2 * S)
    d.rounded_rectangle(s(19, 4, 27, 14), radius=2 * S, fill=(70, 62, 100, 255))
    return guardar(img, nombre)


def barricada():
    img = lienzo(70, 40)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(s(4, 10, 66, 30), radius=5 * S, fill=PAPEL, outline=TINTA, width=3 * S)
    for k in range(5):
        x = 8 + k * 12
        d.polygon([(x * S, 12 * S), ((x + 6) * S, 12 * S), ((x + 1) * S, 28 * S), ((x - 5) * S, 28 * S)], fill=RUMOR)
    d.rounded_rectangle(s(4, 10, 66, 30), radius=5 * S, fill=None, outline=TINTA, width=3 * S)
    d.polygon([(30 * S, 2 * S), (40 * S, 2 * S), (44 * S, 12 * S), (26 * S, 12 * S)], fill=(232, 120, 60, 255), outline=TINTA)
    return guardar(img, "barricada")


def megafono():
    img = lienzo(44, 44)
    d = ImageDraw.Draw(img)
    d.ellipse(s(2, 2, 42, 42), fill=AMBAR, outline=TINTA, width=3 * S)
    d.polygon([(12 * S, 18 * S), (20 * S, 18 * S), (31 * S, 11 * S), (31 * S, 33 * S), (20 * S, 26 * S), (12 * S, 26 * S)],
              fill=TINTA)
    return guardar(img, "aviso")


def hospital():
    img = lienzo(56, 56)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(s(3, 3, 53, 53), radius=12 * S, fill=PAPEL, outline=TINTA, width=4 * S)
    d.rectangle(s(22, 12, 34, 44), fill=RUMOR)
    d.rectangle(s(12, 22, 44, 34), fill=RUMOR)
    return guardar(img, "hospital")


def emergencia(nombre, color):
    img = lienzo(52, 52)
    d = ImageDraw.Draw(img)
    d.ellipse(s(3, 3, 49, 49), fill=color, outline=TINTA, width=4 * S)
    d.rectangle(s(22, 13, 30, 39), fill=PAPEL)
    d.rectangle(s(13, 22, 39, 30), fill=PAPEL)
    return guardar(img, nombre)


def main():
    mapa()
    ambulancia()
    for nombre, col in (("auto_a", (150, 136, 176, 255)), ("auto_b", (98, 92, 118, 255)), ("auto_c", FRENO),
                        ("auto_d", AMBAR), ("auto_e", VINO), ("auto_f", TEAL)):
        auto(nombre, col)
    barricada()
    megafono()
    hospital()
    emergencia("em_critico", RUMOR)
    emergencia("em_grave", AMBAR)
    emergencia("em_moderado", (150, 120, 190, 255))
    emergencia("em_cerrada", (170, 164, 182, 255))
    exportar_web()
    print("ok:", OUT)


def exportar_web():
    """Las mismas imagenes para la Arena Online (leaderboard/app/static/central/*.webp)."""
    web = os.path.join(RAIZ, "leaderboard", "app", "static", "central")
    os.makedirs(web, exist_ok=True)
    for n in ("mapa", "ambulancia", "barricada", "aviso", "hospital", "em_critico", "em_grave", "em_moderado", "em_cerrada"):
        im = Image.open(os.path.join(OUT, n + ".png"))
        im.save(os.path.join(web, n + ".webp"), "WEBP", quality=86, method=6)


if __name__ == "__main__":
    main()
