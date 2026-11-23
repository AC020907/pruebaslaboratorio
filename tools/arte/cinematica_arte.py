"""Arte de la cinematica de apertura (calle bloqueada, ambulancia, interior y monitor), reproducible.

    python tools/arte/cinematica_arte.py

Escribe game/images/cinematica/*.png. Estilo de Civitas: formas planas, contorno de tinta, paleta de la
interfaz, de noche. Se dibuja al doble y se reduce. Solo elementos nuevos de la cinematica: no toca
ningun personaje oficial ni ningun fondo existente.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(RAIZ, "game", "images", "cinematica")
FUENTE = os.path.join(RAIZ, "game", "fonts", "Roboto-Regular.ttf")
S = 2

TINTA = (43, 36, 64, 255)
OSCURO = (16, 12, 24, 255)
NOCHE = (18, 13, 28, 255)
PAPEL = (251, 246, 238, 255)
LILA = (201, 184, 216, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
TEAL = (47, 158, 143, 255)
AMBAR = (232, 176, 75, 255)
FRENO = (61, 126, 166, 255)
VENTANA_OSC = (34, 27, 52, 255)
VIDRIO = (52, 45, 78, 255)
VIDRIO_LUZ = (92, 82, 128, 255)

random.seed(20261122)


def fuente(px):
    return ImageFont.truetype(FUENTE, int(px * S))


def lienzo(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def guardar(img, nombre):
    os.makedirs(OUT, exist_ok=True)
    w, h = img.size
    img = img.resize((w // S, h // S), Image.LANCZOS)
    img.save(os.path.join(OUT, nombre + ".png"), optimize=True)
    return img


def s(*v):
    return [int(x * S) for x in v]


def caja(d, x0, y0, x1, y1, fill, ink=TINTA, w=4, r=0):
    if r:
        d.rounded_rectangle(s(x0, y0, x1, y1), radius=r * S, fill=fill, outline=ink, width=w * S if ink else 0)
    else:
        d.rectangle(s(x0, y0, x1, y1), fill=fill, outline=ink, width=w * S if ink else 0)


def poli(d, pts, fill, ink=TINTA, w=4):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=ink, width=w * S if ink else 0)


def circ(d, cx, cy, r, fill, ink=TINTA, w=4):
    d.ellipse(s(cx - r, cy - r, cx + r, cy + r), fill=fill, outline=ink, width=w * S if ink else 0)


def texto(d, x, y, t, px, fill, anchor="mm", grueso=0, borde=None):
    kw = {}
    if grueso:
        kw = {"stroke_width": int(grueso * S), "stroke_fill": borde or fill}
    d.text((x * S, y * S), t, font=fuente(px), fill=fill, anchor=anchor, **kw)


def mezcla(c1, c2, k):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)) + (255,)


# ------------------------------------------------------------------ calle de noche (parallax)
ANCHO_CALLE = 4800
ACERA = 792          # borde superior de la acera (coordenadas de pantalla, alto 1080)
CALZADA = 832        # borde superior de la calzada


def cielo():
    img = lienzo(1920, 1080)
    d = ImageDraw.Draw(img)
    bandas = [(0, (14, 10, 22)), (300, (19, 14, 31)), (520, (26, 19, 41)), (660, (36, 26, 55)), (760, (50, 34, 66))]
    for (y0, c), (y1, _c) in zip(bandas, bandas[1:] + [(1080, None)]):
        d.rectangle(s(0, y0, 1920, y1), fill=c + (255,))
    for _ in range(60):
        x, y = random.randint(0, 1920), random.randint(10, 480)
        r = random.choice((1, 1, 1.5, 2))
        d.ellipse(s(x - r, y - r, x + r, y + r), fill=(201, 184, 216, random.randint(70, 150)))
    return guardar(img, "calle_cielo")


def lejos():
    """Skyline de Ciudad Nova: el cerro con la torre de antenas y edificios con pocas luces."""
    w = 3000
    img = lienzo(w, 1080)
    d = ImageDraw.Draw(img)
    silueta = (30, 22, 46, 255)
    silueta2 = (38, 28, 58, 255)
    # Cerro y torre (el emblema de la ciudad en las ilustraciones oficiales).
    poli(d, [(1150, 760), (1420, 520), (1560, 470), (1700, 520), (2050, 760)], silueta, ink=None)
    caja(d, 1552, 250, 1568, 480, silueta, ink=None)
    poli(d, [(1530, 480), (1560, 300), (1590, 480)], silueta, ink=None)
    caja(d, 1540, 330, 1580, 345, silueta, ink=None)
    caja(d, 1535, 380, 1585, 398, silueta, ink=None)
    circ(d, 1560, 246, 6, RUMOR, ink=None)
    x = 0
    while x < w:
        bw = random.randint(70, 170)
        bh = random.randint(120, 330)
        if 1250 < x < 1850:
            bh = random.randint(60, 140)
        col = random.choice((silueta, silueta2))
        caja(d, x, 800 - bh, x + bw, 800, col, ink=None)
        for yy in range(800 - bh + 18, 790, 26):
            for xx in range(x + 12, x + bw - 12, 22):
                if random.random() < 0.13:
                    caja(d, xx, yy, xx + 9, yy + 12, (232, 176, 75, 170), ink=None)
        x += bw + random.randint(0, 14)
    d.rectangle(s(0, 790, w, 1080), fill=silueta2)
    return guardar(img, "calle_lejos")


TIENDAS = ("FARMACIA", "PANADERÍA", "TIENDA 24 H", "LAVANDERÍA", "ÓPTICA", "FERRETERÍA", "CAFÉ", "PAPELERÍA",
           "BARBERÍA", "FRUTAS")


def medio():
    """Fachadas a pie de calle: ventanas, tiendas con toldo y una valla con la publicacion del rumor."""
    w = 4600
    img = lienzo(w, 1080)
    d = ImageDraw.Draw(img)
    fachadas = [(46, 37, 70), (58, 46, 85), (51, 40, 76), (66, 53, 95), (44, 36, 66)]
    x, k = -20, 0
    while x < w:
        bw = random.randint(330, 520)
        alto = random.randint(430, 720)
        col = fachadas[k % len(fachadas)] + (255,)
        top = ACERA - alto
        caja(d, x, top, x + bw, ACERA + 4, col, w=5)
        caja(d, x - 8, top - 18, x + bw + 8, top + 4, mezcla(col, (20, 15, 30), 0.35), w=5)
        # Ventanas.
        for yy in range(top + 50, ACERA - 230, 104):
            for xx in range(x + 34, x + bw - 70, 92):
                luz = random.random() < 0.36
                caja(d, xx, yy, xx + 56, yy + 72, (232, 176, 75, 255) if luz else VENTANA_OSC, w=4)
                if luz and random.random() < 0.5:
                    caja(d, xx + 4, yy + 4, xx + 52, yy + 30, (208, 150, 64, 255), ink=None)
                d.line(s(xx + 28, yy, xx + 28, yy + 72), fill=TINTA, width=3 * S)
        # Planta baja: tienda con toldo a rayas y rotulo.
        t_y = ACERA - 190
        caja(d, x + 24, t_y + 60, x + bw - 24, ACERA, (30, 24, 44, 255), w=5)
        vitrina = random.random() < 0.6
        caja(d, x + 44, t_y + 84, x + bw - 44, ACERA - 6, (232, 176, 75, 200) if vitrina else VENTANA_OSC, w=4)
        franjas = 9
        ancho_f = (bw - 30) / franjas
        for i in range(franjas):
            c = VINO if i % 2 == 0 else (230, 220, 232, 255)
            poli(d, [(x + 15 + i * ancho_f, t_y + 20), (x + 15 + (i + 1) * ancho_f, t_y + 20),
                     (x + 15 + (i + 1) * ancho_f + 6, t_y + 66), (x + 15 + i * ancho_f + 6, t_y + 66)], c, ink=None)
        poli(d, [(x + 15, t_y + 20), (x + bw - 15, t_y + 20), (x + bw - 9, t_y + 66), (x + 21, t_y + 66)], None, w=4)
        rot = TIENDAS[k % len(TIENDAS)]
        caja(d, x + bw / 2 - 120, t_y - 34, x + bw / 2 + 120, t_y + 8, PAPEL, w=4, r=4)
        texto(d, x + bw / 2, t_y - 13, rot, 24, TINTA, grueso=0.6, borde=TINTA)
        if rot == "FARMACIA":
            caja(d, x + bw - 70, t_y - 110, x + bw - 20, t_y - 60, TEAL, w=4)
            caja(d, x + bw - 52, t_y - 102, x + bw - 38, t_y - 68, PAPEL, ink=None)
            caja(d, x + bw - 62, t_y - 92, x + bw - 28, t_y - 78, PAPEL, ink=None)
        x += bw
        k += 1
    # Valla publicitaria con la publicacion del rumor (la misma estetica de CivitasNet).
    vx, vy = 2050, 150
    caja(d, vx + 150, vy + 260, vx + 170, vy + 420, TINTA, ink=None)
    caja(d, vx + 450, vy + 260, vx + 470, vy + 420, TINTA, ink=None)
    caja(d, vx, vy, vx + 620, vy + 270, PAPEL, w=7, r=6)
    caja(d, vx + 7, vy + 7, vx + 27, vy + 263, RUMOR, ink=None)
    texto(d, vx + 50, vy + 50, "CIVITAS · TENDENCIA", 22, VINO, anchor="lm", grueso=0.5, borde=VINO)
    texto(d, vx + 50, vy + 115, "#AguaEnvenenada", 54, TINTA, anchor="lm", grueso=1.2, borde=TINTA)
    texto(d, vx + 50, vy + 180, "NO TOMEN AGUA DEL GRIFO", 30, RUMOR, anchor="lm", grueso=0.8, borde=RUMOR)
    texto(d, vx + 50, vy + 228, "48.200 reposts", 22, (139, 132, 168, 255), anchor="lm")
    # Acera.
    d.rectangle(s(0, ACERA, w, CALZADA), fill=(52, 42, 76, 255))
    d.line(s(0, ACERA, w, ACERA), fill=TINTA, width=5 * S)
    for xx in range(0, w, 160):
        d.line(s(xx, ACERA + 4, xx - 14, CALZADA), fill=(44, 35, 64, 255), width=3 * S)
    return guardar(img, "calle_medio")


def via():
    w = ANCHO_CALLE
    img = lienzo(w, 1080)
    d = ImageDraw.Draw(img)
    d.rectangle(s(0, CALZADA, w, 1080), fill=(27, 22, 40, 255))
    d.rectangle(s(0, CALZADA, w, CALZADA + 14), fill=(66, 55, 96, 255))
    d.line(s(0, CALZADA + 14, w, CALZADA + 14), fill=TINTA, width=5 * S)
    for xx in range(0, w, 220):
        caja(d, xx, 1000, xx + 120, 1012, (201, 184, 216, 120), ink=None)
    for _ in range(40):
        x, y = random.randint(0, w), random.randint(CALZADA + 30, 1070)
        caja(d, x, y, x + random.randint(30, 90), y + 3, (36, 29, 52, 255), ink=None)
    return guardar(img, "calle_via")


def primer_plano():
    """Postes, semaforo y bolardos en silueta, delante de todo (parallax rapido)."""
    w = 5800
    img = lienzo(w, 1080)
    d = ImageDraw.Draw(img)
    sil = (11, 8, 17, 255)
    for x in (300, 3050):
        caja(d, x, 120, x + 18, 1080, sil, ink=None)
        poli(d, [(x + 9, 120), (x + 190, 98), (x + 194, 110), (x + 18, 134)], sil, ink=None)
        caja(d, x + 160, 104, x + 236, 122, sil, ink=None)
        caja(d, x + 170, 120, x + 226, 127, (232, 176, 75, 255), ink=None)
    # Semaforo en rojo.
    sx = 1900
    caja(d, sx, 300, sx + 16, 1080, sil, ink=None)
    caja(d, sx - 26, 300, sx + 42, 500, sil, ink=None, r=8)
    circ(d, sx + 8, 338, 22, RUMOR, ink=None)
    circ(d, sx + 8, 398, 22, (40, 30, 34, 255), ink=None)
    circ(d, sx + 8, 458, 22, (30, 40, 36, 255), ink=None)
    for x in range(700, w, 900):
        caja(d, x, 960, x + 46, 1080, sil, ink=None, r=10)
    return guardar(img, "calle_primer_plano")


# ------------------------------------------------------------------ vehiculos (vista lateral, hacia la derecha)
def ruedas(d, xs, base, r=34):
    for cx in xs:
        circ(d, cx, base - r, r, (20, 16, 28, 255), w=5)
        circ(d, cx, base - r, r * 0.45, (110, 100, 140, 255), w=4)


def sedan(nombre, color, taxi=False):
    w, h = 430, 190
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    base = 182
    oscuro = mezcla(color, (10, 8, 16), 0.35)
    poli(d, [(110, 78), (150, 26), (300, 26), (345, 78)], color)
    poli(d, [(126, 74), (158, 36), (220, 36), (220, 74)], VIDRIO, w=3)
    poli(d, [(232, 74), (232, 36), (294, 36), (326, 74)], VIDRIO, w=3)
    poli(d, [(162, 40), (176, 40), (150, 70), (136, 70)], VIDRIO_LUZ, ink=None)
    caja(d, 12, 74, 418, 150, color, w=5, r=22)
    caja(d, 14, 122, 416, 148, oscuro, ink=None, r=14)
    caja(d, 12, 74, 418, 150, None, w=5, r=22)
    d.line(s(225, 80, 225, 140), fill=TINTA, width=3 * S)
    caja(d, 396, 92, 418, 110, (251, 236, 190, 255), w=3, r=4)
    caja(d, 12, 90, 30, 112, RUMOR, w=3, r=4)
    if taxi:
        caja(d, 196, 6, 262, 28, AMBAR, w=4, r=4)
        texto(d, 229, 17, "TAXI", 14, TINTA, grueso=0.4, borde=TINTA)
        for i in range(10):
            c = TINTA if i % 2 == 0 else PAPEL
            caja(d, 60 + i * 30, 112, 90 + i * 30, 122, c, ink=None)
    ruedas(d, (92, 336), base)
    return guardar(img, nombre)


def bus():
    w, h = 980, 360
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    base = 350
    col = (47, 132, 122, 255)
    caja(d, 10, 20, 970, 300, col, w=6, r=26)
    caja(d, 12, 228, 968, 298, mezcla(col, (10, 8, 16), 0.35), ink=None, r=20)
    caja(d, 10, 20, 970, 300, None, w=6, r=26)
    for i in range(8):
        x = 60 + i * 108
        caja(d, x, 60, x + 92, 170, VIDRIO, w=4, r=6)
        if i % 3 == 1:
            caja(d, x + 10, 70, x + 40, 160, VIDRIO_LUZ, ink=None)
    caja(d, 900, 50, 962, 200, VIDRIO, w=4, r=6)
    caja(d, 860, 28, 960, 52, (24, 20, 34, 255), w=3)
    texto(d, 910, 40, "12 CENTRO", 15, AMBAR, grueso=0.3, borde=AMBAR)
    caja(d, 946, 214, 968, 236, (251, 236, 190, 255), w=3, r=4)
    caja(d, 10, 214, 28, 250, RUMOR, w=3, r=4)
    ruedas(d, (150, 820), base, r=42)
    return guardar(img, "bus")


def ambulancia():
    w, h = 700, 330
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    base = 320
    blanco = (236, 230, 236, 255)
    sombra = (196, 186, 204, 255)
    # Modulo trasero (caja) y cabina.
    caja(d, 14, 52, 492, 262, blanco, w=6, r=14)
    poli(d, [(486, 110), (586, 110), (654, 176), (678, 186), (678, 262), (486, 262)], blanco, w=6)
    poli(d, [(500, 122), (578, 122), (634, 176), (500, 176)], VIDRIO, w=4)
    poli(d, [(520, 128), (536, 128), (512, 170), (502, 170)], VIDRIO_LUZ, ink=None)
    caja(d, 16, 222, 676, 260, sombra, ink=None)
    # Franja roja y rotulo.
    caja(d, 14, 168, 678, 196, RUMOR, ink=None)
    d.line(s(14, 168, 678, 168), fill=TINTA, width=3 * S)
    d.line(s(14, 196, 678, 196), fill=TINTA, width=3 * S)
    texto(d, 250, 140, "AMBULANCIA", 40, VINO, grueso=1.0, borde=VINO)
    texto(d, 600, 214, "12", 26, TINTA, grueso=0.6, borde=TINTA)
    # Estrella de la vida, simplificada (seis brazos).
    cx, cy = 92, 110
    for ang in (0, 60, 120):
        a = math.radians(ang)
        dx, dy = math.cos(a) * 34, math.sin(a) * 34
        px, py = -math.sin(a) * 11, math.cos(a) * 11
        poli(d, [(cx - dx - px, cy - dy - py), (cx + dx - px, cy + dy - py), (cx + dx + px, cy + dy + py),
                 (cx - dx + px, cy - dy + py)], FRENO, ink=None)
    circ(d, cx, cy, 6, blanco, ink=None)
    # Ventana trasera y puerta.
    caja(d, 380, 72, 470, 150, VIDRIO, w=4, r=6)
    d.line(s(372, 60, 372, 258), fill=TINTA, width=3 * S)
    # Barra de luces (apagada: las luces encendidas son capas aparte).
    caja(d, 150, 30, 250, 54, (120, 40, 52, 255), w=4, r=5)
    caja(d, 250, 30, 350, 54, (40, 70, 104, 255), w=4, r=5)
    caja(d, 654, 196, 678, 220, (251, 236, 190, 255), w=3, r=4)
    caja(d, 14, 200, 30, 236, RUMOR, w=3, r=4)
    caja(d, 0, 250, 700, 262, None, ink=None)
    caja(d, 14, 52, 492, 262, None, w=6, r=14)
    ruedas(d, (130, 560), base, r=40)
    return guardar(img, "ambulancia")


def brillo(nombre, color, rx, ry, capas=6):
    """Halo de luz: elipses concentricas de poca opacidad (sin degradado continuo)."""
    w, h = int(rx * 2.2), int(ry * 2.2)
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    for i in range(capas):
        k = 1 - i / capas
        a = int(26 + 34 * i / capas)
        d.ellipse(s(w / 2 - rx * k, h / 2 - ry * k, w / 2 + rx * k, h / 2 + ry * k), fill=color[:3] + (a,))
    return guardar(img, nombre)


# ------------------------------------------------------------------ barricada y manifestantes
def barricada():
    w, h = 980, 470
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    base = 455
    # Llantas apiladas.
    for cx, cy in ((120, 410), (210, 410), (165, 350), (800, 410), (885, 410), (842, 350)):
        circ(d, cx, cy, 48, (24, 19, 32, 255), w=5)
        circ(d, cx, cy, 20, (50, 42, 66, 255), w=4)
    # Vallas de madera a rayas.
    for x0 in (250, 520):
        caja(d, x0 + 10, 280, x0 + 26, base, (90, 62, 50, 255), w=4)
        caja(d, x0 + 214, 280, x0 + 230, base, (90, 62, 50, 255), w=4)
        caja(d, x0, 270, x0 + 240, 318, PAPEL, w=5)
        for i in range(6):
            poli(d, [(x0 + i * 40, 272), (x0 + i * 40 + 20, 272), (x0 + i * 40 + 4, 316), (x0 + i * 40 - 16, 316)],
                 RUMOR, ink=None)
        caja(d, x0, 270, x0 + 240, 318, None, w=5)
        caja(d, x0, 350, x0 + 240, 380, (90, 62, 50, 255), w=4)
    # Pancarta entre dos palos.
    caja(d, 270, 40, 284, 280, (90, 62, 50, 255), w=4)
    caja(d, 716, 40, 730, 280, (90, 62, 50, 255), w=4)
    poli(d, [(284, 60), (716, 52), (716, 190), (284, 200)], PAPEL, w=5)
    texto(d, 500, 105, "¡NOS ESTÁN", 42, TINTA, grueso=1.0, borde=TINTA)
    texto(d, 500, 158, "ENVENENANDO!", 50, RUMOR, grueso=1.2, borde=RUMOR)
    # Cono.
    poli(d, [(450, base), (478, 380), (500, 380), (528, base)], (232, 120, 60, 255))
    caja(d, 462, 410, 516, 424, PAPEL, ink=None)
    return guardar(img, "barricada")


CARTELES = ("AGUA LIMPIA YA", "NOS MIENTEN", "#AguaEnvenenada", "¿Y EL ALCALDE?", "NO PASA NADIE", None)


def persona(nombre, alto, cartel, brazo_arriba, color_ropa):
    w, h = 240, 470
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    pie = h - 6
    cuerpo = color_ropa
    cabeza = 30
    hombro = pie - alto + cabeza * 2 + 8
    cx = 120
    # Piernas.
    caja(d, cx - 28, pie - alto * 0.42, cx - 4, pie, (22, 18, 32, 255), w=4, r=6)
    caja(d, cx + 4, pie - alto * 0.42, cx + 28, pie, (22, 18, 32, 255), w=4, r=6)
    # Torso.
    caja(d, cx - 40, hombro, cx + 40, pie - alto * 0.38, cuerpo, w=5, r=18)
    # Cabeza (en silueta: sin rasgos).
    circ(d, cx, hombro - cabeza - 2, cabeza, (30, 24, 42, 255), w=4)
    d.arc(s(cx - cabeza, hombro - cabeza * 2 - 2, cx + cabeza, hombro - 2), 200, 320, fill=LILA, width=3 * S)
    if cartel:
        # Brazos arriba sosteniendo un carton.
        y_c = hombro - (110 if brazo_arriba else 60)
        caja(d, cx - 46, y_c + 30, cx - 32, hombro + 20, cuerpo, w=4, r=6)
        caja(d, cx + 32, y_c + 30, cx + 46, hombro + 20, cuerpo, w=4, r=6)
        tam = 22 if len(cartel) > 10 else 28
        ancho = max(150, len(cartel) * tam * 0.62 + 30)
        caja(d, cx - ancho / 2, y_c - 50, cx + ancho / 2, y_c + 34, (236, 222, 196, 255), w=5)
        texto(d, cx, y_c - 8, cartel, tam, VINO if cartel[0] != "#" else RUMOR, grueso=0.7,
              borde=VINO if cartel[0] != "#" else RUMOR)
    else:
        # Puno en alto.
        caja(d, cx + 30, hombro - 90, cx + 46, hombro + 20, cuerpo, w=4, r=6)
        circ(d, cx + 38, hombro - 96, 13, (30, 24, 42, 255), w=4)
        caja(d, cx - 46, hombro + 10, cx - 32, hombro + 120, cuerpo, w=4, r=6)
    return guardar(img, nombre)


# ------------------------------------------------------------------ interior de la ambulancia
def interior():
    img = lienzo(1920, 1080)
    d = ImageDraw.Draw(img)
    pared = (52, 46, 74, 255)
    pared2 = (60, 54, 86, 255)
    d.rectangle(s(0, 0, 1920, 1080), fill=pared)
    # Techo con riel y luz.
    caja(d, -10, -10, 1930, 120, (40, 35, 58, 255), w=5)
    caja(d, 380, 40, 1500, 70, (201, 184, 216, 255), w=4, r=10)
    caja(d, 200, 112, 1700, 128, (90, 84, 116, 255), w=4)
    # Armarios a la derecha y abajo.
    for i in range(3):
        caja(d, 1240 + i * 220, 170, 1440 + i * 220, 420, pared2, w=5, r=8)
        caja(d, 1320 + i * 220, 280, 1360 + i * 220, 296, (110, 100, 140, 255), w=3, r=4)
    caja(d, 1240, 440, 1900, 470, (40, 35, 58, 255), w=4)
    # Ventanas de las puertas traseras (izquierda): por ahi entra la luz de la sirena.
    caja(d, 60, 200, 330, 560, (36, 30, 52, 255), w=6, r=10)
    caja(d, 90, 230, 300, 420, (16, 12, 26, 255), w=5, r=8)
    # Luces de la ciudad desenfocadas tras el vidrio (circulos planos).
    for cx, cy, r, c in ((140, 300, 18, AMBAR), (220, 350, 12, AMBAR), (260, 270, 9, LILA), (120, 380, 10, RUMOR)):
        circ(d, cx, cy, r, c[:3] + (150,), ink=None)
    d.line(s(330, 160, 330, 1080), fill=TINTA, width=6 * S)
    # Bombona de oxigeno.
    caja(d, 360, 420, 430, 820, TEAL, w=5, r=30)
    caja(d, 378, 392, 412, 426, (90, 84, 116, 255), w=4)
    # Suelo.
    d.rectangle(s(0, 900, 1920, 1080), fill=(34, 29, 48, 255))
    d.line(s(0, 900, 1920, 900), fill=TINTA, width=6 * S)
    for x in range(0, 1920, 120):
        d.line(s(x, 900, x - 60, 1080), fill=(42, 36, 60, 255), width=3 * S)
    # Soporte del monitor en la pared (el monitor se dibuja aparte, con su senal viva).
    caja(d, 1150, 500, 1840, 520, (40, 35, 58, 255), w=4)
    return guardar(img, "interior_fondo")


def camilla():
    """Paciente cubierto con una manta: no se ve el rostro (fuera de cuadro, a la izquierda)."""
    w, h = 1500, 520
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    metal = (150, 140, 170, 255)
    # Patas y estructura.
    for x in (180, 1320):
        caja(d, x, 330, x + 22, 480, metal, w=4)
        circ(d, x + 11, 490, 22, (20, 16, 28, 255), w=4)
    caja(d, 120, 300, 1420, 340, metal, w=5, r=8)
    # Colchon.
    caja(d, 100, 250, 1440, 310, (220, 214, 228, 255), w=5, r=16)
    # Almohada y cabeza vista desde atras (pelo, sin rostro), con la cinta de la mascarilla.
    caja(d, 110, 150, 330, 262, (238, 232, 240, 255), w=5, r=40)
    circ(d, 220, 150, 70, (46, 36, 56, 255), w=5)
    d.arc(s(150, 80, 290, 220), 200, 330, fill=(90, 74, 104, 255), width=6 * S)
    d.line(s(160, 168, 286, 128), fill=(200, 220, 230, 255), width=5 * S)
    d.line(s(290, 150, 420, 40), fill=(200, 220, 230, 255), width=5 * S)
    # Cuerpo bajo la manta: hombro, torso, caderas y piernas (formas suaves, sin detalle).
    poli(d, [(270, 252), (290, 150), (360, 96), (520, 70), (700, 96), (860, 128), (1010, 150), (1180, 170),
             (1330, 186), (1420, 252)], (52, 112, 140, 255), w=5)
    for x0, y0, x1, y1 in ((520, 80, 560, 240), (840, 130, 880, 244), (1100, 162, 1130, 246)):
        d.line(s(x0, y0, x1, y1), fill=(38, 88, 114, 255), width=5 * S)
    caja(d, 270, 214, 1420, 252, (238, 232, 240, 255), w=4)
    # Brazo del paciente sobre la manta, con la pinza del pulsioximetro y la via.
    poli(d, [(420, 150), (800, 168), (806, 198), (414, 186)], (226, 190, 170, 255), w=4)
    caja(d, 800, 160, 850, 204, (40, 35, 58, 255), w=4, r=8)
    circ(d, 840, 182, 5, RUMOR, ink=None)
    d.line(s(850, 182, 1000, 0), fill=(120, 110, 150, 255), width=4 * S)
    caja(d, 560, 150, 600, 184, PAPEL, w=3)
    d.line(s(580, 150, 560, 0), fill=(180, 200, 220, 255), width=4 * S)
    return guardar(img, "interior_camilla")


def paramedico():
    """Paramedica de espaldas en silueta, con la franja reflectante del uniforme."""
    w, h = 620, 900
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    ropa = (28, 50, 78, 255)
    circ(d, 330, 150, 92, (22, 18, 32, 255), w=6)
    caja(d, 250, 50, 420, 130, (22, 18, 32, 255), ink=None, r=40)
    poli(d, [(160, 300), (300, 240), (380, 240), (520, 300), (580, 900), (100, 900)], ropa, w=6)
    caja(d, 130, 560, 560, 600, (210, 220, 120, 255), ink=None)
    caja(d, 120, 640, 570, 660, (180, 190, 200, 255), ink=None)
    poli(d, [(160, 300), (300, 240), (380, 240), (520, 300), (580, 900), (100, 900)], None, w=6)
    # Brazo extendido hacia el paciente.
    poli(d, [(480, 330), (610, 470), (590, 510), (450, 400)], ropa, w=5)
    circ(d, 604, 492, 26, (60, 130, 160, 255), w=5)
    return guardar(img, "interior_paramedico")


def suero():
    w, h = 160, 420
    img = lienzo(w, h)
    d = ImageDraw.Draw(img)
    d.line(s(80, 0, 80, 40), fill=(150, 140, 170, 255), width=5 * S)
    caja(d, 30, 40, 130, 220, (210, 226, 238, 210), w=5, r=22)
    caja(d, 38, 110, 122, 212, (160, 196, 222, 200), ink=None, r=16)
    caja(d, 64, 220, 96, 250, (150, 140, 170, 255), w=4)
    d.line(s(80, 250, 80, 420), fill=(180, 200, 220, 255), width=4 * S)
    return guardar(img, "interior_suero")


# ------------------------------------------------------------------ monitor de signos vitales
def monitor_marco():
    """Carcasa del monitor (1920 x 1080) con la pantalla recortada: la senal se dibuja detras, en vivo."""
    img = lienzo(1920, 1080)
    d = ImageDraw.Draw(img)
    caja(d, 40, 40, 1880, 1040, (58, 52, 80, 255), w=8, r=46)
    caja(d, 64, 64, 1856, 1016, (46, 41, 64, 255), ink=None, r=34)
    # Hueco de la pantalla (transparente).
    d.rounded_rectangle(s(120, 110, 1800, 900), radius=18 * S, fill=(0, 0, 0, 0), outline=TINTA, width=8 * S)
    # Botonera.
    for i in range(6):
        caja(d, 160 + i * 130, 940, 260 + i * 130, 990, (74, 66, 100, 255), w=5, r=12)
    circ(d, 1660, 962, 34, (74, 66, 100, 255), w=6)
    d.line(s(1660, 940, 1660, 962), fill=TINTA, width=6 * S)
    texto(d, 1360, 965, "CN-MED 300", 30, (139, 132, 168, 255), grueso=0.4, borde=(139, 132, 168, 255))
    caja(d, 1500, 946, 1540, 978, (60, 40, 46, 255), w=4, r=8)   # LED de alarma (se enciende aparte)
    return guardar(img, "monitor_marco")


def icono_bloqueo():
    img = lienzo(80, 80)
    d = ImageDraw.Draw(img)
    circ(d, 40, 40, 34, RUMOR, w=5)
    caja(d, 18, 33, 62, 47, PAPEL, ink=None, r=3)
    return guardar(img, "icono_bloqueo")


def icono_ambulancia():
    img = lienzo(90, 90)
    d = ImageDraw.Draw(img)
    circ(d, 45, 45, 38, PAPEL, w=5)
    caja(d, 37, 22, 53, 68, RUMOR, ink=None)
    caja(d, 22, 37, 68, 53, RUMOR, ink=None)
    return guardar(img, "icono_ambulancia")


def main():
    cielo()
    lejos()
    medio()
    via()
    primer_plano()
    sedan("auto_vino", VINO)
    sedan("auto_azul", FRENO)
    sedan("auto_lila", (150, 136, 176, 255))
    sedan("auto_gris", (98, 92, 118, 255))
    sedan("taxi", AMBAR, taxi=True)
    bus()
    ambulancia()
    brillo("luz_roja", RUMOR, 190, 120)
    brillo("luz_azul", (90, 160, 230, 255), 190, 120)
    brillo("luz_freno", RUMOR, 60, 36, capas=4)
    barricada()
    ropas = [(70, 52, 96, 255), (96, 46, 70, 255), (44, 70, 96, 255), (80, 70, 60, 255), (60, 60, 84, 255),
             (100, 60, 52, 255)]
    for i in range(8):
        persona("persona_%d" % i, random.randint(330, 400), CARTELES[i % len(CARTELES)], i % 2 == 0, ropas[i % len(ropas)])
    interior()
    camilla()
    paramedico()
    suero()
    monitor_marco()
    icono_bloqueo()
    icono_ambulancia()
    print("ok:", OUT)


if __name__ == "__main__":
    main()
