"""Voces de la cinematica de apertura (noticiero y radio de la ambulancia), con ElevenLabs.

    python tools/voces/cinematica_voces.py            # sintetiza solo las que faltan
    python tools/voces/cinematica_voces.py --force

Guarda el audio crudo (WAV 22,05 kHz) en tools/voces/cinematica/. El mezclador de la cinematica
(tools/musica/cinematica_sonido.py) las coloca en la linea de tiempo y les aplica el efecto de radio o de emision.
Voces distintas de las de los personajes: el publico no debe confundir al presentador con Claudia ni con Rodrigo.
"""
import argparse
import os
import sys

import numpy as np
import soundfile as sf

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import elevenlabs as EL  # noqa: E402

SALIDA = os.path.join(AQUI, "cinematica")
MODELO = "eleven_multilingual_v2"

LINEAS = {
    "presentador_1": ("jBlmi27XRORxjPquUeCh",
                      "Última hora. Los bloqueos continúan extendiéndose por Ciudad Nova tras la difusión de "
                      "información no verificada sobre el suministro de agua.",
                      {"stability": 0.62, "similarity_boost": 0.8, "style": 0.15, "speed": 1.2}),
    "paramedico": ("RyfjEHnKbtma4Srae2za",
                   "¡Central, tenemos un paciente crítico! La avenida está completamente bloqueada. "
                   "Necesitamos una ruta alternativa.",
                   {"stability": 0.30, "similarity_boost": 0.8, "style": 0.55, "speed": 1.2}),
    "presentador_2": ("jBlmi27XRORxjPquUeCh",
                      "Un paciente con una infección intestinal grave falleció tras sufrir retrasos en su traslado "
                      "de emergencia. Los bloqueos que paralizan Ciudad Nova habrían dificultado su atención.",
                      {"stability": 0.72, "similarity_boost": 0.8, "style": 0.05, "speed": 1.14}),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    os.makedirs(SALIDA, exist_ok=True)
    motor = None
    for nombre, (voz, texto, ajustes) in LINEAS.items():
        ruta = os.path.join(SALIDA, nombre + ".wav")
        if os.path.exists(ruta) and not args.force:
            print("ya existe:", nombre)
            continue
        motor = motor or EL.ElevenLabs(MODELO)
        audio, sr = motor.sintetizar(voz, texto, ajustes)
        sf.write(ruta, np.clip(audio, -1, 1), sr, subtype="PCM_16")
        print("%s: %.2f s" % (nombre, len(audio) / sr))
    if motor:
        print("Caracteres enviados: %d" % motor.caracteres)


if __name__ == "__main__":
    main()
