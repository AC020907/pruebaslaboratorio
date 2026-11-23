"""
Duelo de Frecuencias, dificultad DIFICIL: cancion ORIGINAL de alta energia + chart de 5 carriles.

Referencia pedida: Megalovania (Undertale). No tenemos licencia de la grabacion ni de la composicion, asi que
NO se usa ni se imita su melodia: esta es una pista propia con energia comparable (144 BPM, Mi menor, bajo en
corcheas, rafagas de semicorcheas, acentos sincopados), escrita aqui nota a nota.

Cada carril es una nota de la escala pentatonica de Mi menor (Mi, Sol, La, Si, Re -> D, F, Espacio, J, K): subir
la melodia es moverse a la derecha. El chart sale de LOS MISMOS eventos que toca la "senal" (sin humanizacion),
asi que esta sincronizado por construccion. Dos notas a la vez como maximo, nunca la misma tecla dos veces
seguidas en semicorcheas, y todo en la reticula de 16 pasos por compas.

Uso:  python tools/musica/duelo_dificil.py  ->  game/assets/audio/music/duelo_dificil.ogg
                                                game/ritmo/duelo_dificil.json
"""
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import instruments as I  # noqa: E402
from componer import master, write_ogg  # noqa: E402
from dsp import mtof  # noqa: E402
from song import Song  # noqa: E402

RAIZ = AQUI.parent.parent
BPM = 144
MS_PULSO = 60000.0 / BPM
CARRILES = 5
# Carril -> nota (Mi menor pentatonica). El grado 5..9 es la misma nota una octava arriba (mismo carril).
ESCALA = [64, 67, 69, 71, 74, 76, 79, 81, 83, 86]

# Frases de 1 compas: lista de (paso de semicorchea 0-15, grado o (grado, grado) para dos notas a la vez).
A1 = [(0, 0), (2, 3), (4, 4), (6, 3), (8, 5), (10, 4), (12, 3), (14, 1)]
A2 = [(0, 0), (2, 3), (4, 4), (6, 6), (8, 5), (10, 4), (12, 2), (14, 1), (15, 2)]
R1 = [(0, 0), (1, 1), (2, 2), (3, 3), (6, 4), (8, 3), (10, 2), (12, 1), (14, 0)]          # escalera arriba, baja
R2 = [(0, 4), (1, 3), (2, 2), (3, 1), (6, 0), (8, 1), (10, 2), (11, 3), (12, 4), (14, 2)]
C1 = [(0, (0, 3)), (3, 2), (6, (1, 4)), (9, 2), (12, (0, 3)), (14, 4)]                       # tresillo 3+3+2 con dobles
C2 = [(0, (1, 4)), (3, 3), (6, (0, 2)), (9, 3), (12, (1, 4)), (14, 0)]
D1 = [(0, 0), (4, 4), (8, 1), (12, 3)]                                                       # medio tiempo, saltos amplios
D2 = [(0, 4), (4, 0), (8, 3), (10, 2), (12, 1)]
E1 = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 3), (6, 2), (7, 1), (8, (0, 4)), (10, 2), (11, 3), (12, 4), (14, (1, 3))]
E2 = [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (5, 1), (6, 2), (7, 3), (8, (0, 4)), (10, 2), (11, 1), (12, 0), (14, (1, 3))]
E3 = [(0, (0, 2)), (2, 4), (3, 3), (4, (1, 4)), (6, 0), (7, 1), (8, (2, 4)), (10, 0), (12, (1, 3)), (13, 2), (14, (0, 4))]
E4 = [(0, 0), (1, 2), (2, 4), (4, (1, 3)), (6, 0), (7, 1), (8, 2), (9, 3), (10, 4), (12, (0, 4)), (14, 2)]
# NOVA "llama" (no se toca) antes de cada respuesta: el mismo ritmo, con su sintetizador digital.
LLAMADA = [(0, 7), (1, 6), (2, 5), (3, 4), (6, 3), (8, 4), (10, 5), (12, 6), (14, 7)]

# (compas, frase, quien). Compases 0-1: cuenta atras; 2-5 riff; 6-9 llamada y respuesta; 10-13 dobles;
# 14-17 medio tiempo; 18-23 climax; 24 acorde final; 25-26 cola.
PLAN = ([(2, A1, "senal"), (3, A2, "senal"), (4, A1, "senal"), (5, A2, "senal"),
         (6, LLAMADA, "nova"), (7, R1, "senal"), (8, LLAMADA, "nova"), (9, R2, "senal"),
         (10, C1, "senal"), (11, C2, "senal"), (12, C1, "senal"), (13, C2, "senal"),
         (14, D1, "senal"), (15, D2, "senal"), (16, D1, "senal"), (17, D2, "senal"),
         (18, E1, "senal"), (19, E2, "senal"), (20, E3, "senal"), (21, E4, "senal"), (22, E1, "senal"), (23, E3, "senal")])
COMPASES = 27
FINAL = 24
ACORDES = ["Em", "C", "D", "Em"]          # cada 2 compases
RAIZ_BAJO = {"Em": 40, "C": 36, "D": 38}


def carril(grado):
    return grado % CARRILES


def construir():
    s = Song("duelo_dificil", BPM, COMPASES, rt60=1.0, seed=29, hum=0.0)
    notas = []
    for compas, frase, quien in PLAN:
        for paso, g in frase:
            beat = compas * 4 + paso / 4.0
            grados = g if isinstance(g, tuple) else (g,)
            for grado in grados:
                f = mtof(ESCALA[grado])
                if quien == "nova":
                    s.put(I.digi_arp(f, 0.22 * s.spb, 0.7, bits=5, hold=2), beat, -0.35, 0.36, 0.2, hum=0.0)
                else:
                    s.put(I.pluck(f, 0.3 * s.spb, 0.95, tau=0.16, bright=0.85), beat, 0.12, 0.62, 0.12, hum=0.0)
                    s.put(I.digi_arp(f * 2, 0.12 * s.spb, 0.5, bits=6, hold=1), beat, 0.25, 0.12, 0.05, hum=0.0)
                    notas.append({"time_ms": int(round(beat * MS_PULSO)), "lane": carril(grado), "type": "tap", "beat": beat})
    # Bateria: cuenta atras audible (8 golpes), bombo a negras, caja en 2 y 4, charles que se densifica.
    s.drums(0, 2, {"t": "x...x...x...x..."}, gain=0.5)
    s.drums(2, 14, {"k": "x...x...x...x...", "s": "....x.......x...", "h": "x.x.x.x.x.x.x.x."}, gain=0.42)
    s.drums(14, 18, {"k": "x.......x.......", "s": "........x.......", "o": "....x.......x..."}, gain=0.4)
    s.drums(18, FINAL, {"k": "x...x...x...x.x.", "s": "....x..x....x...", "h": "xxxxxxxxxxxxxxxx"}, gain=0.44)
    # Bajo en corcheas (motor del tema) y acordes cortos en los tiempos fuertes.
    for compas in range(2, FINAL):
        acorde = ACORDES[(compas - 2) // 2 % 4]
        raiz = RAIZ_BAJO[acorde]
        medio = 14 <= compas < 18
        for k in range(0, 8, 2 if medio else 1):
            nota = raiz + (12 if k % 2 else 0)
            s.put(I.bass(mtof(nota), 0.42 * s.spb, 0.85, warmth=1.8), compas * 4 + k * 0.5, 0, 0.34, 0.04, hum=0.0)
        for m in {"Em": (52, 59, 64), "C": (48, 55, 64), "D": (50, 57, 62)}[acorde]:
            s.put(I.stab(mtof(m), 0.5 * s.spb, 0.6, tau=0.12), compas * 4, 0, 0.06, 0.3, hum=0.0)
    s.put(I.riser(4 * s.spb, 0.6), 14 * 4, 0, 0.18, 0.4, hum=0.0)
    s.put(I.riser(4 * s.spb, 0.7), 17 * 4, 0, 0.22, 0.4, hum=0.0)
    # Final: dos notas a la vez sobre un golpe grave.
    final = FINAL * 4
    for grado in (0, 3):
        s.put(I.pluck(mtof(ESCALA[grado]), 2.0 * s.spb, 1.0, tau=0.5, bright=0.8), final, 0.12, 0.7, 0.3, hum=0.0)
        notas.append({"time_ms": int(round(final * MS_PULSO)), "lane": carril(grado), "type": "tap", "beat": final})
    for m in (52, 59, 64, 71):
        s.put(I.stab(mtof(m), 2.5 * s.spb, 0.9), final, 0, 0.26, 0.4, hum=0.0)
    s.put(I.sub_boom(0.85, 45.0), final, 0, 0.5, 0.1, hum=0.0)
    return s, sorted(notas, key=lambda n: (n["time_ms"], n["lane"]))


def chart(notas, duracion_ms):
    return {"song_id": "duelo_dificil", "version": 1, "bpm": BPM, "offset_ms": 0, "difficulty": "dificil",
            "lanes": CARRILES, "duration_ms": int(duracion_ms),
            "notes": [{k: n[k] for k in ("time_ms", "lane", "type")} for n in notas]}


def main():
    s, notas = construir()
    out = master(s.render(), -15.0)
    n = len(out)
    fade = int(0.6 * 44100)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    write_ogg(RAIZ / "game" / "assets" / "audio" / "music" / "duelo_dificil.ogg", out)
    c = chart(notas, n / 44100 * 1000)
    (RAIZ / "game" / "ritmo" / "duelo_dificil.json").write_text(json.dumps(c, indent=1), encoding="utf-8")
    dobles = sum(1 for a, b in zip(c["notes"], c["notes"][1:]) if a["time_ms"] == b["time_ms"])
    print("duelo_dificil %.1f s  %d notas (%.1f/s)  %d dobles" % (n / 44100, len(c["notes"]), len(c["notes"]) / (n / 44100), dobles))


if __name__ == "__main__":
    main()
