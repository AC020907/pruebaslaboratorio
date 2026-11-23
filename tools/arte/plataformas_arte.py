"""Arte de la Ruta de la Verdad (plataformero), generado de forma reproducible.

    python tools/arte/plataformas_arte.py

Escribe game/gui/plataformas/v2/*.png. Estilo de Civitas: formas planas, contorno de tinta (#2b2440),
paleta de la interfaz, sin brillos ni degradados. Todo se dibuja al doble (o cuadruple) del tamano en
pantalla y se muestra reducido, para que el contorno quede limpio.

No toca ningun personaje oficial: el protagonista del plataformero es un avatar propio del minijuego.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(RAIZ, "game", "gui", "plataformas", "v2")
FUENTE = os.path.join(RAIZ, "game", "fonts", "Roboto-Regular.ttf")

TINTA = (43, 36, 64, 255)
NOCHE = (18, 13, 28, 255)
PAPEL = (251, 246, 238, 255)
LILA = (201, 184, 216, 255)
MORADO = (58, 51, 80, 255)
MORADO2 = (74, 63, 102, 255)
MORADO3 = (96, 84, 128, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
TEAL = (47, 158, 143, 255)
AMBAR = (232, 176, 75, 255)
FRENO = (61, 126, 166, 255)
PIEL = (246, 214, 186, 255)
PELO = (52, 40, 66, 255)

T = 144          # tile a 2x (en pantalla 72 px)
L = 7            # grosor del contorno a 2x


def lienzo(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def guardar(img, nombre):
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, nombre + ".png"), optimize=True)


# ------------------------------------------------------------------ tiles solidos (autotiling 4 bits)
CUERPO = (58, 48, 84, 255)       # parte alta del bloque (bajo la pasarela)
CUERPO_M = (50, 41, 74, 255)
HONDO = (40, 33, 60, 255)         # interior: mas oscuro, para que las masas grandes tengan profundidad
JUNTA = (32, 26, 50, 255)
LUZ = (84, 72, 118, 255)          # canto iluminado (luz de las pantallas, desde la izquierda)
SOMBRA = (30, 24, 46, 255)
PASARELA = (222, 212, 234, 255)


def solido(arriba, izq, der, abajo, variante):
    """Bloque de la infraestructura de NOVA (remaster 3). Con pasarela clara arriba, cuerpo en bandas
    planas que oscurecen hacia dentro, racks de servidor y cantos con luz y sombra. Los lados internos
    no llevan contorno: los bloques se unen sin costura."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    rnd = random.Random(variante * 7 + 3)
    if arriba:
        d.rectangle([0, 0, T, T], fill=HONDO)
        d.rectangle([0, 0, T, 96], fill=CUERPO_M)
        d.rectangle([0, 0, T, 60], fill=CUERPO)
    else:
        d.rectangle([0, 0, T, T], fill=HONDO)
    # rack: dos unidades por bloque, con ranura y LED
    for k, y in enumerate((44, 100)):
        if arriba and y < 40:
            continue
        d.rectangle([14, y, T - 14, y + 30], fill=JUNTA)
        d.rectangle([20, y + 6, T - 20, y + 10], fill=SOMBRA)
        d.rectangle([20, y + 18, T - 54, y + 22], fill=SOMBRA)
        led = rnd.random()
        col = TEAL if led < 0.30 else (AMBAR if led < 0.38 else (60, 52, 88, 255))
        d.rectangle([T - 44, y + 16, T - 32, y + 24], fill=col)
    # juntas verticales entre bloques (sutiles, siempre en el mismo sitio: no se nota la repeticion)
    d.rectangle([0, 0, 3, T], fill=JUNTA)
    if arriba:
        d.rectangle([0, 0, T, 34], fill=PASARELA)
        d.rectangle([0, 26, T, 34], fill=(186, 170, 206, 255))
        d.rectangle([0, 34, T, 34 + L], fill=TINTA)
        for x in range(8, T, 36):
            d.rectangle([x, 9, x + 18, 14], fill=(244, 238, 248, 255))
        if variante % 2 == 0:
            d.rectangle([T // 2 - 6, 40 + L, T // 2 + 6, 46 + L], fill=TEAL)
    if izq:
        d.rectangle([L, 0, L + 8, T], fill=LUZ)
        d.rectangle([0, 0, L, T], fill=TINTA)
    if der:
        d.rectangle([T - L - 10, 0, T - L, T], fill=SOMBRA)
        d.rectangle([T - L, 0, T, T], fill=TINTA)
    if abajo:
        d.rectangle([0, T - L - 8, T, T - L], fill=SOMBRA)
        d.rectangle([0, T - L, T, T], fill=TINTA)
    if arriba:
        d.rectangle([0, 0, T, L], fill=TINTA)
        if izq:
            d.polygon([(0, 0), (22, 0), (0, 22)], fill=(0, 0, 0, 0))
            d.line([(0, 22), (22, 0)], fill=TINTA, width=L)
        if der:
            d.polygon([(T, 0), (T - 22, 0), (T, 22)], fill=(0, 0, 0, 0))
            d.line([(T - 22, 0), (T, 22)], fill=TINTA, width=L)
    return im


# ------------------------------------------------------------------ peligros, bloques, objetos
def barrera(frame):
    """Barrera de interferencia: base con franjas de aviso (forma, no solo color) y estatica en dientes."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    base_y = T - 34
    d.rectangle([4, base_y, T - 4, T - 2], fill=TINTA)
    for i, x in enumerate(range(-20, T, 28)):
        d.polygon([(x, T - 6), (x + 14, base_y + 4), (x + 28, base_y + 4), (x + 14, T - 6)], fill=AMBAR)
    rnd = random.Random(frame * 31 + 7)
    puntos = [(6, base_y)]
    n = 6
    for i in range(n):
        x0 = 6 + (T - 12) * i / n
        alto = 46 + rnd.randint(-10, 14)
        puntos += [(x0 + (T - 12) / n / 2, base_y - alto), (x0 + (T - 12) / n, base_y)]
    d.polygon(puntos, fill=RUMOR, outline=TINTA)
    d.line(puntos + [puntos[0]], fill=TINTA, width=5, joint="curve")
    # chispas de estatica
    for _ in range(3):
        x, y = rnd.randint(16, T - 16), rnd.randint(base_y - 60, base_y - 30)
        d.line([(x - 6, y), (x + 6, y)], fill=PAPEL, width=4)
    return im


def inestable(estado):
    """Plataforma de datos que se apaga. on: solida con barra de carga; aviso: grietas y barra roja; off: fantasma."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    if estado == "off":
        for x in range(8, T - 8, 22):
            d.line([(x, 10), (x + 11, 10)], fill=LILA + (0,) if False else (201, 184, 216, 150), width=5)
            d.line([(x, T - 52), (x + 11, T - 52)], fill=(201, 184, 216, 150), width=5)
        d.line([(10, 10), (10, T - 52)], fill=(201, 184, 216, 110), width=4)
        d.line([(T - 10, 10), (T - 10, T - 52)], fill=(201, 184, 216, 110), width=4)
        return im
    d.rounded_rectangle([4, 4, T - 4, T - 48], radius=10, fill=MORADO3, outline=TINTA, width=L)
    d.rectangle([12, 12, T - 12, 30], fill=LILA)
    barra = RUMOR if estado == "aviso" else TEAL
    d.rectangle([20, 56, T - 20, 72], fill=TINTA)
    d.rectangle([24, 60, (T - 24) if estado == "on" else 60, 68], fill=barra)
    if estado == "aviso":
        d.line([(40, 6), (52, 30), (44, 44), (58, 64)], fill=TINTA, width=5)
        d.line([(100, 8), (92, 28), (104, 46)], fill=TINTA, width=5)
    # soportes
    d.rectangle([28, T - 48, 40, T - 30], fill=TINTA)
    d.rectangle([T - 40, T - 48, T - 28, T - 30], fill=TINTA)
    return im


def documento(sello=True):
    """Fragmento de evidencia: hoja con esquina doblada, lineas de texto y un sello."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 30, 18, 112, 124
    d.polygon([(x0, y0), (x1 - 24, y0), (x1, y0 + 24), (x1, y1), (x0, y1)], fill=PAPEL, outline=TINTA)
    d.line([(x0, y0), (x1 - 24, y0), (x1, y0 + 24), (x1, y1), (x0, y1), (x0, y0)], fill=TINTA, width=6, joint="curve")
    d.polygon([(x1 - 24, y0), (x1 - 24, y0 + 24), (x1, y0 + 24)], fill=LILA, outline=TINTA)
    d.line([(x1 - 24, y0), (x1 - 24, y0 + 24), (x1, y0 + 24)], fill=TINTA, width=5)
    for i, y in enumerate((48, 62, 76, 90)):
        d.line([(x0 + 12, y), (x1 - (30 if i == 3 else 14), y)], fill=MORADO3, width=5)
    if sello:
        d.ellipse([x1 - 40, y1 - 40, x1 - 6, y1 - 6], outline=RUMOR, width=5)
        d.line([(x1 - 32, y1 - 23), (x1 - 25, y1 - 16), (x1 - 14, y1 - 30)], fill=RUMOR, width=5)
    # clip
    d.rounded_rectangle([x0 + 18, y0 - 10, x0 + 30, y0 + 18], radius=6, outline=TINTA, width=5)
    return im


def antena(activa):
    """Punto de control: antena de la red ciudadana (apagada: gris; activa: bandera y ondas)."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    d.rectangle([60, 40, 82, T - 4], fill=MORADO2, outline=TINTA, width=5)
    d.rectangle([44, T - 20, 98, T - 2], fill=TINTA)
    cabeza = TEAL if activa else MORADO3
    d.ellipse([50, 18, 92, 54], fill=cabeza, outline=TINTA, width=6)
    if activa:
        d.polygon([(82, 56), (128, 70), (82, 86)], fill=TEAL, outline=TINTA)
        d.line([(82, 56), (128, 70), (82, 86)], fill=TINTA, width=5)
        for r in (34, 50):
            d.arc([71 - r, 36 - r, 71 + r, 36 + r], 200, 340, fill=TEAL, width=5)
    return im


def archivo():
    """Meta: la puerta del archivo original (2 tiles de alto), con letrero."""
    w, h = 216, 288
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([20, 40, w - 20, h - 4], fill=MORADO2, outline=TINTA, width=L)
    d.rectangle([48, 96, w - 48, h - 4], fill=NOCHE, outline=TINTA, width=L)
    d.rectangle([62, 110, w - 62, h - 18], fill=(36, 30, 54, 255))
    for y in range(126, h - 30, 26):
        d.rectangle([76, y, w - 76, y + 12], fill=PAPEL)
        d.rectangle([100, y + 3, w - 100, y + 9], fill=MORADO3)
    d.rounded_rectangle([12, 8, w - 12, 64], radius=10, fill=PAPEL, outline=TINTA, width=L)
    f = ImageFont.truetype(FUENTE, 30)
    texto = "ARCHIVO"
    tw = d.textlength(texto, font=f)
    d.text(((w - tw) / 2, 18), texto, font=f, fill=VINO)
    return im


# ------------------------------------------------------------------ protagonista (avatar del minijuego)
def avatar(pose, fase=0.0):
    """Lienzo 224 x 256 (4x de 56 x 64). Pies abajo al centro, como el sprite anterior (misma caja de juego)."""
    W, H = 224, 256
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    cx = W // 2
    suelo = H - 6
    bob = 0
    # angulos de piernas y brazos (grados desde la vertical; + hacia delante = derecha)
    if pose == "idle":
        pi, pd, bi, bd, bob = 4, -4, 8, -8, int(2 * math.sin(fase * math.pi))
    elif pose == "corre":
        a = math.sin(fase * 2 * math.pi)
        pi, pd = 38 * a, -38 * a
        bi, bd = -42 * a, 42 * a
        bob = -int(6 * abs(math.cos(fase * 2 * math.pi)))
    elif pose == "salto":
        pi, pd, bi, bd, bob = 30, -55, -150, -120, -6
    elif pose == "cae":
        pi, pd, bi, bd, bob = 18, -18, -125, 125, -2
    elif pose == "recoge":
        pi, pd, bi, bd, bob = 8, -8, -170, 170, -4
    elif pose == "dano":
        pi, pd, bi, bd, bob = 40, -10, -60, 100, 0
    elif pose == "victoria":
        pi, pd, bi, bd, bob = 10, -10, -160, 30, -8
    else:
        pi, pd, bi, bd = 0, 0, 0, 0
    cadera_y = suelo - 62 + bob
    hombro_y = cadera_y - 58

    def miembro(x, y, ang, largo, grosor, color, pie=False):
        r = math.radians(ang)
        x2, y2 = x + largo * math.sin(r), y + largo * math.cos(r)
        d.line([(x, y), (x2, y2)], fill=TINTA, width=grosor + 10)
        d.line([(x, y), (x2, y2)], fill=color, width=grosor)
        if pie:
            d.ellipse([x2 - 15, y2 - 9, x2 + 17, y2 + 9], fill=TINTA)
        else:
            d.ellipse([x2 - 10, y2 - 10, x2 + 10, y2 + 10], fill=PIEL, outline=TINTA, width=5)

    # pierna y brazo de atras (mas oscuros)
    miembro(cx - 8, cadera_y, pd, 52, 16, PELO, pie=True)
    miembro(cx - 10, hombro_y + 8, bd, 44, 13, (70, 60, 110, 255))
    # bufanda (la cola ondea detras)
    ondea = math.sin(fase * 2 * math.pi) * 8
    cola = [(cx - 14, hombro_y - 2), (cx - 52, hombro_y + 4 + ondea), (cx - 74, hombro_y - 6 - ondea),
            (cx - 66, hombro_y + 14 + ondea), (cx - 20, hombro_y + 14)]
    d.polygon(cola, fill=RUMOR, outline=TINTA)
    d.line(cola + [cola[0]], fill=TINTA, width=5, joint="curve")
    # torso: chaqueta del alcalde
    d.rounded_rectangle([cx - 28, hombro_y - 4, cx + 28, cadera_y + 8], radius=18, fill=(91, 79, 154, 255),
                        outline=TINTA, width=6)
    d.line([(cx, hombro_y + 6), (cx, cadera_y + 4)], fill=TINTA, width=4)
    d.rectangle([cx - 24, hombro_y - 8, cx + 24, hombro_y + 8], fill=RUMOR, outline=TINTA, width=5)
    # pierna y brazo de delante
    miembro(cx + 8, cadera_y, pi, 52, 16, (60, 50, 84, 255), pie=True)
    miembro(cx + 10, hombro_y + 8, bi, 44, 13, (110, 98, 176, 255))
    # cabeza
    hy = hombro_y - 44
    d.ellipse([cx - 40, hy - 40, cx + 40, hy + 40], fill=PIEL, outline=TINTA, width=6)
    d.chord([cx - 42, hy - 44, cx + 42, hy + 30], 180, 360, fill=PELO, outline=TINTA, width=6)
    d.polygon([(cx + 6, hy - 14), (cx + 40, hy - 10), (cx + 36, hy - 30)], fill=PELO)
    if pose == "dano":
        for ox in (6, 26):
            d.line([(cx + ox - 6, hy - 2), (cx + ox + 6, hy + 10)], fill=TINTA, width=5)
            d.line([(cx + ox + 6, hy - 2), (cx + ox - 6, hy + 10)], fill=TINTA, width=5)
    else:
        for ox in (8, 28):
            d.ellipse([cx + ox - 6, hy - 2, cx + ox + 6, hy + 12], fill=TINTA)
    if pose in ("victoria", "recoge"):
        d.arc([cx + 6, hy + 10, cx + 30, hy + 26], 10, 170, fill=TINTA, width=5)
    d.ellipse([cx + 30, hy + 12, cx + 40, hy + 20], fill=(240, 160, 160, 255))
    if pose == "recoge":
        hoja = documento(sello=False).resize((64, 64), Image.LANCZOS)
        im.alpha_composite(hoja, (cx - 32, hombro_y - 120))
    return im


# ------------------------------------------------------------------ fondos con parallax (remaster 3)
def bandas(d, w, y0, y1, colores):
    """Degradado en bandas planas (posterizado): profundidad sin romper el estilo plano."""
    n = len(colores)
    for i, c in enumerate(colores):
        d.rectangle([0, int(y0 + (y1 - y0) * i / n), w, int(y0 + (y1 - y0) * (i + 1) / n) + 1], fill=c)


def cielo():
    """Plano fijo: noche de Ciudad Nova en bandas y, al fondo, la senal de NOVA (disco con ondas)."""
    W, H = 1920, 1080
    im = Image.new("RGBA", (W, H), NOCHE)
    d = ImageDraw.Draw(im)
    bandas(d, W, 0, 760, [(18, 13, 28, 255), (22, 16, 36, 255), (28, 20, 44, 255), (36, 25, 52, 255),
                          (46, 30, 60, 255), (58, 36, 66, 255), (72, 42, 70, 255)])
    d.rectangle([0, 760, W, H], fill=(72, 42, 70, 255))
    cx, cy = 1340, 330
    capa = lienzo(W, H)
    c = ImageDraw.Draw(capa)
    for r, a in ((300, 18), (240, 26), (190, 34)):
        c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(201, 184, 216, a), width=4)
    c.ellipse([cx - 140, cy - 140, cx + 140, cy + 140], fill=(201, 184, 216, 46))
    c.ellipse([cx - 104, cy - 104, cx + 104, cy + 104], fill=(209, 73, 91, 40))
    c.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(251, 246, 238, 70))
    im.alpha_composite(capa)
    rnd = random.Random(3)
    for _ in range(90):
        x, y = rnd.randint(0, W), rnd.randint(0, 520)
        t = rnd.choice((2, 2, 3))
        d.rectangle([x, y, x + t, y + t], fill=(201, 184, 216, rnd.randint(60, 140)))
    return im


def silueta(d, x, w, top, base, color, ventanas, rnd):
    d.rectangle([x, top, x + w, base], fill=color)
    if rnd.random() < 0.4:
        d.rectangle([x + w // 4, top - rnd.randint(30, 70), x + w // 4 + 8, top], fill=color)
    for yy in range(top + 24, base - 20, 34):
        for xx in range(x + 12, x + w - 16, 26):
            v = rnd.random()
            if v < ventanas:
                d.rectangle([xx, yy, xx + 10, yy + 14], fill=(232, 176, 75, 150) if v < ventanas * 0.35 else (201, 184, 216, 90))


def fondo_lejos():
    """Ciudad Nova a lo lejos (silueta en dos planos, la torre del cerro), con bruma en el horizonte.
    Enlaza sin costura: 3840 px, se dibuja dos veces."""
    W, H = 3840, 1080
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    for base in (0, 1920):
        d.polygon([(base + 900, 760), (base + 1180, 560), (base + 1420, 600), (base + 1700, 760)], fill=(46, 32, 62, 255))
        d.rectangle([base + 1178, 330, base + 1186, 560], fill=(46, 32, 62, 255))
        d.rectangle([base + 1166, 420, base + 1198, 438], fill=(46, 32, 62, 255))
        d.ellipse([base + 1176, 318, base + 1188, 330], fill=(209, 73, 91, 200))
    for fila, (color, alto, vent) in enumerate((((44, 31, 60, 255), (160, 330), 0.10), ((34, 25, 50, 255), (120, 260), 0.16))):
        rnd = random.Random(40 + fila)
        x = -60
        while x < W:
            w = rnd.randint(70, 170)
            top = 760 + fila * 60 - rnd.randint(*alto)
            silueta(d, x, w, top, H, color, vent, rnd)
            x += w + rnd.randint(-10, 24)
    # bruma: bandas claras sobre la base de la ciudad
    for i, a in enumerate((36, 26, 16)):
        d.rectangle([0, 760 + i * 40, W, 800 + i * 40], fill=(201, 184, 216, a))
    return im


def fondo_medio():
    """Torres de NOVA (plano medio, 0.35): oscuras, con canto iluminado, ventanas y pantallas del rumor
    que brillan. Sin velo encima: el contraste lo dan los colores."""
    W, H = 3840, 1080
    im = lienzo(W, H)
    brillo = lienzo(W, H)
    d = ImageDraw.Draw(im)
    g = ImageDraw.Draw(brillo)
    rnd = random.Random(11)
    textos = ("#AguaEnvenenada", "COMPARTE YA", "Los medios callan", "18.900 reposts", "NO LA TOMEN")
    x = 0
    while x < W - 200:
        w = rnd.randint(170, 280)
        h = rnd.randint(380, 700)
        top = H - h
        d.rectangle([x, top, x + w, H], fill=(29, 22, 44, 255), outline=TINTA, width=6)
        d.rectangle([x + 6, top + 6, x + 14, H], fill=(58, 48, 86, 255))
        d.rectangle([x, top, x + w, top + 18], fill=(40, 32, 60, 255), outline=TINTA, width=6)
        for yy in range(top + 46, H - 30, 40):
            for xx in range(x + 26, x + w - 26, 30):
                v = rnd.random()
                if v < 0.07:
                    d.rectangle([xx, yy, xx + 14, yy + 18], fill=(38, 112, 104, 255))
                elif v < 0.11:
                    d.rectangle([xx, yy, xx + 14, yy + 18], fill=(150, 112, 62, 255))
                elif v < 0.55:
                    d.rectangle([xx, yy, xx + 14, yy + 18], fill=(22, 16, 34, 255))
        if rnd.random() < 0.6 and w > 190:
            sy = top + 64
            g.rectangle([x + 2, sy - 16, x + w - 2, sy + 126], fill=(209, 73, 91, 46))
            g.rectangle([x + 10, sy - 8, x + w - 10, sy + 118], fill=(209, 73, 91, 40))
            d.rectangle([x + 18, sy, x + w - 18, sy + 110], fill=(238, 230, 242, 255), outline=TINTA, width=6)
            d.rectangle([x + 18, sy, x + 30, sy + 110], fill=RUMOR)
            t = rnd.choice(textos)
            fs = 28
            while fs > 12 and d.textlength(t, font=ImageFont.truetype(FUENTE, fs)) > w - 70:
                fs -= 2
            d.text((x + 42, sy + 16), "@verdad.oculta", font=ImageFont.truetype(FUENTE, 18), fill=VINO)
            d.text((x + 42, sy + 50), t, font=ImageFont.truetype(FUENTE, fs), fill=TINTA)
        if rnd.random() < 0.45:
            d.line([(x + w // 2, top), (x + w // 2, top - 80)], fill=TINTA, width=6)
            g.ellipse([x + w // 2 - 26, top - 106, x + w // 2 + 26, top - 54], fill=(209, 73, 91, 60))
            d.ellipse([x + w // 2 - 11, top - 91, x + w // 2 + 11, top - 69], fill=RUMOR, outline=TINTA, width=4)
        x += w + rnd.randint(40, 110)
    brillo.alpha_composite(im)
    return brillo


def vineta():
    """Vineta suave hacia las esquinas: centra la mirada en la zona de juego."""
    g = Image.radial_gradient("L").resize((960, 540), Image.BILINEAR)
    a = g.point(lambda v: 0 if v < 150 else min(140, int((v - 150) / 105.0 * 140)))
    im = Image.new("RGBA", (960, 540), (18, 13, 28, 255))
    im.putalpha(a)
    return im.resize((1920, 1080), Image.LANCZOS)


def halo():
    """Aura del documento: tres anillos planos en ambar (se ve antes que el documento, sin destello)."""
    im = lienzo(T * 2, T * 2)
    d = ImageDraw.Draw(im)
    c = T
    for r, a in ((128, 30), (100, 46), (74, 64)):
        d.ellipse([c - r, c - r, c + r, c + r], fill=(232, 176, 75, a))
    return im


def primer_plano():
    """Cables colgando en el borde superior (primer plano, se mueve mas rapido). No toca la zona de juego."""
    W, H = 3840, 260
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    x = 0
    while x < W:
        ancho = rnd.randint(380, 700)
        caida = rnd.randint(70, 170)
        pts = [(x + ancho * t / 30.0, 10 + caida * math.sin(math.pi * t / 30.0)) for t in range(31)]
        d.line(pts, fill=(14, 10, 22, 255), width=14, joint="curve")
        if rnd.random() < 0.5:
            px, py = pts[15]
            d.rectangle([px - 18, py, px + 18, py + 34], fill=(14, 10, 22, 255))
            d.rectangle([px - 8, py + 34, px + 8, py + 44], fill=(170, 70, 90, 255))
        x += ancho - rnd.randint(40, 160)
    d.rectangle([0, 0, W, 14], fill=(14, 10, 22, 255))
    return im


# ------------------------------------------------------------------ Ruta de la Verdad 2: piezas nuevas y decoracion
def pasarela(izq, der):
    """Pasarela de datos (un sentido): losa fina con borde claro arriba y luz lila hacia abajo; transparente debajo."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    for k in range(4):                          # resplandor plano en bandas (se ve que se puede atravesar)
        d.rectangle([0, 40 + k * 10, T, 48 + k * 10], fill=(201, 184, 216, 70 - k * 16))
    x0 = 10 if izq else 0
    x1 = T - 10 if der else T
    d.rectangle([x0, 4, x1, 38], fill=PASARELA)
    d.rectangle([x0, 26, x1, 38], fill=(186, 170, 206, 255))
    for x in range(x0 + 10, x1 - 6, 30):
        d.rectangle([x, 12, x + 14, 18], fill=TEAL)
    d.line([(x0, 4), (x1, 4)], fill=TINTA, width=L)
    d.line([(x0, 38), (x1, 38)], fill=TINTA, width=L)
    if izq:
        d.line([(x0, 4), (x0, 38)], fill=TINTA, width=L)
        d.rectangle([x0 + 8, 38, x0 + 18, 60], fill=TINTA)
    if der:
        d.line([(x1, 4), (x1, 38)], fill=TINTA, width=L)
        d.rectangle([x1 - 18, 38, x1 - 8, 60], fill=TINTA)
    return im


def impulsor(pulsado):
    """Impulsor: bloque de la infraestructura con una plataforma de resorte y flechas (forma, no solo color)."""
    im = solido(True, True, True, False, 0)
    d = ImageDraw.Draw(im)
    alto = 18 if pulsado else 34
    d.rectangle([18, 0, T - 18, 40], fill=HONDO)
    d.rounded_rectangle([14, 40 - alto, T - 14, 40], radius=8, fill=TEAL, outline=TINTA, width=L)
    for k in range(3):
        y = 40 - alto - 18 - k * 20
        if y < -60:
            break
    for x in (36, 72, 108):
        d.polygon([(x - 12, 62), (x, 48), (x + 12, 62)], fill=PAPEL if not pulsado else AMBAR, outline=TINTA)
    d.rectangle([24, 76, T - 24, 86], fill=TINTA)
    return im


def escaner(estado):
    """Haz del escaner (un tile de alto): off = guia punteada; aviso = linea fina que parpadea; on = haz ancho."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    c = T // 2
    if estado == "off":
        for y in range(0, T, 24):
            d.rectangle([c - 3, y, c + 3, y + 10], fill=(209, 73, 91, 90))
    elif estado == "aviso":
        d.rectangle([c - 5, 0, c + 5, T], fill=(209, 73, 91, 200))
        for y in range(8, T, 36):
            d.rectangle([c - 14, y, c + 14, y + 4], fill=(251, 246, 238, 160))
    else:
        d.rectangle([c - 34, 0, c + 34, T], fill=(209, 73, 91, 90))
        d.rectangle([c - 22, 0, c + 22, T], fill=(209, 73, 91, 200))
        d.rectangle([c - 8, 0, c + 8, T], fill=(255, 220, 228, 255))
    return im


def emisor(activo):
    """Cabeza del escaner, colgada bajo el bloque: lente roja (encendida) o apagada."""
    im = lienzo(T, T // 2)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 0, T - 30, 48], radius=10, fill=MORADO2, outline=TINTA, width=L)
    d.ellipse([T // 2 - 18, 22, T // 2 + 18, 58], fill=RUMOR if activo else MORADO3, outline=TINTA, width=5)
    return im


def deco_pantalla(texto):
    """Pantalla de NOVA en la pared del fondo con una frase del rumor (decoracion, no colisiona)."""
    w, h = 288, 180
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w - 6, h - 30], radius=12, fill=(30, 24, 46, 255), outline=TINTA, width=L)
    d.rectangle([22, 22, w - 22, h - 46], fill=(52, 40, 74, 255))
    f = ImageFont.truetype(FUENTE, 22)
    d.text((34, 32), "@verdad.oculta", font=f, fill=(209, 73, 91, 255))
    f2 = ImageFont.truetype(FUENTE, 26)
    d.text((34, 66), texto, font=f2, fill=PAPEL)
    d.rectangle([w // 2 - 10, h - 30, w // 2 + 10, h - 6], fill=TINTA)
    return im


def deco_rack():
    """Rack de servidores al fondo (2 tiles de alto), con LEDs."""
    w, h = 120, 288
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w - 4, h - 4], fill=(40, 33, 60, 255), outline=(26, 20, 38, 255), width=6)
    rnd = random.Random(5)
    for y in range(20, h - 20, 26):
        d.rectangle([16, y, w - 16, y + 16], fill=(30, 24, 46, 255))
        d.rectangle([w - 34, y + 5, w - 24, y + 11], fill=TEAL if rnd.random() < 0.4 else (60, 52, 88, 255))
    return im


def deco_cartel(simbolo):
    """Cartel de aviso antes de un peligro: triangulo con signo (pinchos, escaner, plataforma) o flecha de impulsor."""
    w, h = 120, 160
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([w // 2 - 6, 70, w // 2 + 6, h], fill=TINTA)
    if simbolo == "impulso":
        d.rounded_rectangle([12, 8, w - 12, 84], radius=10, fill=TEAL, outline=TINTA, width=L)
        d.polygon([(w // 2, 18), (w // 2 + 24, 48), (w // 2 + 8, 48), (w // 2 + 8, 72), (w // 2 - 8, 72),
                   (w // 2 - 8, 48), (w // 2 - 24, 48)], fill=PAPEL)
        return im
    d.polygon([(w // 2, 6), (w - 8, 84), (8, 84)], fill=AMBAR, outline=TINTA)
    d.line([(w // 2, 6), (w - 8, 84), (8, 84), (w // 2, 6)], fill=TINTA, width=L)
    if simbolo == "escaner":
        d.rectangle([w // 2 - 5, 30, w // 2 + 5, 74], fill=RUMOR)
    else:
        d.rectangle([w // 2 - 5, 30, w // 2 + 5, 58], fill=TINTA)
        d.ellipse([w // 2 - 6, 64, w // 2 + 6, 76], fill=TINTA)
    return im


def deco_arco(nombre):
    """Arco de zona (se cruza al llegar a cada punto de control): marco de servidor con letrero."""
    w, h = 288, 432
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    for x0 in (8, w - 48):
        d.rectangle([x0, 70, x0 + 40, h], fill=MORADO2, outline=TINTA, width=L)
        for y in range(100, h - 20, 40):
            d.rectangle([x0 + 10, y, x0 + 30, y + 8], fill=TEAL)
    d.rounded_rectangle([0, 8, w, 80], radius=12, fill=PAPEL, outline=TINTA, width=L)
    f = ImageFont.truetype(FUENTE, 24)
    tw = d.textlength(nombre, font=f)
    d.text(((w - tw) / 2, 30), nombre, font=f, fill=VINO)
    return im


def meta_haz():
    """Columna de luz sobre el archivo (presentacion de la meta)."""
    w, h = 216, 720
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    for k, a in enumerate((40, 60, 90)):
        m = 30 + k * 28
        d.rectangle([m, 0, w - m, h], fill=(232, 176, 75, a))
    return im


def main():
    for m in range(16):
        arriba, izq, der, abajo = bool(m & 1), bool(m & 2), bool(m & 4), bool(m & 8)
        for v in range(2):
            guardar(solido(arriba, izq, der, abajo, v), "solido_%d_%d" % (m, v))
    for f in range(3):
        guardar(barrera(f), "barrera_%d" % f)
    for e in ("on", "aviso", "off"):
        guardar(inestable(e), "inestable_" + e)
    guardar(documento(), "documento")
    guardar(antena(False), "antena_off")
    guardar(antena(True), "antena_on")
    guardar(archivo(), "archivo")
    for i in range(2):
        guardar(avatar("idle", i / 2.0), "av_idle_%d" % i)
    for i in range(6):
        guardar(avatar("corre", i / 6.0), "av_corre_%d" % i)
    for p in ("salto", "cae", "recoge", "dano", "victoria"):
        guardar(avatar(p, 0.25), "av_" + p)
    guardar(cielo(), "cielo")
    guardar(vineta(), "vineta")
    guardar(halo(), "halo")
    guardar(fondo_lejos(), "fondo_lejos")
    guardar(fondo_medio(), "fondo_medio")
    guardar(primer_plano(), "primer_plano")
    for izq in (0, 1):
        for der in (0, 1):
            guardar(pasarela(izq, der), "pasarela_%d%d" % (izq, der))
    guardar(impulsor(False), "impulsor_0")
    guardar(impulsor(True), "impulsor_1")
    for e in ("off", "aviso", "on"):
        guardar(escaner(e), "escaner_" + e)
    guardar(emisor(False), "emisor_0")
    guardar(emisor(True), "emisor_1")
    for k, t in enumerate(("NO LA TOMEN", "COMPARTE YA", "¿Y EL ALCALDE?")):
        guardar(deco_pantalla(t), "deco_pantalla_%d" % k)
    guardar(deco_rack(), "deco_rack")
    for simb in ("peligro", "escaner", "impulso"):
        guardar(deco_cartel(simb), "deco_cartel_" + simb)
    for k, nombre in enumerate(("PUERTA DE ENLACE", "GRANJA DE BOTS", "NÚCLEO DE NOVA", "ARCHIVO ORIGINAL")):
        guardar(deco_arco(nombre), "deco_arco_%d" % k)
    guardar(meta_haz(), "meta_haz")
    print("ok:", len(os.listdir(OUT)), "archivos en", OUT)


if __name__ == "__main__":
    main()
