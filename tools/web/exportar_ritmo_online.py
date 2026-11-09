"""
Copia al servidor online los recursos ORIGINALES del Duelo de Frecuencias (una sola fuente: game/).

- Audio: OGG -> AAC (.m4a), porque Safari en iPhone/iPad no decodifica Vorbis. Se sirven los dos y el
  navegador usa el que pueda decodificar. Requiere `pip install imageio-ffmpeg` solo al regenerar.
- Notas y receptores: los mismos PNG del juego.
- NOVA: los sprites del juego reducidos (el telefono no necesita 1500 px).

Los charts NO se copian: el servidor los lee de game/ritmo/ (mismo archivo que Ren'Py).

Uso:  python tools/web/exportar_ritmo_online.py
"""
import os
import shutil
import subprocess

from PIL import Image

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DESTINO = os.path.join(RAIZ, "leaderboard", "app", "static", "ritmo")
MUSICA = os.path.join(RAIZ, "game", "assets", "audio", "music")
GUI = os.path.join(RAIZ, "game", "gui", "ritmo")
SPRITES = os.path.join(RAIZ, "game", "images", "personajes", "sprites")
EXPRESIONES_NOVA = ("seria", "feliz", "enojada")


def main():
    os.makedirs(DESTINO, exist_ok=True)
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for modo in ("feria", "historia"):
        origen = os.path.join(MUSICA, "duelo_%s.ogg" % modo)
        shutil.copyfile(origen, os.path.join(DESTINO, "duelo_%s.ogg" % modo))
        subprocess.check_call([ff, "-loglevel", "error", "-y", "-i", origen, "-c:a", "aac", "-b:a", "128k",
                               os.path.join(DESTINO, "duelo_%s.m4a" % modo)])
    for k in range(4):
        for nombre in ("nota_%d.png", "receptor_%d.png", "receptor_on_%d.png"):
            shutil.copyfile(os.path.join(GUI, nombre % k), os.path.join(DESTINO, nombre % k))
    for e in EXPRESIONES_NOVA:
        img = Image.open(os.path.join(SPRITES, "nova_%s.png" % e)).convert("RGBA")
        img.thumbnail((520, 520))
        img.save(os.path.join(DESTINO, "nova_%s.webp" % e), quality=85)
    print("Recursos exportados en", DESTINO)


if __name__ == "__main__":
    main()
