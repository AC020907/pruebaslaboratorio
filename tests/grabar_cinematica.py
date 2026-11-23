"""
Graba la cinematica de apertura desde el juego real y la guarda como AVI (video MJPEG + audio PCM).

    python tests/grabar_cinematica.py --salida <carpeta> [--tam 1280x720] [--fps 30]

Lanza Ren'Py con la etapa de QA "cinematica" (qa_cinematica.rpy), captura la ventana del juego con ImageGrab
mientras se reproduce y la marca de tiempo que escribe el juego (hora de pared del t = 0 de la cinematica)
alinea cada cuadro capturado con su instante. El audio del AVI son las dos pistas que el juego reproduce
(apertura_fx.ogg + apertura_voces.ogg) colocadas desde ese mismo t = 0: no se graba el altavoz.
Escribe tambien grabacion.json con los cuadros capturados por segundo y la cobertura de la linea de tiempo.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import io
import json
import os
import struct
import sys
import time

import numpy as np
import soundfile as sf
from PIL import ImageGrab

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "game"))
from qa_visual import SDK_DEFECTO, lanzar  # noqa: E402
from clases import cinematica_tiempos as CT  # noqa: E402

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


def ventana_de(pid):
    encontradas = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cada(hwnd, _l):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            r = wt.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            if r.right > 400:
                encontradas.append(hwnd)
        return True

    user32.EnumWindows(cada, 0)
    return encontradas[0] if encontradas else None


def rect_cliente(hwnd):
    r = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return (pt.x, pt.y, pt.x + r.right, pt.y + r.bottom)


# ---------------- AVI (RIFF) con MJPEG + PCM ----------------
def _chunk(fcc, datos):
    return fcc + struct.pack("<I", len(datos)) + datos + (b"\0" if len(datos) % 2 else b"")


def _lista(tipo, contenido):
    return b"LIST" + struct.pack("<I", len(contenido) + 4) + tipo + contenido


def escribir_avi(ruta, jpegs, w, h, fps, pcm, sr=44100):
    n = len(jpegs)
    muestras_por_cuadro = sr // fps
    mayor = max(len(j) for j in jpegs)
    avih = struct.pack("<IIIIIIIIII4I", int(1e6 / fps), mayor * fps + sr * 4, 0, 0x10 | 0x100, n, 0, 2,
                       mayor + 16, w, h, 0, 0, 0, 0)
    strh_v = struct.pack("<4s4sIHHIIIIIIII4h", b"vids", b"MJPG", 0, 0, 0, 0, 1, fps, 0, n, mayor + 16,
                         0xFFFFFFFF, 0, 0, 0, w, h)
    strf_v = struct.pack("<IiiHH4sIiiII", 40, w, h, 1, 24, b"MJPG", w * h * 3, 0, 0, 0, 0)
    bloques = len(pcm) // 4
    strh_a = struct.pack("<4s4sIHHIIIIIIII4h", b"auds", b"\0\0\0\0", 0, 0, 0, 0, 4, sr * 4, 0, bloques,
                         muestras_por_cuadro * 4, 0xFFFFFFFF, 4, 0, 0, 0, 0)
    strf_a = struct.pack("<HHIIHHH", 1, 2, sr, sr * 4, 4, 16, 0)
    hdrl = _lista(b"hdrl", _chunk(b"avih", avih) + _lista(b"strl", _chunk(b"strh", strh_v) + _chunk(b"strf", strf_v))
                  + _lista(b"strl", _chunk(b"strh", strh_a) + _chunk(b"strf", strf_a)))
    movi, indice = io.BytesIO(), []
    movi.write(b"movi")
    for k, j in enumerate(jpegs):
        for fcc, datos in ((b"00dc", j), (b"01wb", pcm[k * muestras_por_cuadro * 4:(k + 1) * muestras_por_cuadro * 4])):
            if not datos:
                continue
            indice.append(struct.pack("<4sIII", fcc, 0x10, movi.tell(), len(datos)))
            movi.write(_chunk(fcc, datos))
    movi_b = movi.getvalue()
    cuerpo = b"AVI " + hdrl + b"LIST" + struct.pack("<I", len(movi_b)) + movi_b + _chunk(b"idx1", b"".join(indice))
    with open(ruta, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sdk", default=SDK_DEFECTO)
    ap.add_argument("--tam", default="1280x720")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)
    marca = os.path.join(salida, "t0.txt")
    if os.path.exists(marca):
        os.remove(marca)
    carpeta = os.path.join(salida, "juego")
    proc, _t = lanzar(args.sdk, {"ALCALDE_QA": "galeria", "ALCALDE_QA_ETAPA": "cinematica", "ALCALDE_QA_TAM": args.tam,
                                 "ALCALDE_QA_CAPTURAS": carpeta, "ALCALDE_QA_VOZ": "1", "ALCALDE_QA_CINE_MARCA": marca},
                      carpeta)
    hwnd = None
    limite = time.time() + 60
    while hwnd is None and time.time() < limite:
        time.sleep(0.2)
        hwnd = ventana_de(proc.pid)
    if hwnd is None:
        proc.kill()
        sys.exit("no aparecio la ventana del juego")
    user32.SetForegroundWindow(hwnd)
    cuadros = []
    fin = None
    while proc.poll() is None:
        ahora = time.time()
        if fin is None and os.path.exists(marca):
            with open(marca) as f:
                texto = f.read().strip()
            if texto:
                t0 = float(texto)
                fin = t0 + CT.DURACION + 0.4
        if fin is not None and ahora > fin:
            break
        img = ImageGrab.grab(bbox=rect_cliente(hwnd), all_screens=True)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=88)
        cuadros.append((ahora, buf.getvalue(), img.size))
    proc.kill()
    if fin is None:
        sys.exit("el juego no marco el inicio de la cinematica")
    w, h = cuadros[-1][2]
    tiempos = np.array([c[0] for c in cuadros])
    salida_cuadros, huecos = [], 0.0
    pasos = int((CT.DURACION + 0.3) * args.fps)
    for k in range(pasos):
        objetivo = t0 + k / args.fps
        i = int(np.argmin(np.abs(tiempos - objetivo)))
        huecos = max(huecos, abs(tiempos[i] - objetivo))
        salida_cuadros.append(cuadros[i][1] if cuadros[i][2] == (w, h) else cuadros[-1][1])
    dentro = [c for c in cuadros if t0 <= c[0] <= t0 + CT.DURACION]
    fx, sr = sf.read(os.path.join(RAIZ, "game", "assets", "audio", "cine", "apertura_fx.ogg"), always_2d=True)
    vz, _ = sf.read(os.path.join(RAIZ, "game", "assets", "audio", "cine", "apertura_voces.ogg"), always_2d=True)
    n = min(len(fx), len(vz))
    mezcla = np.clip(fx[:n] + vz[:n], -1, 1)
    total = pasos * (sr // args.fps)
    mezcla = np.pad(mezcla, ((0, max(0, total - n)), (0, 0)))[:total]
    pcm = (mezcla * 32767).astype("<i2").tobytes()
    ruta = os.path.join(salida, "civitas_cinematica_apertura.avi")
    escribir_avi(ruta, salida_cuadros, w, h, args.fps, pcm, sr)
    info = {"archivo": ruta, "tamano": [w, h], "fps_salida": args.fps, "segundos": round(pasos / args.fps, 2),
            "capturas_durante_la_cinematica": len(dentro),
            "capturas_por_segundo": round(len(dentro) / CT.DURACION, 1),
            "mayor_desfase_cuadro_s": round(float(huecos), 3), "bytes": os.path.getsize(ruta)}
    with open(os.path.join(salida, "grabacion.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
