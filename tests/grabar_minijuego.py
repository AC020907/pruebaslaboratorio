"""
Graba un minijuego jugandose en el juego real (ventana de Ren'Py) como AVI MJPEG, sin audio.

    python tests/grabar_minijuego.py --etapa ruta --salida <carpeta> [--segundos 60]
    python tests/grabar_minijuego.py --etapa central --salida <carpeta> --segundos 95

Lanza la etapa de QA indicada (qa_ruta.rpy: Ruta de la Verdad con la ruta verificada; qa_central.rpy: Central de
Emergencias con la fase 1 jugada con clics y el resto con el despachador automatico) y captura la ventana con
ImageGrab a ~30-40 capturas/s; el video se arma a 30 fps por marca de tiempo. No se graba el altavoz (no hay una
pista unica que alinear como en la cinematica), asi que el AVI no lleva audio.
"""
import argparse
import io
import json
import os
import sys
import time

import numpy as np
from PIL import ImageGrab

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from qa_visual import SDK_DEFECTO, lanzar  # noqa: E402
from grabar_cinematica import ventana_de, rect_cliente, user32, _chunk, _lista  # noqa: E402
import struct  # noqa: E402


def escribir_avi_mudo(ruta, jpegs, w, h, fps):
    n = len(jpegs)
    mayor = max(len(j) for j in jpegs)
    avih = struct.pack("<IIIIIIIIII4I", int(1e6 / fps), mayor * fps, 0, 0x10, n, 0, 1, mayor + 16, w, h, 0, 0, 0, 0)
    strh = struct.pack("<4s4sIHHIIIIIIII4h", b"vids", b"MJPG", 0, 0, 0, 0, 1, fps, 0, n, mayor + 16, 0xFFFFFFFF, 0, 0, 0, w, h)
    strf = struct.pack("<IiiHH4sIiiII", 40, w, h, 1, 24, b"MJPG", w * h * 3, 0, 0, 0, 0)
    hdrl = _lista(b"hdrl", _chunk(b"avih", avih) + _lista(b"strl", _chunk(b"strh", strh) + _chunk(b"strf", strf)))
    movi, indice = io.BytesIO(), []
    movi.write(b"movi")
    for j in jpegs:
        indice.append(struct.pack("<4sIII", b"00dc", 0x10, movi.tell(), len(j)))
        movi.write(_chunk(b"00dc", j))
    mb = movi.getvalue()
    cuerpo = b"AVI " + hdrl + b"LIST" + struct.pack("<I", len(mb)) + mb + _chunk(b"idx1", b"".join(indice))
    with open(ruta, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", required=True, choices=("ruta", "central"))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sdk", default=SDK_DEFECTO)
    ap.add_argument("--tam", default="1280x720")
    ap.add_argument("--segundos", type=float, default=60.0)
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)
    carpeta = os.path.join(salida, "juego_" + args.etapa)
    proc, _t = lanzar(args.sdk, {"ALCALDE_QA": "galeria", "ALCALDE_QA_ETAPA": args.etapa, "ALCALDE_QA_TAM": args.tam,
                                 "ALCALDE_QA_CAPTURAS": carpeta}, carpeta)
    hwnd, limite = None, time.time() + 60
    while hwnd is None and time.time() < limite:
        time.sleep(0.2)
        hwnd = ventana_de(proc.pid)
    if hwnd is None:
        proc.kill()
        sys.exit("no aparecio la ventana del juego")
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)
    cuadros, t0 = [], time.time()
    while proc.poll() is None and time.time() - t0 < args.segundos:
        x0, y0, x1, y1 = rect_cliente(hwnd)
        if x1 - x0 < 100 or y1 - y0 < 100:          # la ventana se esta creando o redimensionando
            time.sleep(0.05)
            continue
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=88)
        cuadros.append((time.time(), buf.getvalue(), img.size))
    proc.kill()
    w, h = cuadros[-1][2]
    tiempos = np.array([c[0] for c in cuadros])
    pasos = int((tiempos[-1] - tiempos[0]) * args.fps)
    salida_cuadros, peor = [], 0.0
    for k in range(pasos):
        objetivo = tiempos[0] + k / args.fps
        i = int(np.argmin(np.abs(tiempos - objetivo)))
        peor = max(peor, abs(tiempos[i] - objetivo))
        salida_cuadros.append(cuadros[i][1] if cuadros[i][2] == (w, h) else cuadros[-1][1])
    ruta = os.path.join(salida, "civitas_%s.avi" % ("ruta_de_la_verdad" if args.etapa == "ruta" else "central_de_emergencias"))
    escribir_avi_mudo(ruta, salida_cuadros, w, h, args.fps)
    info = {"archivo": ruta, "tamano": [w, h], "fps_salida": args.fps, "segundos": round(pasos / args.fps, 1),
            "capturas_por_segundo": round(len(cuadros) / max(0.1, tiempos[-1] - tiempos[0]), 1),
            "mayor_desfase_cuadro_s": round(float(peor), 3), "bytes": os.path.getsize(ruta), "audio": False}
    with open(os.path.join(salida, "grabacion_%s.json" % args.etapa), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
