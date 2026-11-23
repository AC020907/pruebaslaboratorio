"""
Duelo de Frecuencias, dificultad DIFICIL: chart de 5 carriles disenado musicalmente y sincronizado con la cancion.
- chart valido, 5 carriles, mas notas que Normal, rafagas, dobles, cambios de carril, sin patrones imposibles;
- cada nota cae en la reticula de semicorcheas de 144 BPM y coincide con un ataque REAL del audio generado;
- el juez es el mismo (Ritmo.Duelo): pulsar a tiempo da PERFECT, el quinto carril funciona;
- Normal, Facil y la Arena siguen con 4 carriles y sus charts sin cambios.
"""
import json
import os
import sys
import unittest

import numpy as np
import soundfile as sf

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RAIZ, "game"))
from clases import Ritmo  # noqa: E402

CHART = os.path.join(RAIZ, "game", "ritmo", "duelo_dificil.json")
AUDIO = os.path.join(RAIZ, "game", "assets", "audio", "music", "duelo_dificil.ogg")


def cargar(nombre):
    with open(os.path.join(RAIZ, "game", "ritmo", nombre), encoding="utf-8") as f:
        return json.load(f)


class ChartDificil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = cargar("duelo_dificil.json")
        cls.notas = cls.c["notes"]

    def test_valido_cinco_carriles_y_todos_usados(self):
        self.assertEqual(Ritmo.validar_chart(self.c), [])
        self.assertEqual(self.c["lanes"], 5)
        self.assertEqual({n["lane"] for n in self.notas}, set(range(5)))

    def test_mas_exigente_que_normal(self):
        dur = self.c["duration_ms"] / 1000.0
        normal = cargar("duelo_historia_normal.json")
        d_normal = len(normal["notes"]) / (normal["duration_ms"] / 1000.0)
        self.assertGreater(len(self.notas) / dur, 2.5 * d_normal)
        tiempos = [n["time_ms"] for n in self.notas]
        dobles = sum(1 for a, b in zip(tiempos, tiempos[1:]) if a == b)
        self.assertGreaterEqual(dobles, 20)                       # notas simultaneas
        semicorchea = 60000.0 / self.c["bpm"] / 4
        rafaga = max_rafaga = 1
        unicos = sorted(set(tiempos))
        for a, b in zip(unicos, unicos[1:]):
            rafaga = rafaga + 1 if abs((b - a) - semicorchea) <= 2 else 1
            max_rafaga = max(max_rafaga, rafaga)
        self.assertGreaterEqual(max_rafaga, 5)                    # rafagas rapidas de semicorcheas
        cambios = sum(1 for a, b in zip(self.notas, self.notas[1:]) if a["lane"] != b["lane"])
        self.assertGreater(cambios, 0.8 * len(self.notas))        # cambios de carril constantes

    def test_sin_patrones_imposibles(self):
        por_tiempo = {}
        for n in self.notas:
            por_tiempo.setdefault(n["time_ms"], []).append(n["lane"])
        self.assertLessEqual(max(len(v) for v in por_tiempo.values()), 2)          # como mucho dos teclas a la vez
        ultimo = {}
        for n in self.notas:
            if n["lane"] in ultimo:
                self.assertGreaterEqual(n["time_ms"] - ultimo[n["lane"]], 200, n)   # nunca la misma tecla en semicorcheas
            ultimo[n["lane"]] = n["time_ms"]

    def test_reticula_musical(self):
        semicorchea = 60000.0 / self.c["bpm"] / 4
        for n in self.notas:
            paso = n["time_ms"] / semicorchea
            self.assertLess(abs(paso - round(paso)) * semicorchea, 1.01, n)

    def test_cada_nota_coincide_con_un_ataque_del_audio(self):
        """Sincronizacion medida en la cancion real: flujo espectral (ataques) cerca de cada nota frente a puntos al azar."""
        audio, sr = sf.read(AUDIO)
        x = audio.mean(axis=1)
        self.assertAlmostEqual(len(x) / sr * 1000, self.c["duration_ms"], delta=50)
        hop, win = 256, 1024
        ventana = np.hanning(win)
        mags = np.array([np.abs(np.fft.rfft(x[i:i + win] * ventana)) for i in range(0, len(x) - win, hop)])
        flujo = np.concatenate([[0], np.maximum(0, np.diff(np.log1p(mags), axis=0)).sum(axis=1)])
        t_marco = (np.arange(len(flujo)) * hop + win / 2) / sr * 1000

        def pico(t_ms, radio=20):
            sel = (t_marco >= t_ms - radio) & (t_marco <= t_ms + radio)
            return flujo[sel].max() if sel.any() else 0.0

        umbral = np.percentile(flujo, 90)
        alineadas = sum(1 for t in sorted({n["time_ms"] for n in self.notas}) if pico(t) >= umbral)
        self.assertGreaterEqual(alineadas / float(len({n["time_ms"] for n in self.notas})), 0.95)


class JuezCincoCarriles(unittest.TestCase):
    def test_pulsar_a_tiempo_es_perfect_en_los_cinco_carriles(self):
        c = cargar("duelo_dificil.json")
        d = Ritmo.Duelo(c)
        self.assertEqual(d.carriles, 5)
        d.empezar()
        for n in c["notes"]:
            d.actualizar(n["time_ms"])
            self.assertEqual(d.pulsar(n["lane"], n["time_ms"]), "perfect")
        d.actualizar(c["duration_ms"] + 500)
        self.assertEqual(d.estado, Ritmo.RESULTS)
        self.assertEqual(d.precision(), 1.0)
        self.assertEqual(d.resultado()["calificacion"], "S")
        self.assertEqual(d.max_combo, len(c["notes"]))

    def test_sin_pulsar_pierde_y_un_carril_6_no_existe(self):
        c = cargar("duelo_dificil.json")
        d = Ritmo.Duelo(c)
        d.empezar()
        self.assertIsNone(d.pulsar(5, c["notes"][0]["time_ms"]))
        d.actualizar(c["duration_ms"] + 500)
        self.assertFalse(d.exito())
        malo = dict(c, notes=[dict(c["notes"][0], lane=5)])
        self.assertTrue(Ritmo.validar_chart(malo))

    def test_normal_facil_y_arena_siguen_con_cuatro_carriles(self):
        for nombre, notas in (("duelo_historia_normal.json", 98), ("duelo_feria_normal.json", 43)):
            c = cargar(nombre)
            self.assertNotIn("lanes", c)
            self.assertEqual(Ritmo.Duelo(c).carriles, 4)
            self.assertEqual(len(c["notes"]), notas)
            self.assertEqual(Ritmo.validar_chart(c), [])


if __name__ == "__main__":
    unittest.main()
