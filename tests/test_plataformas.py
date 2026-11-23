"""
Ruta de la Verdad (plataformero): motor de reglas.
Colisiones, coyote time, jump buffering, sin doble salto, salto variable, pinchos y caida con punto de control,
bloques intermitentes, meta, tiempo agotado, puntuacion (dominan evidencias y meta; no se puede ganar sin llegar),
rejuego determinista de la traza (lo que usa el servidor), trazas manipuladas e independencia de los FPS.
"""
import os
import random
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases import Plataformas as P  # noqa: E402


def avanzar(p, mascara, ticks):
    for _ in range(ticks):
        p.avanzar(mascara)


def nivel_prueba(filas, limite_s=30):
    """Nivel de laboratorio para probar una pieza aislada (se registra y se borra en cada prueba).
    La meta va en la esquina superior derecha, fuera de alcance: la prueba no termina por llegar a ella."""
    filas = [filas[0][:-1] + P.META] + list(filas[1:])
    P.NIVELES["_prueba"] = {"limite_s": limite_s, "mapa": filas}
    return P.Partida("_prueba")


def piloto_ruta_hasta(clave, condicion, max_ticks=20000):
    p = P.Partida(clave)
    piloto = P.PilotoRuta(clave)
    while not condicion(p) and p.jugando() and p.tick < max_ticks:
        p.avanzar(piloto.mascara(p))
    assert condicion(p), clave
    return p


def en_suelo(clave="tutorial"):
    p = P.Partida(clave)
    avanzar(p, 0, 3)
    assert p.en_suelo
    return p


class TestNiveles(unittest.TestCase):
    def test_niveles_validos_y_coherentes(self):
        for clave in P.NIVELES:
            n = P.Nivel(clave)
            self.assertGreaterEqual(len(n.evidencias), 4, clave)
            self.assertLessEqual(len(n.evidencias), len(P.FRAGMENTOS))
            self.assertLess(n.inicio[0], n.meta[0])
            self.assertEqual(n.tile(n.inicio[0], n.inicio[1] + 1), P.SOLIDO)     # se empieza sobre suelo
            for fx, fy in n.controles:
                self.assertEqual(n.tile(fx, fy + 1), P.SOLIDO, (clave, fx))      # se reaparece sobre suelo

    def test_todos_los_niveles_se_pueden_completar_con_todas_las_evidencias(self):
        """La ruta encontrada por busqueda sobre el motor (tools/plataformas_rutas.py) se rejuega: cada nivel se
        completa con TODAS las evidencias y sin detecciones, en menos del 55 % del tiempo (margen para personas)."""
        for clave in ("tutorial", "feria", "arena", "historia"):
            traza = P.rutas().get(clave)
            self.assertTrue(traza, clave)
            p = P.rejugar(clave, traza)
            self.assertTrue(p.completado(), clave)
            self.assertEqual(sorted(p.recogidas), list(range(len(p.nivel.evidencias))), clave)
            self.assertEqual(p.muertes, 0, clave)
            self.assertLess(p.tick, p.nivel.limite_ticks * 0.55, clave)

    def test_niveles_usan_las_piezas_nuevas_y_tienen_zonas(self):
        for clave in ("feria", "arena", "historia"):
            mapa = "".join(P.NIVELES[clave]["mapa"])
            for pieza in (P.PASARELA, P.IMPULSO, P.ESCANER, P.INTERMITENTE, P.PINCHO):
                self.assertIn(pieza, mapa, (clave, pieza))
            self.assertGreaterEqual(len(P.Nivel(clave).controles), 2, clave)
            self.assertEqual(len(P.NIVELES[clave]["mapa"]), 13)

    def test_bots_ordenados_por_habilidad(self):
        for clave in ("feria", "arena"):
            alto = P.bot(clave, random.Random(1), 0.95)
            medio = P.bot(clave, random.Random(1), 0.6)
            bajo = P.bot(clave, random.Random(1), 0.25)
            self.assertTrue(alto.completado())
            self.assertGreater(alto.puntuacion(), medio.puntuacion())
            self.assertGreaterEqual(medio.puntuacion(), bajo.puntuacion())

    def test_velocidad_maxima_menor_que_un_tile(self):
        self.assertLess(P.V_MAX, P.T)
        self.assertLess(P.V_CAIDA_MAX, P.T)
        self.assertLess(abs(P.V_SALTO), P.T)
        self.assertLess(abs(P.V_IMPULSO), P.T)


class TestFisica(unittest.TestCase):
    def test_gravedad_y_suelo(self):
        p = en_suelo()
        y = p.y
        avanzar(p, 0, 30)
        self.assertEqual(p.y, y)
        self.assertEqual((p.y + P.ALTO) % P.T, 0)        # apoyado exactamente sobre el tile

    def test_pared_del_borde_del_mundo(self):
        p = en_suelo()
        avanzar(p, P.IZQ, 120)
        self.assertEqual(p.x, 0)
        self.assertEqual(p.vx, 0)

    def test_salto_y_sin_doble_salto(self):
        p = en_suelo()
        y0 = p.y
        p.avanzar(P.SALTO)
        self.assertLess(p.vy, 0)
        avanzar(p, P.SALTO, 8)
        altura_1 = y0 - p.y
        p.avanzar(0)
        p.avanzar(P.SALTO)                # pulsar otra vez en el aire no vuelve a impulsar
        self.assertGreaterEqual(p.vy, P.V_CORTE)
        avanzar(p, 0, 80)
        self.assertTrue(p.en_suelo)
        self.assertGreater(altura_1, P.T)
        self.assertEqual(sum(1 for e in p.eventos if e[1] == "salto"), 1)

    def test_mantener_salto_no_rebota(self):
        p = en_suelo()
        avanzar(p, P.SALTO, 200)          # dejar el boton pulsado solo salta una vez
        self.assertEqual(sum(1 for e in p.eventos if e[1] == "salto"), 1)

    def test_salto_variable(self):
        def altura(ticks_pulsado):
            p = en_suelo()
            y0, minimo = p.y, p.y
            for i in range(70):
                p.avanzar(P.SALTO if i < ticks_pulsado else 0)
                minimo = min(minimo, p.y)
            return y0 - minimo
        self.assertGreater(altura(25), altura(3) + P.T // 2)
        self.assertGreaterEqual(altura(25), 2 * P.T)             # alcanza plataformas a 2 tiles
        self.assertLess(altura(25), 3 * P.T)                     # pero no a 3: los escalones importan

    def test_jump_buffer(self):
        p = en_suelo()
        avanzar(p, P.SALTO, 3)
        avanzar(p, 0, 200)
        saltos = sum(1 for e in p.eventos if e[1] == "salto")
        # pulsar BUFFER-2 ticks antes de aterrizar salta al tocar suelo
        p2 = en_suelo()
        avanzar(p2, P.SALTO, 25)
        while not p2.en_suelo or p2.vy < 0:
            antes = (p2.y, p2.vy)
            p2.avanzar(0)
            if p2.vy > 0 and self._ticks_para_suelo(p2) == P.BUFFER - 2:
                break
        p2.avanzar(P.SALTO)
        avanzar(p2, 0, P.BUFFER + 3)
        self.assertEqual(saltos, 1)
        self.assertEqual(sum(1 for e in p2.eventos if e[1] == "salto"), 2)

    @staticmethod
    def _ticks_para_suelo(p):
        import copy
        q = copy.deepcopy(p)
        k = 0
        while not q.en_suelo and k < 200:
            q.avanzar(0)
            k += 1
        return k

    def test_coyote_time(self):
        def salta_tras_dejar_el_borde(ticks_en_el_aire):
            p = en_suelo()                # el tutorial tiene un hueco tras el primer tramo
            while p.en_suelo:
                p.avanzar(P.DER)
            avanzar(p, P.DER, ticks_en_el_aire - 1)
            p.avanzar(P.DER | P.SALTO)
            return any(e[1] == "salto" for e in p.eventos)
        self.assertTrue(salta_tras_dejar_el_borde(P.COYOTE - 1))
        self.assertFalse(salta_tras_dejar_el_borde(P.COYOTE + 3))

    def test_caer_al_vacio_reaparece_en_el_inicio(self):
        p = en_suelo()
        x0 = p.x
        for _ in range(400):
            p.avanzar(P.DER)
            if p.muertes:
                break
        self.assertEqual(p.muertes, 1)
        self.assertEqual(p.x, x0)
        y = p.y
        avanzar(p, P.DER, P.RESPAWN_TICKS - 1)
        self.assertEqual((p.x, p.y), (x0, y))             # quieto durante la reaparicion

    def test_punto_de_control(self):
        q = piloto_ruta_hasta("tutorial", lambda q: any(e[1] == "control" for e in q.eventos))
        control = q.control
        while q.muertes == 0 and q.jugando():
            q.avanzar(P.IZQ)              # volver atras sin saltar: cae en el foso de pinchos
        self.assertEqual(q.muertes, 1)
        self.assertEqual(q.x // P.T, control[0])

    def test_correccion_de_esquina_y_aterrizaje(self):
        """Un salto que roza el borde inferior de un bloque por pocos px no se corta: se desliza y sigue subiendo."""
        n = P.Nivel("tutorial")
        # Un bloque al alcance de un salto normal: su borde inferior a 1 tile sobre el suelo de al lado.
        fx, fy = next((x, y) for y, fila in enumerate(n.filas) for x, ch in enumerate(fila)
                      if ch == P.SOLIDO and y <= 8 and n.tile(x - 1, y) == "." and n.tile(x, y + 1) == "."
                      and n.tile(x - 1, y + 2) == P.SOLIDO)
        for roce, debe_pasar in ((4 * P.SUB, True), (20 * P.SUB, False)):
            p = P.Partida("tutorial")
            suelo = next(y for y in range(fy + 1, n.alto) if n.tile(fx - 1, y) == P.SOLIDO)
            p.x, p.y, p.en_suelo = fx * P.T - P.ANCHO + roce, suelo * P.T - P.ALTO, True
            minimo = p.y
            for i in range(40):
                p.avanzar(P.SALTO)
                minimo = min(minimo, p.y)
            self.assertEqual(minimo < (fy + 1) * P.T - P.ALTO // 2, debe_pasar, roce)
            for _ in range(120):
                p.avanzar(0)
            self.assertTrue(any(e[1] == "aterriza" for e in p.eventos))

    def test_pasarela_se_atraviesa_desde_abajo_y_sostiene_al_caer(self):
        filas = ["." * 10] * 8 + ["....====..", ".S........"] + ["#" * 10] * 3
        p = nivel_prueba(filas)
        try:
            avanzar(p, 0, 3)
            p.x = 5 * P.T                                         # justo debajo de la pasarela (fila 8)
            avanzar(p, 0, 2)
            y_suelo = p.y
            minimo = p.y
            for i in range(40):
                p.avanzar(P.SALTO)
                minimo = min(minimo, p.y)
            self.assertLess(minimo, 8 * P.T - P.ALTO)            # los pies subieron por encima del borde: la atraveso
            avanzar(p, 0, 60)
            self.assertTrue(p.en_suelo)
            self.assertEqual(p.y + P.ALTO, 8 * P.T)              # quedo de pie SOBRE la pasarela
            self.assertLess(p.y, y_suelo)
            avanzar(p, P.DER, 40)                                 # al caminar fuera, cae: no es una pared
            avanzar(p, 0, 60)
            self.assertEqual(p.y, y_suelo)
        finally:
            P.NIVELES.pop("_prueba", None)

    def test_impulsor_lanza_alto_y_no_se_recorta(self):
        filas = ["." * 8] * 9 + [".S......", "###J####", "########", "########"]
        p = nivel_prueba(filas)
        try:
            avanzar(p, 0, 3)
            y0 = p.y
            p.x = 3 * P.T + (P.T - P.ANCHO) // 2
            minimo = p.y
            for i in range(90):
                p.avanzar(0)                                      # sin pulsar salto: el impulso no se corta
                minimo = min(minimo, p.y)
                if any(e[1] == "impulso" for e in p.eventos) and p.vy > 0:
                    break
            altura = y0 - minimo
            self.assertTrue(any(e[1] == "impulso" for e in p.eventos))
            self.assertGreater(altura, 4 * P.T)
            self.assertLess(altura, 5 * P.T)
        finally:
            P.NIVELES.pop("_prueba", None)

    def test_escaner_solo_detecta_encendido(self):
        filas = ["." * 8] * 5 + [".....#..", ".....L..", ".....L..", ".....L..", ".S...L.."] + ["#" * 8] * 3
        for desfase, muere in ((P.ESCANER_ACTIVO + 2, False), (0, True)):
            p = nivel_prueba(filas)
            try:
                avanzar(p, 0, 3)
                # Colocar al jugador sobre el haz en un instante de la fase elegida.
                objetivo = (desfase - 5 * P.ESCANER_DESFASE) % P.ESCANER_CICLO
                while P.escaner_fase(p.tick + 1, 5) != (objetivo + 5 * P.ESCANER_DESFASE) % P.ESCANER_CICLO:
                    p.avanzar(0)
                p.x = 5 * P.T + (P.T - P.ANCHO) // 2
                p.avanzar(0)
                self.assertEqual(p.muertes == 1, muere, desfase)
            finally:
                P.NIVELES.pop("_prueba", None)
        self.assertTrue(P.escaner_activo(0, 0))
        self.assertFalse(P.escaner_activo(P.ESCANER_ACTIVO, 0))
        self.assertNotEqual(P.escaner_activo(10, 0), P.escaner_activo(10, 2))   # columnas desfasadas: una ola

    def test_intermitentes(self):
        self.assertTrue(P.intermitente_activo(0))
        self.assertFalse(P.intermitente_activo(P.PARPADEO))
        n = P.Nivel("historia")
        fx, fy = next((x, y) for y, fila in enumerate(n.filas) for x, ch in enumerate(fila) if ch == P.INTERMITENTE)
        self.assertTrue(n.solido(fx, fy, 0))
        self.assertFalse(n.solido(fx, fy, P.PARPADEO))


class TestPuntuacion(unittest.TestCase):
    def test_meta_y_evidencias_dominan(self):
        perfecto = P.bot("feria", random.Random(3), 1.0)
        self.assertTrue(perfecto.completado())
        self.assertGreater(perfecto.puntuacion(), 700)
        self.assertLessEqual(perfecto.puntuacion(), 1000)
        parado = P.Partida("feria")
        avanzar(parado, 0, parado.nivel.limite_ticks + 5)
        self.assertEqual(parado.estado, "tiempo")
        self.assertEqual(parado.puntuacion(), 0)
        self.assertFalse(parado.resultado()["exito"])
        self.assertEqual(parado.resultado()["calificacion"], "D")

    def test_sin_meta_no_hay_bonos_ni_victoria(self):
        p = piloto_ruta_hasta("feria", lambda q: len(q.recogidas) >= 2)
        p.abandonar()
        total = len(p.nivel.evidencias)
        self.assertEqual(p.puntuacion(), (550 * len(p.recogidas) + total // 2) // total)
        self.assertLess(p.puntuacion(), 550)
        self.assertFalse(p.completado())

    def test_morir_no_multiplica_evidencias(self):
        p = piloto_ruta_hasta("tutorial", lambda q: bool(q.recogidas))
        while p.muertes < 2 and p.jugando():
            p.avanzar(P.DER)
        self.assertEqual(len(p.recogidas), len(set(p.recogidas)))
        self.assertLessEqual(len(p.recogidas), len(p.nivel.evidencias))

    def test_contrato_de_resultado_para_la_historia(self):
        r = P.bot("historia", random.Random(2), 1.0).resultado()
        self.assertEqual(r["minijuego"], "viralizacion")          # clave estable: finales y expediente no cambian
        for k in ("exito", "calificacion", "puntos", "consecuencia", "mensaje"):
            self.assertIn(k, r)
        res = P.bot("arena", random.Random(2), 1.0).resumen()
        for k in ("score_raw", "score_normalized", "completed", "evidence", "deaths", "elapsed_ms"):
            self.assertIn(k, res)

    def test_ayuda_de_tiempo_acotada(self):
        base = P.Nivel("historia").limite_ticks
        self.assertEqual(P.Nivel("historia", 20).limite_ticks, base + 20 * P.TICKS_S)
        self.assertEqual(P.Nivel("historia", 999).limite_ticks, base + P.EXTRA_MAX_S * P.TICKS_S)


class TestRejuego(unittest.TestCase):
    def test_la_traza_reproduce_exactamente_la_partida(self):
        for clave in P.NIVELES:
            for semilla, hab in ((1, 1.0), (2, 0.6), (3, 0.2)):
                p = P.bot(clave, random.Random(semilla), hab)
                q = P.rejugar(clave, p.traza)
                self.assertEqual((q.tick, q.x, q.y, q.recogidas, q.muertes, q.estado, q.puntuacion()),
                                 (p.tick, p.x, p.y, p.recogidas, p.muertes, p.estado, p.puntuacion()), (clave, semilla))

    def test_trazas_manipuladas(self):
        limite = P.Nivel("feria").limite_ticks
        for mala in (None, "x", [[1]], [[9, 3]], [[1, 0]], [[1, True]], [[1, 2.5]], [[1, limite + 1]], [[1, 1]] * 7000):
            with self.assertRaises(P.TrazaInvalida):
                P.rejugar("feria", mala)
        with self.assertRaises(P.TrazaInvalida):
            P.rejugar("no_existe", [[2, 10]])
        # Una traza que se queda corta cuenta lo conseguido, sin bono de meta.
        p = P.rejugar("feria", [[2, 60]])
        self.assertEqual(p.estado, "abandono")
        self.assertFalse(p.completado())

    def test_independiente_de_los_fps(self):
        """El render acumula tiempo y avanza a paso fijo: a 30, 60 o 144 FPS se simulan los mismos ticks."""
        referencia = P.rejugar("feria", P.rutas()["feria"])
        for fps in (30, 60, 144):
            p = P.Partida("feria")
            piloto = P.PilotoRuta("feria")
            acum, paso, dt = 0.0, 1.0 / P.TICKS_S, 1.0 / fps
            while p.jugando():
                acum += dt
                while acum >= paso and p.jugando():
                    acum -= paso
                    p.avanzar(piloto.mascara(p))
            self.assertEqual((p.tick, p.puntuacion(), p.recogidas), (referencia.tick, referencia.puntuacion(), referencia.recogidas), fps)


if __name__ == "__main__":
    unittest.main()
