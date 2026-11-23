"""Remaster 3: piezas de interfaz de Ren'Py en el lenguaje de Civitas (ficha de papel con contorno de tinta).

    python tools/arte/gui_civitas.py

Sustituye los restos del estilo anterior (botones lavanda, deslizadores indigo, pildoras azul marino)
por la paleta de Civitas. Guarda los originales en tools/arte/respaldo_v1/gui/ la primera vez.
Solo interfaz: no toca personajes, fondos ni la historia.
"""
import os
import shutil

from PIL import Image, ImageDraw

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GUI = os.path.join(RAIZ, "game", "gui")
RESPALDO = os.path.join(RAIZ, "tools", "arte", "respaldo_v1", "gui")

TINTA = (43, 36, 64, 255)
PAPEL = (251, 246, 238, 255)
PAPEL_HOVER = (239, 230, 243, 255)
LILA = (201, 184, 216, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
S = 4   # se dibuja a 4x y se reduce: bordes limpios


def guardar(img, rel):
    ruta = os.path.join(GUI, rel)
    copia = os.path.join(RESPALDO, rel)
    if os.path.exists(ruta) and not os.path.exists(copia):
        os.makedirs(os.path.dirname(copia), exist_ok=True)
        shutil.copy2(ruta, copia)
    img.save(ruta, optimize=True)


def ficha(w, h, relleno, borde=TINTA, grosor=4, radio=8, sombra=6, franja=None, franja_w=12):
    """Rectangulo de papel con contorno y sombra plana de tinta (sin degradados)."""
    W, H = w * S, h * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    alto = H - sombra * S
    if sombra:
        d.rounded_rectangle([0, sombra * S, W - 1, H - 1], radius=radio * S, fill=TINTA)
    d.rounded_rectangle([0, 0, W - 1, alto - 1], radius=radio * S, fill=borde)
    g = grosor * S
    d.rounded_rectangle([g, g, W - 1 - g, alto - 1 - g], radius=max(1, (radio - grosor)) * S, fill=relleno)
    if franja:
        d.rectangle([g, g + radio * S // 2, g + franja_w * S, alto - 1 - g - radio * S // 2], fill=franja)
    return im.resize((w, h), Image.LANCZOS)


def barra(w, h, color, radio=None):
    W, H = w * S, h * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, W - 1, H - 1], radius=(radio if radio is not None else h // 2) * S, fill=color)
    return im.resize((w, h), Image.LANCZOS)


def perilla(tam, centro):
    W = tam * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, W - 1, W - 1], fill=TINTA)
    d.ellipse([4 * S, 4 * S, W - 1 - 4 * S, W - 1 - 4 * S], fill=PAPEL)
    r = W * 0.18
    d.ellipse([W / 2 - r, W / 2 - r, W / 2 + r, W / 2 + r], fill=centro)
    return im.resize((tam, tam), Image.LANCZOS)


def main():
    # Los botones (boton_menu_*, telefono_boton*) volvieron a su diseno original (commit 76af0ef) por decision
    # del equipo: este generador ya no los toca. Las fichas del remaster 3 siguen en el historial (commit 739b74b).
    # Marco general (Frame 30,30): papel con contorno de tinta y sombra plana.
    guardar(ficha(300, 300, (251, 246, 238, 250), grosor=5, radio=12, sombra=8), "frame.png")
    # Deslizadores, barras y barras de desplazamiento.
    for estado, fondo in (("idle", (201, 184, 216, 170)), ("hover", (201, 184, 216, 230))):
        guardar(barra(500, 24, fondo), "slider/horizontal_%s_bar.png" % estado)
        guardar(barra(38, 525, fondo), "slider/vertical_%s_bar.png" % estado)
        guardar(barra(1050, 18, fondo), "scrollbar/horizontal_%s_bar.png" % estado)
        guardar(barra(18, 500, (201, 184, 216, 120 if estado == "idle" else 170)), "scrollbar/vertical_%s_bar.png" % estado)
        pul = VINO if estado == "idle" else RUMOR
        guardar(perilla(34, pul), "slider/horizontal_%s_thumb.png" % estado)
        guardar(barra(38, 15, pul, radio=4), "slider/vertical_%s_thumb.png" % estado)
        guardar(barra(1050, 18, TINTA if estado == "idle" else VINO), "scrollbar/horizontal_%s_thumb.png" % estado)
        guardar(barra(18, 120, TINTA if estado == "idle" else VINO), "scrollbar/vertical_%s_thumb.png" % estado)
    guardar(barra(500, 24, VINO), "bar/left.png")
    guardar(barra(500, 24, (201, 184, 216, 150)), "bar/right.png")
    guardar(barra(38, 525, VINO), "bar/bottom.png")
    guardar(barra(38, 525, (201, 184, 216, 150)), "bar/top.png")
    print("ok: interfaz regenerada; originales en", RESPALDO)


if __name__ == "__main__":
    main()
