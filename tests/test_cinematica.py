"""
Cinematica de apertura: linea de tiempo determinista, guion exacto, sincronia de pitidos y latidos, linea
plana definitiva, tono continuo, silencio, archivos de imagen y audio, e integracion antes del prologo.
"""
import os
import re
import sys
import unittest

import numpy as np
import soundfile as sf

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RAIZ, "game"))
sys.path.insert(0, os.path.join(RAIZ, "tools", "voces"))

from clases import cinematica_tiempos as CT  # noqa: E402

AUDIO = os.path.join(RAIZ, "game", "assets", "audio", "cine")
RPY = os.path.join(RAIZ, "game", "story", "cinematica.rpy")


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def energia_banda(x, sr, f0, f1, t0, t1):
    a, b = int(t0 * sr), int(t1 * sr)
    seg = x[a:b]
    if len(seg) < 16:
        return 0.0
    esp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1.0 / sr)
    return float(np.sum(esp[(fr >= f0) & (fr <= f1)] ** 2))


class LineaDeTiempo(unittest.TestCase):
    def test_planos_contiguos_y_orden_del_guion(self):
        nombres = [p[0] for p in CT.PLANOS]
        self.assertEqual(nombres, ["noticias", "ambulancia", "paciente", "monitor", "noticia_muerte", "titulo"])
        self.assertEqual(CT.PLANOS[0][1], 0.0)
        self.assertEqual(CT.PLANOS[-1][2], CT.DURACION)
        for (_a, _i, fin), (_b, ini, _f) in zip(CT.PLANOS, CT.PLANOS[1:]):
            self.assertEqual(fin, ini)
        self.assertEqual(CT.MONTAJE[0][1], 0.0)
        self.assertEqual(CT.MONTAJE[-1][2], CT.inicio("ambulancia"))
        self.assertTrue(30.0 <= CT.DURACION <= 40.0)

    def test_latidos_se_espacian_y_debilitan(self):
        t = [r for r, _a in CT.LATIDOS]
        self.assertEqual(t, sorted(t))
        audibles = [(r, a) for r, a in CT.LATIDOS if r >= CT.PITIDOS_DESDE]
        intervalos = [b[0] - a[0] for a, b in zip(audibles, audibles[1:])]
        self.assertTrue(all(y >= x - 1e-9 for x, y in zip(intervalos, intervalos[1:])), intervalos)
        amps = [a for _r, a in audibles]
        self.assertTrue(all(y <= x for x, y in zip(amps, amps[1:])), amps)
        self.assertGreater(intervalos[-1], 1.8 * intervalos[0])
        self.assertLess(amps[-1], 0.5)

    def test_cada_latido_dibuja_su_pico_y_despues_del_ultimo_la_senal_es_plana(self):
        for r, amp in CT.LATIDOS:
            self.assertAlmostEqual(CT.ecg(r), amp, delta=0.2 * amp)
        for k in range(0, 2000):
            t = CT.PLANA + k * 0.01
            self.assertEqual(CT.ecg(t), 0.0)
        for k in range(0, 2000):
            self.assertEqual(CT.pletismografia(CT.PLANA + 0.3 + k * 0.01), 0.0)
        # Ningun pico despues del ultimo latido (lo que se ve tras el es su onda T y la linea plana).
        picos = [CT.ecg(CT.ULTIMO_LATIDO + 0.05 + k * 0.002) for k in range(0, 400)]
        self.assertLess(max(picos), 0.3 * CT.LATIDOS[-1][1])

    def test_secuencia_de_la_muerte(self):
        self.assertLess(CT.inicio("monitor"), CT.ULTIMO_LATIDO)
        self.assertLess(CT.ULTIMO_LATIDO, CT.PLANA)
        self.assertLess(CT.PLANA, CT.TONO[0])
        self.assertEqual(CT.TONO[1], CT.CONGELADO[0])
        self.assertEqual(CT.CONGELADO[1], CT.inicio("noticia_muerte"))
        # El ultimo latido sale de la pantalla antes de que termine el tono: se ve la linea plana completa.
        self.assertLess(CT.ULTIMO_LATIDO + CT.VENTANA, CT.TONO[1] - 0.5)
        self.assertTrue(CT.inicio("noticia_muerte") <= CT.TITULAR < CT.inicio("titulo"))

    def test_vitales_bajan_y_no_inventan_valores_tras_la_linea_plana(self):
        fc = [CT.vitales(CT.PITIDOS_DESDE + k * 0.25)[0] for k in range(0, 36)]
        self.assertTrue(all(b <= a for a, b in zip(fc, fc[1:])), fc)
        self.assertGreater(min(CT.vitales(CT.PLANA - 0.01)), 0)

    def test_guion_exacto_en_voces_y_subtitulos(self):
        import cinematica_voces as V
        esperado = {
            "presentador_1": "Última hora. Los bloqueos continúan extendiéndose por Ciudad Nova tras la difusión de "
                             "información no verificada sobre el suministro de agua.",
            "paramedico": "¡Central, tenemos un paciente crítico! La avenida está completamente bloqueada. "
                          "Necesitamos una ruta alternativa.",
            "presentador_2": "Un paciente con una infección intestinal grave falleció tras sufrir retrasos en su "
                             "traslado de emergencia. Los bloqueos que paralizan Ciudad Nova habrían dificultado su atención.",
        }
        for nombre, texto in esperado.items():
            self.assertEqual(V.LINEAS[nombre][1], texto)
        inicios = dict(CT.VOCES)
        grupos = {"presentador_1": [], "paramedico": [], "presentador_2": []}
        for a, b, quien, texto in CT.SUBTITULOS:
            self.assertLess(a, b)
            voz = "paramedico" if quien == "AMBULANCIA 12" else ("presentador_1" if a < 20 else "presentador_2")
            self.assertGreaterEqual(a, inicios[voz] - 0.05)
            grupos[voz].append(texto)
        for nombre, textos in grupos.items():
            self.assertEqual(" ".join(textos), esperado[nombre])
        self.assertEqual(CT.DIAGNOSTICO, "Colitis infecciosa grave — complicaciones sistémicas")

    def test_titular_y_titulo_en_el_codigo(self):
        s = leer(RPY)
        for frase in ("LA DESINFORMACIÓN COBRÓ OTRA VÍCTIMA", "ALCALDE DIGITAL",
                      "Una mentira puede recorrer una ciudad. Sus consecuencias también.", "DRAMATIZACIÓN",
                      "Se investiga si los bloqueos retrasaron"):
            self.assertIn(frase, s)


class Audio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fx, cls.sr = sf.read(os.path.join(AUDIO, "apertura_fx.ogg"))
        voces, sr2 = sf.read(os.path.join(AUDIO, "apertura_voces.ogg"))
        assert sr2 == cls.sr
        cls.fx = fx.mean(axis=1)
        cls.voces = voces.mean(axis=1)

    def test_duracion(self):
        for x in (self.fx, self.voces):
            self.assertTrue(CT.DURACION <= len(x) / self.sr <= CT.DURACION + 0.5)

    def test_cada_pitido_suena_en_su_latido(self):
        audibles = [(r, a) for r, a in CT.LATIDOS if r >= CT.PITIDOS_DESDE]
        previo = CT.PITIDOS_DESDE - 0.3
        for r, amp in audibles:
            f = CT.tono_pitido(amp)
            # Referencia: el punto medio entre este latido y el anterior (ahi no hay pitido).
            m = (previo + r) / 2
            previo = r
            durante = energia_banda(self.fx, self.sr, f - 25, f + 25, r, r + 0.08)
            entre = energia_banda(self.fx, self.sr, f - 25, f + 25, m - 0.04, m + 0.04)
            self.assertGreater(durante, 8 * entre, "pitido de %.2f s" % r)

    def test_sin_pitidos_tras_el_ultimo_latido(self):
        f = CT.tono_pitido(CT.LATIDOS[-1][1])
        ultimo = energia_banda(self.fx, self.sr, 700, 1000, CT.ULTIMO_LATIDO, CT.ULTIMO_LATIDO + 0.08)
        despues = energia_banda(self.fx, self.sr, 700, 1000, CT.PLANA, CT.TONO[0] - 0.02)
        self.assertLess(despues, ultimo / 50, f)

    def test_tono_continuo_y_silencio(self):
        t0, t1 = CT.TONO
        for k in range(int((t1 - t0) / 0.2)):
            a = t0 + 0.05 + k * 0.2
            self.assertGreater(energia_banda(self.fx, self.sr, 940, 980, a, a + 0.1),
                               20 * energia_banda(self.fx, self.sr, 600, 900, a, a + 0.1) + 1.0)
        # Silencio: a partir de 60 ms tras el corte (un bloque de Vorbis puede arrastrar el final del tono).
        a, b = int((CT.CONGELADO[0] + 0.06) * self.sr), int(CT.CONGELADO[1] * self.sr)
        self.assertLess(float(np.max(np.abs(self.fx[a:b]))), 1e-3)
        self.assertLess(float(np.max(np.abs(self.voces[a:b]))), 1e-3)

    def test_voces_solo_donde_dice_el_guion(self):
        def rms(x, t0, t1):
            s = x[int(t0 * self.sr): int(t1 * self.sr)]
            return float(np.sqrt(np.mean(s ** 2)))
        self.assertLess(rms(self.voces, 15.0, CT.inicio("noticia_muerte")), 1e-3)
        self.assertLess(rms(self.voces, CT.inicio("titulo") + 0.2, CT.DURACION), 1e-3)
        for nombre, t0 in CT.VOCES:
            self.assertGreater(rms(self.voces, t0 + 0.3, t0 + 1.3), 0.02, nombre)
        self.assertLess(float(np.max(np.abs(self.voces))), 0.99)
        self.assertLess(float(np.max(np.abs(self.fx))), 0.99)


class Integracion(unittest.TestCase):
    def test_imagenes_existen(self):
        s = leer(RPY)
        nombres = set(re.findall(r'self\.img\("([a-z_0-9]+)"', s))
        nombres |= {"persona_%d" % i for i in range(8)} | {"luz_roja", "luz_azul"}
        for n in nombres:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "game", "images", "cinematica", n + ".png")), n)

    def test_va_antes_del_prologo_en_nueva_partida_y_modo_feria(self):
        for ruta, llamada in (("script.rpy", "call prologo\n"), (os.path.join("story", "modo_feria.rpy"), "call prologo(corto=True)\n")):
            lineas = [l.strip() for l in leer(os.path.join(RAIZ, "game", ruta)).splitlines()]
            k = lineas.index(llamada.strip())
            self.assertEqual(lineas[k - 1], "call cinematica_apertura", ruta)

    def test_no_toca_el_estado_de_la_partida(self):
        s = leer(RPY)
        self.assertNotIn("store.", s)
        self.assertNotRegex(s, r"(?m)^default ")
        self.assertNotRegex(s, r"(hecho|dar_pista|aplicar_consecuencia|subir_afinidad|calidad_decision)\(")
        self.assertIn('on "hide" action Function(cine_audio_detener)', s)
        self.assertIn('key "game_menu" action Return("omitida")', s)
        self.assertNotIn('key "dismiss"', s)


if __name__ == "__main__":
    unittest.main()
