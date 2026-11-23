"""
Central de Emergencias (clases/CentralEmergencias.py): grafo, Dijkstra, BFS, grafo dinamico, ambulancias,
emergencias, bloqueos, desvios, recursos, hospitales, tiempos, puntuacion, rejuego y fases.
"""
import os
import random
import sys
import time
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases import CentralEmergencias as CE  # noqa: E402


def bellman_ford(g, origen, prioridad=False):
    dist = [1 << 40] * len(CE.NODOS)
    dist[origen] = 0
    for _ in range(len(CE.NODOS)):
        for i, (a, b, _t, _n) in enumerate(CE.CALLES):
            if g.bloqueada[i]:
                continue
            c = g.coste(i, prioridad)
            if dist[a] + c < dist[b]:
                dist[b] = dist[a] + c
            if dist[b] + c < dist[a]:
                dist[a] = dist[b] + c
    return dist


def escenario_simple(eventos, duracion_s=60, recursos=None):
    return {"modo": "prueba", "semilla": 0, "duracion": duracion_s * CE.TICKS_S, "eventos": eventos,
            "recursos": recursos or {"despejar": 1, "prioridad": 1}, "aislado": None}


def avanzar(p, ticks):
    for _ in range(ticks):
        p.avanzar()


class Grafo(unittest.TestCase):
    def test_mapa_conexo_y_coherente(self):
        g = CE.Grafo()
        self.assertTrue(all(g.bfs([0])))                       # sin bloqueos, toda la ciudad se alcanza
        self.assertGreaterEqual(len(CE.NODOS), 30)
        self.assertGreaterEqual(len(CE.CALLES), 45)
        for i, (a, b, tipo, _n) in enumerate(CE.CALLES):
            self.assertNotEqual(a, b)
            self.assertGreater(CE.BASE[i], 0)
            self.assertIn(tipo, CE.VELOCIDAD)
        puentes = [c for c in CE.CALLES if c[2] == "puente"]
        self.assertEqual(len(puentes), 3)                       # el rio solo se cruza por tres puentes

    def test_dijkstra_igual_a_bellman_ford_con_trafico_y_bloqueos(self):
        rng = random.Random(5)
        for caso in range(150):
            g = CE.Grafo()
            for i in range(len(CE.CALLES)):
                g.trafico[i] = rng.choice((0, 0, 1, 2))
                g.bloqueada[i] = rng.random() < 0.12
            o, d = rng.randrange(len(CE.NODOS)), rng.randrange(len(CE.NODOS))
            prioridad = caso % 5 == 0
            ref = bellman_ford(g, o, prioridad)[d]
            r = g.dijkstra(o, d, prioridad)
            if ref >= 1 << 40:
                self.assertIsNone(r)
                continue
            coste, nodos, aristas = r
            self.assertEqual(coste, ref)
            self.assertEqual((nodos[0], nodos[-1]), (o, d))
            self.assertEqual(len(aristas), len(nodos) - 1)
            for k, i in enumerate(aristas):                     # la ruta es una cadena de calles abiertas y contiguas
                self.assertFalse(g.bloqueada[i])
                self.assertEqual({CE.CALLES[i][0], CE.CALLES[i][1]}, {nodos[k], nodos[k + 1]})

    def test_trafico_cambia_la_ruta(self):
        g = CE.Grafo()
        o, d = CE._n(0, 2), CE._n(6, 2)                         # de punta a punta por la Av. Central
        rapida = g.dijkstra(o, d)
        self.assertTrue(all(CE.CALLES[i][3] == "Av. Central" for i in rapida[2]))
        for i in CE.GRUPOS_CALLES["avenida"]:
            g.trafico[i] = 2                                    # atasco: la avenida corta deja de ser la mejor
        congestionada = g.dijkstra(o, d)
        self.assertNotEqual(rapida[1], congestionada[1])
        self.assertLessEqual(congestionada[0], sum(g.coste(i) for i in rapida[2]))

    def test_bfs_y_zonas_aisladas(self):
        g = CE.Grafo()
        self.assertEqual(g.aislados(), [])
        sur_oeste = CE._n(0, 4)
        for _v, i in CE.ADY[sur_oeste]:
            g.bloqueada[i] = True
        self.assertEqual(g.aislados(), [sur_oeste])
        self.assertIsNone(g.dijkstra(CE.HOSPITALES[0][1], sur_oeste))
        for i in CE.GRUPOS_CALLES["puentes"]:                    # sin puentes, el Sur queda partido en dos
            g.bloqueada[i] = True
        alcanza_central = g.bfs([CE.HOSPITALES[0][1]])
        self.assertFalse(any(alcanza_central[k] for k in range(len(CE.NODOS)) if CE.NODOS[k][2] == "Sur"))
        # El Sur Oeste (columnas 0-3) no tiene hospital ni puente abierto; el Sur Este conserva la Clinica del Sur.
        self.assertEqual(g.aislados(), [CE._n(c, 4) for c in range(4)])

    def test_alternativa_distinta_y_evita_protesta_anunciada(self):
        p = CE.Central(escenario_simple([]))
        o, d = CE._n(4, 2), CE._n(0, 0)
        ops = p.opciones(o, d)
        self.assertEqual(len(ops), 2)
        self.assertNotEqual(ops[0][1], ops[1][1])
        self.assertLessEqual(ops[0][0], ops[1][0])
        anunciada = ops[0][2][len(ops[0][2]) // 2]
        p.g.aviso[anunciada] = True
        ops2 = p.opciones(o, d)
        self.assertNotIn(anunciada, ops2[1][2])                  # B esquiva la calle con protesta anunciada


class Simulacion(unittest.TestCase):
    def test_despacho_recogida_y_entrega_a_tiempo(self):
        nodo = CE._n(5, 2)
        esc = escenario_simple([{"t": 0, "tipo": "emergencia", "id": 0, "nodo": nodo, "gravedad": "grave", "limite": 60 * CE.TICKS_S}])
        p = CE.Central(esc)
        p.avanzar()
        p.ordenar("despachar", 0, 0, 0)
        visto = set()
        while p.jugando():
            p.avanzar()
            visto.add(p.ambulancias[0].estado)
            if p.ambulancias[0].estado == "esperando_hospital" and not p.ambulancias[0].objetivo:
                p.ordenar("hospital", 0, 0, 0)
        e = p.emergencias[0]
        self.assertEqual(e.estado, "a_tiempo")
        self.assertTrue({"ruta", "recogiendo", "esperando_hospital", "entregando"} <= visto)
        self.assertEqual(e.hospital, 0)
        self.assertEqual(p.resumen()["a_tiempo"], 1)
        self.assertTrue(p.exito())

    def test_ordenes_invalidas_se_ignoran(self):
        esc = escenario_simple([{"t": 0, "tipo": "emergencia", "id": 0, "nodo": CE._n(1, 1), "gravedad": "grave", "limite": 900}])
        p = CE.Central(esc)
        p.avanzar()
        for o in (("despachar", 1, 0, 0), ("despachar", 0, 9, 0), ("despachar", 0, 0, 5), ("hospital", 0, 0, 0),
                  ("desviar", 0, 0, 0), ("despejar", 3, 0, 0), ("prioridad", 2, 0, 0)):
            p.ordenar(*o)                                       # ambulancia inactiva, emergencia o opcion inexistentes...
        p.avanzar()
        self.assertEqual(p.ordenes, [])
        self.assertEqual(p.ambulancias[0].estado, "libre")

    def test_bloqueo_en_ruta_detiene_y_desvio_reanuda(self):
        o, d = CE._n(4, 2), CE._n(0, 2)
        ruta = CE.Grafo().dijkstra(o, d)[2]
        cortada = ruta[2]
        esc = escenario_simple([{"t": 0, "tipo": "emergencia", "id": 0, "nodo": d, "gravedad": "moderado", "limite": 80 * CE.TICKS_S},
                                {"t": 12, "tipo": "bloqueo", "arista": cortada}])
        p = CE.Central(esc)
        p.avanzar()
        p.ordenar("despachar", 0, 0, 0)
        while p.jugando() and p.ambulancias[0].estado != "detenida":
            p.avanzar()
        a = p.ambulancias[0]
        self.assertEqual(a.estado, "detenida")
        self.assertTrue(any(t == "ruta_bloqueada" for _k, t, _d in p.eventos))
        avanzar(p, 30)
        self.assertEqual(a.estado, "detenida")                  # sin decision no se mueve
        p.ordenar("desviar", 0, 0, 0)
        p.avanzar()
        avanzar(p, 5)
        self.assertEqual(a.estado, "ruta")
        self.assertNotIn(cortada, p._aristas_ruta(a))
        self.assertEqual(p.desvios, 1)

    def test_mediacion_abre_la_calle_y_gasta_recurso(self):
        esc = escenario_simple([{"t": 0, "tipo": "bloqueo", "arista": 5},
                                {"t": 50 * CE.TICKS_S, "tipo": "emergencia", "id": 0, "nodo": 3, "gravedad": "grave", "limite": 900}],
                               recursos={"despejar": 1, "prioridad": 0})
        p = CE.Central(esc)
        p.avanzar()
        self.assertTrue(p.g.bloqueada[5])
        p.ordenar("despejar", 5)
        avanzar(p, CE.DESPEJE + 2)
        self.assertFalse(p.g.bloqueada[5])
        self.assertEqual(p.recursos["despejar"], 0)
        p.ordenar("despejar", 5)                                # sin recursos ni bloqueo: no hace nada
        p.avanzar()
        self.assertEqual(p.usados["despejar"], 1)

    def test_ruta_prioritaria_ignora_el_trafico(self):
        eventos = [{"t": 0, "tipo": "trafico", "arista": i, "nivel": 2} for i in range(len(CE.CALLES))]
        tiempos = []
        for prioridad in (False, True):
            esc = escenario_simple(eventos + [{"t": 0, "tipo": "emergencia", "id": 0, "nodo": CE._n(0, 0), "gravedad": "grave",
                                                "limite": 90 * CE.TICKS_S}], recursos={"despejar": 0, "prioridad": 1})
            p = CE.Central(esc)
            p.avanzar()
            if prioridad:
                p.ordenar("prioridad", 0)
            p.ordenar("despachar", 0, 0, 0)
            while p.ambulancias[0].estado != "recogiendo":
                p.avanzar()
            tiempos.append(p.tick)
        self.assertLess(tiempos[1], tiempos[0] * 0.6)

    def test_camas_y_hospital_automatico(self):
        nodo = CE._n(1, 1)
        esc = escenario_simple([{"t": 0, "tipo": "emergencia", "id": 0, "nodo": nodo, "gravedad": "grave", "limite": 90 * CE.TICKS_S}])
        p = CE.Central(esc)
        p.camas[0] = 0                                          # Hospital Central lleno
        p.avanzar()
        p.ordenar("despachar", 0, 0, 0)
        while p.ambulancias[0].estado != "esperando_hospital":
            p.avanzar()
        p.ordenar("hospital", 0, 0, 0)                          # sin cama: rechazado
        p.avanzar()
        self.assertEqual(p.ambulancias[0].estado, "esperando_hospital")
        avanzar(p, CE.AUTO_HOSPITAL + 2)                        # nadie elige: la tripulacion va al mas rapido CON cama
        self.assertTrue(any(t == "auto_hospital" for _k, t, _d in p.eventos))
        self.assertNotEqual(p.emergencias[0].hospital, 0)

    def test_paciente_sin_atender_libera_la_ambulancia(self):
        esc = escenario_simple([{"t": 0, "tipo": "emergencia", "id": 0, "nodo": CE._n(0, 0), "gravedad": "critico", "limite": 3 * CE.TICKS_S}])
        p = CE.Central(esc)
        p.avanzar()
        p.ordenar("despachar", 0, 0, 0)
        avanzar(p, 6 * CE.TICKS_S)
        self.assertEqual(p.emergencias[0].estado, "sin_atender")
        a = p.ambulancias[0]
        self.assertIsNone(a.objetivo)                           # la ambulancia deja de ir hacia alli
        self.assertEqual(a.ruta, [])
        while p.jugando():
            p.avanzar()
        self.assertEqual(p.resumen()["score_normalized"], 0)
        self.assertFalse(p.exito())

    def test_refuerzos_y_fases(self):
        esc = CE.generar_escenario("historia", 3)
        fases = [e for e in esc["eventos"] if e["tipo"] == "fase"]
        self.assertEqual([f["subtitulo"] for f in fases], ["Primera emergencia", "Ciudad congestionada", "Crisis"])
        p = CE.Central(esc)
        activas = []
        while p.jugando():
            p.avanzar()
            activas.append((p.fase, sum(a.activa for a in p.ambulancias)))
        self.assertEqual(max(n for f, n in activas if f == 1), 1)
        self.assertEqual(max(n for f, n in activas if f == 2), 2)
        self.assertEqual(max(n for f, n in activas if f == 3), 3)

    def test_fase_3_aisla_un_barrio(self):
        for semilla in range(1, 6):
            esc = CE.generar_escenario("feria", semilla)
            p = CE.Central(esc)
            aislado = False
            while p.jugando() and not aislado:
                p.avanzar()
                aislado = esc["aislado"] in p.g.aislados()
            self.assertTrue(aislado, semilla)
            self.assertEqual(p.fase, 3)


class Turno30(unittest.TestCase):
    def test_el_turno_dura_exactamente_30_segundos_en_todos_los_modos(self):
        """30 s de juego efectivo (900 ticks), se juegue bien, mal o nada; y lo mismo en Historia, Feria y Arena."""
        for modo in ("historia", "feria", "arena"):
            esc = CE.generar_escenario(modo, 4)
            self.assertEqual(esc["duracion"], 30 * CE.TICKS_S)
            for jugada in (CE.jugar_bot(esc, random.Random(1), 1.0), CE.jugar_bot(esc, random.Random(1), 0.2), CE.rejugar(esc, [])):
                self.assertEqual(jugada.tick, 30 * CE.TICKS_S, modo)
                self.assertEqual(jugada.resumen()["segundos"], 30)

    def test_cada_llamada_cabe_en_el_turno_y_hay_tres_fases(self):
        for semilla in range(1, 6):
            esc = CE.generar_escenario("feria", semilla)
            ems = [e for e in esc["eventos"] if e["tipo"] == "emergencia"]
            self.assertEqual(len(ems), 6)
            for e in ems:
                self.assertLessEqual(e["t"] + e["limite"], esc["duracion"])      # se puede resolver antes del final
                self.assertGreaterEqual(e["limite"], 7 * CE.TICKS_S)              # y con tiempo para decidir
            fases = [e["t"] for e in esc["eventos"] if e["tipo"] == "fase"]
            self.assertEqual(fases, [0, 9 * CE.TICKS_S, 19 * CE.TICKS_S])
            self.assertTrue(any(e["tipo"] == "bloqueo" for e in esc["eventos"] if e["t"] < 10 * CE.TICKS_S))

    def test_bloqueos_y_ambulancias_actuan_durante_los_30_segundos(self):
        esc = CE.generar_escenario("feria", 2)
        p = CE.jugar_bot(esc, random.Random(2), 1.0)
        tipos = [(t, tipo) for t, tipo, _d in p.eventos]
        for tipo in ("bloqueo", "despacho", "entregado", "refuerzo", "apertura"):
            self.assertTrue(any(x == tipo for _t, x in tipos), tipo)
        self.assertTrue(any(x == "bloqueo" and t > 19 * CE.TICKS_S for t, x in tipos))    # tambien en la crisis
        self.assertGreaterEqual(len(p.ordenes), 8)                                      # muchas decisiones en 30 s


class Puntuacion(unittest.TestCase):
    def test_determinista_y_rejugable(self):
        for modo in ("feria", "historia", "arena"):
            esc = CE.generar_escenario(modo, 42)
            self.assertEqual(esc, CE.generar_escenario(modo, 42))
            vivo = CE.jugar_bot(esc, random.Random(9), 0.8)
            rejugada = CE.rejugar(esc, vivo.ordenes)
            self.assertEqual(vivo.resumen(), rejugada.resumen())
            self.assertEqual([e.estado for e in vivo.emergencias], [e.estado for e in rejugada.emergencias])

    def test_jugar_bien_puntua_mas_que_jugar_mal_y_no_hacer_nada(self):
        for semilla in range(1, 7):
            esc = CE.generar_escenario("feria", semilla)
            bueno = CE.jugar_bot(esc, random.Random(semilla), 1.0).resumen()
            torpe = CE.jugar_bot(esc, random.Random(semilla), 0.1).resumen()
            nada = CE.rejugar(esc, []).resumen()
            self.assertGreaterEqual(bueno["score_normalized"], torpe["score_normalized"])
            self.assertEqual(nada["score_normalized"], 0)
            self.assertEqual(nada["a_tiempo"], 0)
            self.assertGreaterEqual(bueno["a_tiempo"], 4)

    def test_puntuacion_acotada_y_transparente(self):
        esc = CE.generar_escenario("historia", 8)
        p = CE.jugar_bot(esc, random.Random(1), 1.0)
        r = p.resumen()
        self.assertTrue(0 <= r["score_normalized"] <= 1000)
        self.assertEqual(r["a_tiempo"] + r["tarde"] + r["sin_atender"], r["total"])
        res = p.resultado()
        self.assertEqual(res["minijuego"], "contencion")          # mismo hueco que Caza-Rumores en la historia
        for k in ("exito", "calificacion", "puntos", "mensaje", "consecuencia"):
            self.assertIn(k, res)
        self.assertIn(res["calificacion"], "SABCD")
        # Los clics no puntuan: las mismas decisiones con ordenes redundantes (rechazadas) dan lo mismo.
        ruido = []
        for o in p.ordenes:
            ruido.append(o)
            ruido.append([o[0], "hospital", 0, 9, 0])            # hospital inexistente: rechazada
        self.assertEqual(CE.rejugar(esc, ruido).resumen()["score_normalized"], r["score_normalized"])

    def test_rejugar_rechaza_listas_manipuladas(self):
        esc = CE.generar_escenario("feria", 1)
        for mala in ("x", [[0, "despachar", 0]], [[0, "volar", 0, 0, 0]], [[5, "despachar", 0, 0, 0], [3, "despachar", 0, 0, 0]],
                     [[0, "despachar", True, 0, 0]], [[esc["duracion"] + 1, "despachar", 0, 0, 0]], [[0, "despachar", 0, 0, 0]] * 401):
            with self.assertRaises(CE.OrdenesInvalidas):
                CE.rejugar(esc, mala)

    def test_rendimiento(self):
        t0 = time.time()
        for semilla in range(10):
            CE.jugar_bot(CE.generar_escenario("historia", semilla), random.Random(semilla), 1.0)
        self.assertLess(time.time() - t0, 10.0)                  # 10 turnos completos con IA en menos de 10 s


if __name__ == "__main__":
    unittest.main()
