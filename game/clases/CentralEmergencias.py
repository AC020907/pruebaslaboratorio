"""
Central de Emergencias: estrategia en tiempo real y gestion de rutas (logica pura, sin Ren'Py).

La desinformacion provoca bloqueos en Ciudad Nova y hay personas que necesitan atencion medica urgente.
El jugador coordina ambulancias: elige a quien atender, por que ruta, a que hospital y cuando desviar.

Estructuras de datos y algoritmos (los que deciden la partida, no decoran):
- La ciudad es un GRAFO PONDERADO no dirigido con listas de adyacencia: cada interseccion es un vertice y cada
  calle una arista. El peso es el tiempo de recorrido en ticks y cambia en vivo con el trafico (nivel 0-2).
- DIJKSTRA (cola de prioridad con heapq, O((V + E) log V)) calcula la ruta mas rapida para cada despacho, cada
  eleccion de hospital y cada desvio, y los tiempos estimados que ve el jugador. La ruta alternativa es otro
  Dijkstra con las aristas de la primera (o las que tienen protesta anunciada) penalizadas.
- BFS (cola FIFO, O(V + E)) recorre las calles abiertas desde los hospitales: los vertices que no alcanza
  forman ZONAS AISLADAS. A una emergencia aislada no se puede despachar hasta despejar una calle.
- El grafo es DINAMICO: los eventos del escenario bloquean y desbloquean calles y cambian el trafico. Si un
  bloqueo cae sobre la ruta de una ambulancia, esta se detiene antes y el jugador decide el desvio.

Determinismo: paso fijo de 30 ticks/s, solo enteros, desempates por id. Las mismas ordenes en los mismos ticks
dan exactamente el mismo resultado aqui y en leaderboard/app/static/central_motor.js (tests/test_central_web.py).
El servidor de la Arena puntua REJUGANDO la lista de ordenes del jugador.
"""
import heapq
import random
from collections import deque

TICKS_S = 30

# ---------------------------------------------------------------- mapa de Ciudad Nova (1360 x 900)
# Columnas y filas de la cuadricula; el rio corre entre las filas 3 y 4 y solo lo cruzan tres puentes.
_COLS = (80, 290, 500, 700, 905, 1105, 1285)
_FILAS = (75, 245, 415, 580, 790)
_AJUSTE = {(1, 0): (10, 14), (2, 1): (-14, 8), (4, 0): (0, 18), (5, 1): (18, -6), (0, 2): (0, -10), (6, 2): (-6, 12),
           (1, 3): (-12, 0), (4, 3): (10, -8), (2, 4): (16, -6), (6, 4): (-10, -12), (0, 4): (14, -4)}


def _barrio(c, f):
    if f == 4:
        return "Sur"
    if f <= 1:
        return "Norte" if c <= 2 else ("Centro" if c == 3 else "Medios")
    if c <= 1:
        return "Oeste"
    if c <= 3:
        return "Centro"
    return "Alcaldía"


NODOS = []                   # (x, y, barrio)
_ID = {}
for _f, _y in enumerate(_FILAS):
    for _c, _x in enumerate(_COLS):
        dx, dy = _AJUSTE.get((_c, _f), (0, 0))
        _ID[(_c, _f)] = len(NODOS)
        NODOS.append((_x + dx, _y + dy, _barrio(_c, _f)))

# Calles: (a, b, tipo, nombre). Tipos: avenida (rapida), calle, puente.
VELOCIDAD = {"avenida": 92, "calle": 62, "puente": 70}     # px por segundo sin trafico
_SIN = {((0, 0), (0, 1)), ((5, 0), (6, 0)), ((1, 1), (1, 2)), ((5, 1), (5, 2)), ((2, 3), (3, 3)), ((5, 3), (6, 3)),
        ((6, 1), (6, 2)), ((3, 4), (4, 4))}
_NOMBRE_FILA = ("Calle 1", "Calle 9", "Av. Central", "Calle del Río", "Calle Sur")
_NOMBRE_COL = ("Carrera Oeste", "Carrera 4", "Carrera 7", "Av. Libertad", "Carrera 12", "Carrera 15", "Carrera Este")
_PUENTES = {1: "Puente Oeste", 3: "Puente Central", 5: "Puente Sur"}
CALLES = []
for _f in range(len(_FILAS)):
    for _c in range(len(_COLS) - 1):
        if ((_c, _f), (_c + 1, _f)) not in _SIN:
            CALLES.append((_ID[(_c, _f)], _ID[(_c + 1, _f)], "avenida" if _f == 2 else "calle", _NOMBRE_FILA[_f]))
for _c in range(len(_COLS)):
    for _f in range(len(_FILAS) - 1):
        if ((_c, _f), (_c, _f + 1)) in _SIN:
            continue
        if _f == 3:
            if _c in _PUENTES:
                CALLES.append((_ID[(_c, 3)], _ID[(_c, 4)], "puente", _PUENTES[_c]))
            continue
        CALLES.append((_ID[(_c, _f)], _ID[(_c, _f + 1)], "avenida" if _c == 3 else "calle", _NOMBRE_COL[_c]))
# Diagonal del Parque: atajo entre el Norte y el Centro.
CALLES.append((_ID[(1, 0)], _ID[(2, 1)], "calle", "Diagonal del Parque"))

HOSPITALES = (  # (nombre, nodo, camas)
    ("Hospital Central", _ID[(2, 1)], 2),
    ("Clínica del Sur", _ID[(5, 4)], 2),
    ("Puesto Oeste", _ID[(0, 3)], 1),
)
AMBULANCIAS = (  # (numero, nodo de salida)
    (12, _ID[(4, 2)]),
    (7, _ID[(2, 1)]),
    (21, _ID[(5, 4)]),
)
NIVELES_TRAFICO = (100, 160, 240)          # % del tiempo base: fluido, denso, atasco
GRAVEDAD = {  # nombre visible, puntos base, tiempo limite (s) por defecto
    "critico": ("Crítico", 300, 38),
    "grave": ("Grave", 220, 52),
    "moderado": ("Moderado", 160, 70),
}
RECOGER, ENTREGA = 60, 45                  # ticks en la escena y en la puerta del hospital
AUTO_HOSPITAL = 180                        # si nadie elige hospital en 6 s, la tripulacion va al mas rapido con cama
DESPEJE = 90                               # una mediacion tarda 3 s en abrir una calle
PRIORIDAD = 600                            # ruta prioritaria: 20 s sin pagar el trafico
CAMA_CADA = 900                            # cada 30 s un hospital libera una cama (hasta su maximo)
AVISO = 240                                # las protestas se anuncian 8 s antes


def _largo(a, b):
    xa, ya, _ = NODOS[a]
    xb, yb, _ = NODOS[b]
    d2 = (xa - xb) ** 2 + (ya - yb) ** 2
    r = int(d2 ** 0.5)
    while r * r > d2:
        r -= 1
    while (r + 1) * (r + 1) <= d2:
        r += 1
    return r


BASE = []                                  # ticks de cada calle sin trafico
for _a, _b, _t, _n in CALLES:
    _v = VELOCIDAD[_t]
    BASE.append(-(-_largo(_a, _b) * TICKS_S // _v))


def _ady():
    ady = [[] for _ in NODOS]
    for i, (a, b, _t, _n) in enumerate(CALLES):
        ady[a].append((b, i))
        ady[b].append((a, i))
    for lista in ady:
        lista.sort()
    return ady


ADY = _ady()


def arista_entre(a, b):
    for v, i in ADY[a]:
        if v == b:
            return i
    return -1


# ---------------------------------------------------------------- grafo dinamico
class Grafo(object):
    def __init__(self):
        self.bloqueada = [False] * len(CALLES)
        self.trafico = [0] * len(CALLES)
        self.aviso = [False] * len(CALLES)   # protesta anunciada (todavia abierta)

    def coste(self, i, prioridad=False):
        if prioridad:
            return BASE[i]
        return BASE[i] * NIVELES_TRAFICO[self.trafico[i]] // 100

    def dijkstra(self, origen, destino, prioridad=False, penalizadas=None):
        """Ruta de menor tiempo. Devuelve (coste, [nodos desde origen], [aristas]) o None si no hay camino.
        Desempate determinista: la cola ordena por (distancia, vertice) y solo se mejora con '<' estricto."""
        n = len(NODOS)
        inf = 1 << 40
        dist = [inf] * n
        previo = [-1] * n
        via = [-1] * n
        dist[origen] = 0
        cola = [(0, origen)]
        while cola:
            d, u = heapq.heappop(cola)
            if d > dist[u]:
                continue
            if u == destino:
                break
            for v, i in ADY[u]:
                if self.bloqueada[i]:
                    continue
                c = self.coste(i, prioridad)
                if penalizadas is not None and penalizadas[i]:
                    c *= 4
                nd = d + c
                if nd < dist[v]:
                    dist[v] = nd
                    previo[v] = u
                    via[v] = i
                    heapq.heappush(cola, (nd, v))
        if dist[destino] >= inf:
            return None
        nodos, aristas = [destino], []
        while nodos[-1] != origen:
            aristas.append(via[nodos[-1]])
            nodos.append(previo[nodos[-1]])
        nodos.reverse()
        aristas.reverse()
        return sum(self.coste(i, prioridad) for i in aristas), nodos, aristas

    def bfs(self, origenes):
        """Vertices alcanzables por calles abiertas desde cualquiera de los origenes (cola FIFO)."""
        visto = [False] * len(NODOS)
        cola = deque()
        for o in origenes:
            if not visto[o]:
                visto[o] = True
                cola.append(o)
        while cola:
            u = cola.popleft()
            for v, i in ADY[u]:
                if not self.bloqueada[i] and not visto[v]:
                    visto[v] = True
                    cola.append(v)
        return visto

    def aislados(self):
        """Vertices que ningun hospital alcanza: zonas aisladas por los bloqueos."""
        visto = self.bfs([h[1] for h in HOSPITALES])
        return [k for k in range(len(NODOS)) if not visto[k]]


# ---------------------------------------------------------------- escenarios (las tres fases)
# Cada fase usa las mismas reglas: lo que cambia son las decisiones (mas emergencias que ambulancias, trafico,
# protestas anunciadas, un barrio aislado), no solo los temporizadores.
def _n(c, f):
    return _ID[(c, f)]


CANDIDATOS = {
    "Norte": [_n(0, 0), _n(1, 0), _n(0, 1), _n(1, 1), _n(2, 0)],
    "Medios": [_n(5, 0), _n(6, 0), _n(5, 1), _n(6, 1), _n(4, 0)],
    "Centro": [_n(3, 1), _n(2, 2), _n(3, 3), _n(2, 3)],
    "Oeste": [_n(0, 2), _n(1, 3), _n(1, 2)],
    "Alcaldía": [_n(5, 2), _n(6, 3), _n(4, 3), _n(6, 2)],
    "Sur": [_n(1, 4), _n(2, 4), _n(3, 4), _n(4, 4), _n(6, 4)],
}
MODOS = {
    # duracion (s); fases: (inicio s, titulo, subtitulo); emergencias: (s, barrio, gravedad);
    # protestas: (s, calle_candidatas, duracion s o None = hasta despejar); trafico: (s, calles, nivel); refuerzos: (s, ambulancia)
    "historia": {"duracion": 150, "recursos": {"despejar": 2, "prioridad": 2},
                 "fases": ((0, "Fase 1", "Primera emergencia"), (32, "Fase 2", "Ciudad congestionada"), (76, "Fase 3", "Crisis")),
                 "refuerzos": ((32, 1), (76, 2)),
                 "emergencias": ((2, "Norte", "grave"), (34, "Medios", "critico"), (36, "Oeste", "moderado"),
                                 (78, "Sur", "critico"), (82, "Norte", "grave"), (92, "Medios", "moderado"),
                                 (100, "Centro", "critico")),
                 "protestas": ((9, "ruta:0:0", 40), (38, "ruta:1:1", 40), (46, "puentes", 45), (80, "aislar", None),
                               (102, "ruta:0:6", 40)),
                 "trafico": ((32, "avenida", 2), (32, "libertad", 1), (60, "avenida", 1), (96, "libertad", 2))},
    "feria": {"duracion": 110, "recursos": {"despejar": 1, "prioridad": 1},
              "fases": ((0, "Fase 1", "Primera emergencia"), (26, "Fase 2", "Ciudad congestionada"), (58, "Fase 3", "Crisis")),
              "refuerzos": ((26, 1), (58, 2)),
              "emergencias": ((2, "Norte", "grave"), (27, "Medios", "critico"), (29, "Oeste", "moderado"),
                              (60, "Sur", "critico"), (64, "Norte", "grave"), (72, "Centro", "critico")),
              "protestas": ((8, "ruta:0:0", 30), (31, "ruta:1:1", 30), (36, "puentes", 35), (61, "aislar", None),
                            (74, "ruta:0:5", 30)),
              "trafico": ((26, "avenida", 2), (26, "libertad", 1), (70, "libertad", 2))},
}
MODOS["arena"] = dict(MODOS["historia"], duracion=140)
GRUPOS_CALLES = {
    "fase1": [i for i, c in enumerate(CALLES) if c[3] in ("Calle 9", "Carrera 7", "Diagonal del Parque")],
    "puentes": [i for i, c in enumerate(CALLES) if c[2] == "puente"],
    "centro": [i for i, c in enumerate(CALLES) if c[3] in ("Av. Central", "Av. Libertad") and
               NODOS[c[0]][2] in ("Centro", "Alcaldía") and NODOS[c[1]][2] in ("Centro", "Alcaldía")],
    "avenida": [i for i, c in enumerate(CALLES) if c[3] == "Av. Central"],
    "libertad": [i for i, c in enumerate(CALLES) if c[3] == "Av. Libertad"],
}


def generar_escenario(modo, semilla, tension=0):
    """Mismo modo y semilla -> mismo escenario (todos los jugadores de la Arena reciben este dict).
    tension > 0 (Arena: mucha desinformacion tras el Consejo): una protesta corta una calle del centro desde el inicio."""
    cfg = MODOS[modo]
    rng = random.Random("central|%s|%s" % (modo, semilla))
    ev = []
    usados = set()
    for k, (s, barrio, grav) in enumerate(cfg["emergencias"]):
        opciones = [n for n in CANDIDATOS[barrio] if n not in usados and n not in [h[1] for h in HOSPITALES]]
        nodo = rng.choice(opciones)
        usados.add(nodo)
        ev.append({"t": s * TICKS_S, "tipo": "emergencia", "id": k, "nodo": nodo, "gravedad": grav,
                   "limite": GRAVEDAD[grav][2] * TICKS_S})
    aislar_nodo = None
    for s, grupo, dur in cfg["protestas"]:
        if grupo.startswith("ruta:"):
            _r, k_amb, k_em = grupo.split(":")
            em = next(e for e in ev if e["tipo"] == "emergencia" and e["id"] == int(k_em))
            ruta = Grafo().dijkstra(AMBULANCIAS[int(k_amb)][1], em["nodo"])[2]
            calles = [ruta[len(ruta) // 2]] if ruta else []
        elif grupo == "aislar":
            # La emergencia critica del Sur queda incomunicada: se bloquean todas sus calles salvo... ninguna.
            em = next(e for e in ev if e["tipo"] == "emergencia" and NODOS[e["nodo"]][2] == "Sur")
            aislar_nodo = em["nodo"]
            calles = [i for _v, i in ADY[aislar_nodo]]
        else:
            pool = list(GRUPOS_CALLES[grupo])
            rng.shuffle(pool)
            calles = sorted(pool[:2 if grupo in ("puentes", "centro") else 1])
        for i in calles:
            if any(x["tipo"] == "bloqueo" and x["arista"] == i for x in ev):
                continue
            ev.append({"t": max(0, s * TICKS_S - AVISO), "tipo": "aviso", "arista": i})
            ev.append({"t": s * TICKS_S, "tipo": "bloqueo", "arista": i})
            if dur is not None:
                ev.append({"t": (s + dur) * TICKS_S, "tipo": "apertura", "arista": i})
    if tension:
        pool = [i for i in GRUPOS_CALLES["centro"] if not any(x["tipo"] == "bloqueo" and x["arista"] == i for x in ev)]
        rng.shuffle(pool)
        for i in sorted(pool[:tension]):
            ev.append({"t": 0, "tipo": "bloqueo", "arista": i})
            ev.append({"t": 60 * TICKS_S, "tipo": "apertura", "arista": i})
    for s, grupo, nivel in cfg["trafico"]:
        for i in GRUPOS_CALLES[grupo]:
            ev.append({"t": s * TICKS_S, "tipo": "trafico", "arista": i, "nivel": nivel})
    for s, amb in cfg["refuerzos"]:
        ev.append({"t": s * TICKS_S, "tipo": "refuerzo", "ambulancia": amb})
    for k, (s, titulo, sub) in enumerate(cfg["fases"]):
        ev.append({"t": s * TICKS_S, "tipo": "fase", "fase": k + 1, "titulo": titulo, "subtitulo": sub})
    orden = {"fase": 0, "refuerzo": 1, "trafico": 2, "aviso": 3, "apertura": 4, "bloqueo": 5, "emergencia": 6}
    ev.sort(key=lambda e: (e["t"], orden[e["tipo"]], e.get("arista", e.get("id", 0))))
    return {"modo": modo, "semilla": semilla, "duracion": cfg["duracion"] * TICKS_S, "eventos": ev,
            "recursos": dict(cfg["recursos"]), "aislado": aislar_nodo}


# ---------------------------------------------------------------- simulacion
class Emergencia(object):
    def __init__(self, e, tick):
        self.id, self.nodo, self.gravedad = e["id"], e["nodo"], e["gravedad"]
        self.aparece = tick
        self.limite = tick + e["limite"]
        self.estado = "espera"     # espera | asignada | atendiendo | traslado | a_tiempo | tarde | sin_atender
        self.ambulancia = -1
        self.despachada = -1       # tick del despacho (tiempo de respuesta)
        self.entregada = -1
        self.hospital = -1


class Ambulancia(object):
    def __init__(self, k, numero, nodo):
        self.k, self.numero = k, numero
        self.nodo = nodo           # vertice actual (o de salida de la arista en curso)
        self.activa = False
        self.estado = "inactiva"   # inactiva | libre | ruta | detenida | recogiendo | esperando_hospital | entregando
        self.ruta = []             # vertices pendientes (el primero es el siguiente)
        self.arista = -1           # arista en curso
        self.hacia = -1
        self.prog = 0
        self.dur = 0
        self.objetivo = None       # ("paciente", id) | ("hospital", indice)
        self.paciente = -1
        self.espera = 0
        self.prioridad_hasta = -1
        self.bloqueo_avisado = False
        self.recorrido = 0         # ticks en movimiento (eficiencia)


class Central(object):
    """Una partida. avanzar() simula un tick; ordenar() registra una orden para el tick actual."""

    def __init__(self, escenario):
        self.esc = escenario
        self.g = Grafo()
        self.tick = 0
        self.fin_tick = escenario["duracion"]
        self.ambulancias = [Ambulancia(k, num, nodo) for k, (num, nodo) in enumerate(AMBULANCIAS)]
        self.ambulancias[0].activa = True
        self.ambulancias[0].estado = "libre"
        self.emergencias = []
        self.camas = [h[2] for h in HOSPITALES]
        self.recursos = dict(escenario["recursos"])
        self.despejes = []           # (tick en que abre, arista)
        self.pendientes = list(escenario["eventos"])
        self.fase = 1
        self.estado = "jugando"      # jugando | fin
        self.ordenes = []            # registro [[tick, tipo, a, b, c]] (para rejugar en el servidor)
        self.desvios = 0
        self.usados = {"despejar": 0, "prioridad": 0}
        self.eventos = []            # (tick, tipo, dato) para la vista (sonido, avisos); no afecta a las reglas
        self._cola_ordenes = []

    # ----- consultas -----
    def jugando(self):
        return self.estado == "jugando"

    def emergencia(self, i):
        for e in self.emergencias:
            if e.id == i:
                return e
        return None

    def origen_de(self, a):
        """Vertice desde el que se calcula una ruta nueva (si va por una calle, el final de esa calle)."""
        return a.hacia if a.arista >= 0 else a.nodo

    def opciones(self, origen, destino, prioridad=False):
        """Hasta dos rutas: la mas rapida (Dijkstra) y una alternativa (Dijkstra con penalizaciones)."""
        if origen == destino:
            return [(0, [origen], [])]
        a = self.g.dijkstra(origen, destino, prioridad)
        if a is None:
            return []
        avisadas = [self.g.aviso[i] for i in range(len(CALLES))]
        if any(avisadas[i] for i in a[2]):
            pen = avisadas
        else:
            pen = [False] * len(CALLES)
            for i in a[2]:
                pen[i] = True
        b = self.g.dijkstra(origen, destino, prioridad, pen)
        if b is None or b[1] == a[1]:
            return [a]
        return [a, b]

    def eta_hospitales(self, a):
        """Para la ambulancia con paciente: [(indice, coste o -1 si no hay camino, camas)]."""
        res = []
        for k, (_nom, nodo, _c) in enumerate(HOSPITALES):
            op = self.opciones(self.origen_de(a), nodo, self.tick < a.prioridad_hasta)
            res.append((k, op[0][0] if op else -1, self.camas[k]))
        return res

    # ----- ordenes del jugador (se aplican al empezar el tick) -----
    def ordenar(self, tipo, a=0, b=0, c=0):
        self._cola_ordenes.append([self.tick, tipo, a, b, c])

    def _aplicar(self, o):
        _t, tipo, x, y, z = o
        ok = False
        if tipo == "despachar":
            ok = self._despachar(x, y, z)
        elif tipo == "hospital":
            ok = self._hospital(x, y, z)
        elif tipo == "desviar":
            ok = self._desviar(x, y)
        elif tipo == "despejar":
            ok = self._despejar(x)
        elif tipo == "prioridad":
            ok = self._prioridad(x)
        if ok:
            self.ordenes.append(list(o))
        return ok

    def _fijar_ruta(self, a, ruta_nodos):
        """ruta_nodos empieza en origen_de(a)."""
        a.ruta = list(ruta_nodos[1:])
        a.bloqueo_avisado = False
        if a.arista < 0:
            a.estado = "ruta" if a.ruta else a.estado

    def _despachar(self, k, em_id, opcion):
        if not 0 <= k < len(self.ambulancias):
            return False
        a = self.ambulancias[k]
        e = self.emergencia(em_id)
        if not a.activa or a.estado != "libre" or e is None or e.estado != "espera":
            return False
        op = self.opciones(self.origen_de(a), e.nodo, self.tick < a.prioridad_hasta)
        if not 0 <= opcion < len(op):
            return False
        e.estado, e.ambulancia, e.despachada = "asignada", k, self.tick
        a.objetivo = ("paciente", em_id)
        a.estado = "ruta"
        self._fijar_ruta(a, op[opcion][1])
        self.eventos.append((self.tick, "despacho", k))
        if not a.ruta:
            self._llegar(a)
        return True

    def _hospital(self, k, h, opcion):
        if not 0 <= k < len(self.ambulancias) or not 0 <= h < len(HOSPITALES):
            return False
        a = self.ambulancias[k]
        if a.estado != "esperando_hospital" or self.camas[h] <= 0:
            return False
        op = self.opciones(self.origen_de(a), HOSPITALES[h][1], self.tick < a.prioridad_hasta)
        if not 0 <= opcion < len(op):
            return False
        self.camas[h] -= 1
        e = self.emergencia(a.paciente)
        e.hospital = h
        a.objetivo = ("hospital", h)
        a.estado = "ruta"
        self._fijar_ruta(a, op[opcion][1])
        self.eventos.append((self.tick, "hacia_hospital", k))
        if not a.ruta:
            self._llegar(a)
        return True

    def _desviar(self, k, opcion):
        if not 0 <= k < len(self.ambulancias):
            return False
        a = self.ambulancias[k]
        if a.estado not in ("ruta", "detenida") or a.objetivo is None:
            return False
        destino = self._destino(a)
        op = self.opciones(self.origen_de(a), destino, self.tick < a.prioridad_hasta)
        if not 0 <= opcion < len(op):
            return False
        if op[opcion][1][1:] == a.ruta:
            return False
        self._fijar_ruta(a, op[opcion][1])
        if a.arista < 0:
            a.estado = "ruta"
        self.desvios += 1
        self.eventos.append((self.tick, "desvio", k))
        return True

    def _despejar(self, i):
        if not 0 <= i < len(CALLES) or not self.g.bloqueada[i] or self.recursos["despejar"] <= 0:
            return False
        if any(x == i for _t, x in self.despejes):
            return False
        self.recursos["despejar"] -= 1
        self.usados["despejar"] += 1
        self.despejes.append((self.tick + DESPEJE, i))
        self.eventos.append((self.tick, "mediacion", i))
        return True

    def _prioridad(self, k):
        if not 0 <= k < len(self.ambulancias) or self.recursos["prioridad"] <= 0:
            return False
        a = self.ambulancias[k]
        if not a.activa or a.estado == "inactiva" or self.tick < a.prioridad_hasta:
            return False
        self.recursos["prioridad"] -= 1
        self.usados["prioridad"] += 1
        a.prioridad_hasta = self.tick + PRIORIDAD
        self.eventos.append((self.tick, "prioridad", k))
        return True

    def _destino(self, a):
        tipo, x = a.objetivo
        return self.emergencia(x).nodo if tipo == "paciente" else HOSPITALES[x][1]

    # ----- eventos del escenario -----
    def _evento(self, e):
        t = e["tipo"]
        if t == "emergencia":
            em = Emergencia(e, self.tick)
            self.emergencias.append(em)
            self.eventos.append((self.tick, "emergencia", em.id))
        elif t == "aviso":
            self.g.aviso[e["arista"]] = True
            self.eventos.append((self.tick, "aviso", e["arista"]))
        elif t == "bloqueo":
            i = e["arista"]
            self.g.bloqueada[i] = True
            self.g.aviso[i] = False
            self.eventos.append((self.tick, "bloqueo", i))
            for a in self.ambulancias:
                if i in self._aristas_ruta(a):
                    a.bloqueo_avisado = True
                    self.eventos.append((self.tick, "ruta_bloqueada", a.k))
        elif t == "apertura":
            if self.g.bloqueada[e["arista"]]:
                self.g.bloqueada[e["arista"]] = False
                self.eventos.append((self.tick, "apertura", e["arista"]))
        elif t == "trafico":
            self.g.trafico[e["arista"]] = e["nivel"]
        elif t == "refuerzo":
            a = self.ambulancias[e["ambulancia"]]
            a.activa, a.estado = True, "libre"
            self.eventos.append((self.tick, "refuerzo", a.k))
        elif t == "fase":
            self.fase = e["fase"]
            self.eventos.append((self.tick, "fase", e["fase"]))

    def _aristas_ruta(self, a):
        """Calles que la ambulancia todavia no ha empezado a recorrer."""
        res = []
        previo = self.origen_de(a)
        for v in a.ruta:
            res.append(arista_entre(previo, v))
            previo = v
        if a.arista >= 0 and a.ruta and a.ruta[0] == a.hacia:
            res = res[1:]
        return res

    # ----- movimiento -----
    def _mover(self, a):
        if a.estado in ("recogiendo", "entregando"):
            a.espera -= 1
            if a.espera <= 0:
                self._fin_espera(a)
            return
        if a.estado == "esperando_hospital":
            a.espera -= 1
            if a.espera <= 0:
                self._auto_hospital(a)
            return
        if a.arista >= 0:
            a.prog += 1
            a.recorrido += 1
            if a.prog >= a.dur:
                a.nodo, a.arista, a.prog = a.hacia, -1, 0
                if a.ruta and a.ruta[0] == a.nodo:
                    a.ruta.pop(0)
                if not a.ruta:
                    self._llegar(a)
            return
        if a.estado in ("ruta", "detenida") and a.ruta:
            siguiente = a.ruta[0]
            i = arista_entre(a.nodo, siguiente)
            if i < 0 or self.g.bloqueada[i]:
                if a.estado != "detenida":
                    a.estado = "detenida"
                    self.eventos.append((self.tick, "detenida", a.k))
                return
            a.estado = "ruta"
            a.arista, a.hacia, a.prog = i, siguiente, 0
            a.dur = max(1, self.g.coste(i, self.tick < a.prioridad_hasta))

    def _llegar(self, a):
        if a.objetivo is None:
            a.estado = "libre"
            return
        tipo, x = a.objetivo
        if tipo == "paciente":
            e = self.emergencia(x)
            if e.estado != "asignada":
                a.objetivo, a.estado = None, "libre"
                return
            e.estado = "atendiendo"
            a.estado, a.espera = "recogiendo", RECOGER
            self.eventos.append((self.tick, "en_escena", a.k))
        else:
            a.estado, a.espera = "entregando", ENTREGA
            self.eventos.append((self.tick, "en_hospital", a.k))

    def _fin_espera(self, a):
        if a.estado == "recogiendo":
            e = self.emergencia(a.objetivo[1])
            e.estado = "traslado"
            a.paciente = e.id
            a.objetivo = None
            a.estado, a.espera = "esperando_hospital", AUTO_HOSPITAL
            self.eventos.append((self.tick, "paciente_a_bordo", a.k))
        else:
            e = self.emergencia(a.paciente)
            e.entregada = self.tick
            e.estado = "a_tiempo" if self.tick <= e.limite else "tarde"
            a.paciente, a.objetivo, a.estado = -1, None, "libre"
            self.eventos.append((self.tick, "entregado", e.id))

    def _auto_hospital(self, a):
        """La tripulacion no espera indefinidamente: va al hospital mas rapido con cama libre."""
        mejor = None
        for k, coste, camas in self.eta_hospitales(a):
            if camas > 0 and coste >= 0 and (mejor is None or coste < mejor[1]):
                mejor = (k, coste)
        if mejor is not None:
            self._hospital(a.k, mejor[0], 0)
            self.eventos.append((self.tick, "auto_hospital", a.k))
        else:
            a.espera = TICKS_S          # sin camas o sin camino: vuelve a intentarlo en 1 s

    # ----- un tick -----
    def avanzar(self):
        if not self.jugando():
            return
        for o in self._cola_ordenes:
            self._aplicar(o)
        self._cola_ordenes = []
        while self.pendientes and self.pendientes[0]["t"] <= self.tick:
            self._evento(self.pendientes.pop(0))
        for t_abre, i in list(self.despejes):
            if t_abre <= self.tick:
                self.despejes.remove((t_abre, i))
                if self.g.bloqueada[i]:
                    self.g.bloqueada[i] = False
                    self.eventos.append((self.tick, "apertura", i))
        if self.tick > 0 and self.tick % CAMA_CADA == 0:
            for k, h in enumerate(HOSPITALES):
                if self.camas[k] < h[2]:
                    self.camas[k] += 1
        for a in self.ambulancias:
            if a.activa:
                self._mover(a)
        for e in self.emergencias:
            if e.estado in ("espera", "asignada") and self.tick > e.limite:
                e.estado = "sin_atender"
                self.eventos.append((self.tick, "sin_atender", e.id))
                for a in self.ambulancias:
                    if a.objetivo == ("paciente", e.id):
                        a.objetivo, a.ruta = None, []
                        if a.arista < 0:
                            a.estado = "libre"
        self.tick += 1
        total = sum(1 for e in self.esc["eventos"] if e["tipo"] == "emergencia")
        resueltas = sum(1 for e in self.emergencias if e.estado in ("a_tiempo", "tarde", "sin_atender"))
        if self.tick >= self.fin_tick or (resueltas == total and not any(e["tipo"] == "emergencia" for e in self.pendientes)):
            self._terminar()

    def _terminar(self):
        for e in self.emergencias:
            if e.estado not in ("a_tiempo", "tarde"):
                e.estado = "sin_atender"
        self.estado = "fin"
        self.eventos.append((self.tick, "fin", None))

    # ----- resultado -----
    def resumen(self):
        total = sum(1 for e in self.esc["eventos"] if e["tipo"] == "emergencia")
        maximo = sum(GRAVEDAD[e["gravedad"]][1] * 5 // 4 for e in self.esc["eventos"] if e["tipo"] == "emergencia")
        bruto = 0
        a_tiempo = tarde = 0
        respuesta = []
        for e in self.emergencias:
            base = GRAVEDAD[e.gravedad][1]
            if e.estado == "a_tiempo":
                a_tiempo += 1
                margen = max(0, e.limite - e.entregada)
                bruto += base + base * margen // (4 * max(1, e.limite - e.aparece))
            elif e.estado == "tarde":
                tarde += 1
                bruto += base // 5
            if e.despachada >= 0:
                respuesta.append(e.despachada - e.aparece)
        bruto -= 15 * (self.usados["despejar"] + self.usados["prioridad"])
        bruto = max(0, bruto)
        normal = min(1000, bruto * 1000 // max(1, maximo))
        return {"score_raw": bruto, "score_normalized": normal, "a_tiempo": a_tiempo, "tarde": tarde,
                "sin_atender": total - a_tiempo - tarde, "total": total, "desvios": self.desvios,
                "recursos": self.usados["despejar"] + self.usados["prioridad"],
                "respuesta_media_s": ((sum(respuesta) // len(respuesta) + TICKS_S // 2) // TICKS_S) if respuesta else 0,
                "recorrido_s": sum(a.recorrido for a in self.ambulancias) // TICKS_S,
                "segundos": self.tick // TICKS_S, "ordenes": len(self.ordenes)}

    def exito(self):
        r = self.resumen()
        return self.estado == "fin" and r["a_tiempo"] * 5 >= r["total"] * 3

    def calificacion(self):
        if not self.exito():
            return "D"
        n = self.resumen()["score_normalized"]
        return "S" if n >= 820 else "A" if n >= 680 else "B" if n >= 540 else "C"

    def resultado(self):
        """Contrato de los minijuegos de la Historia. Ocupa el lugar de Caza-Rumores, asi que la clave sigue siendo
        'contencion' (la contencion de la crisis): finales, expediente, Puntuacion Civica y guardados no cambian."""
        nota = self.calificacion()
        if nota in ("S", "A"):
            consecuencia = {"desinformacion": -7, "confianza": 4, "conflictos": -3, "puntos": 14}
        elif nota in ("B", "C"):
            consecuencia = {"desinformacion": -3, "confianza": 2, "puntos": 7}
        else:
            consecuencia = {"desinformacion": 7, "conflictos": 4, "confianza": -4}
        r = self.resumen()
        mensaje = ("%d de %d pacientes llegaron a tiempo al hospital." % (r["a_tiempo"], r["total"]))
        return {"minijuego": "contencion", "juego": "central", "exito": self.exito(), "calificacion": nota,
                "puntos": r["score_normalized"], "a_tiempo": r["a_tiempo"], "tarde": r["tarde"],
                "sin_atender": r["sin_atender"], "total": r["total"], "desvios": r["desvios"], "recursos": r["recursos"],
                "respuesta_media_s": r["respuesta_media_s"], "mensaje": mensaje, "consecuencia": consecuencia}


# ---------------------------------------------------------------- rejugar (servidor) y piloto automatico
class OrdenesInvalidas(ValueError):
    pass


TIPOS_ORDEN = ("despachar", "hospital", "desviar", "despejar", "prioridad")


def rejugar(escenario, ordenes, max_ordenes=400):
    """Reproduce la lista de ordenes [[tick, tipo, a, b, c], ...] y devuelve la partida terminada."""
    if not isinstance(ordenes, list) or len(ordenes) > max_ordenes:
        raise OrdenesInvalidas("Lista de órdenes inválida.")
    previo = -1
    for o in ordenes:
        if (not isinstance(o, (list, tuple)) or len(o) != 5 or o[1] not in TIPOS_ORDEN
                or any(isinstance(v, bool) or not isinstance(v, int) for v in (o[0], o[2], o[3], o[4]))
                or not 0 <= o[0] <= escenario["duracion"] or o[0] < previo
                or not all(0 <= v < 64 for v in (o[2], o[3], o[4]))):
            raise OrdenesInvalidas("Orden inválida.")
        previo = o[0]
    p = Central(escenario)
    k = 0
    while p.jugando():
        while k < len(ordenes) and ordenes[k][0] == p.tick:
            o = ordenes[k]
            p.ordenar(o[1], o[2], o[3], o[4])
            k += 1
        p.avanzar()
    return p


class Despachador(object):
    """Jugador automatico (pruebas, QA visual y bots de la Arena). Usa las mismas ordenes que una persona.
    habilidad 1: prioriza por urgencia, evita protestas anunciadas, desvia y despeja a tiempo.
    habilidad baja: reacciona tarde, atiende por orden de llegada y a veces elige la ruta mas lenta."""

    def __init__(self, rng, habilidad=1.0):
        self.rng, self.h = rng, habilidad
        self.proximo = 0

    def ordenes(self, p):
        if p.tick < self.proximo:
            return
        self.proximo = p.tick + 6 + int((1 - self.h) * 150)
        h, rng = self.h, self.rng
        # 1) pacientes a bordo: hospital mas rapido con cama
        for a in p.ambulancias:
            if a.estado == "esperando_hospital" and rng.random() < h:
                mejor = None
                for k, coste, camas in p.eta_hospitales(a):
                    if camas > 0 and coste >= 0 and (mejor is None or coste < mejor[1]):
                        mejor = (k, coste)
                if mejor:
                    p.ordenar("hospital", a.k, mejor[0], 0)
                elif p.recursos["despejar"] > 0:
                    for _v, i in ADY[p.origen_de(a)]:
                        if p.g.bloqueada[i] and not any(x == i for _t, x in p.despejes):
                            p.ordenar("despejar", i)
                            break
        # 2) bloqueos en ruta: desviar o despejar
        for a in p.ambulancias:
            if (a.estado == "detenida" and rng.random() < 0.25 + h) or (a.bloqueo_avisado and a.estado == "ruta" and h > 0.5):
                op = p.opciones(p.origen_de(a), p._destino(a)) if a.objetivo else []
                if op:
                    p.ordenar("desviar", a.k, 0)
                elif a.estado == "detenida" and a.ruta:
                    p.ordenar("despejar", arista_entre(a.nodo, a.ruta[0]))
        # 3) emergencias en espera: la mas urgente con la ambulancia libre mas cercana
        libres = [a for a in p.ambulancias if a.activa and a.estado == "libre"]
        espera = [e for e in p.emergencias if e.estado == "espera"]
        if rng.random() < h:
            espera.sort(key=lambda e: (e.limite, e.id))
        aislados = set(p.g.aislados())
        for e in espera:
            if not libres:
                break
            if e.nodo in aislados:
                if p.recursos["despejar"] > 0 and h > 0.5:
                    for _v, i in ADY[e.nodo]:
                        if p.g.bloqueada[i] and not any(x == i for _t, x in p.despejes):
                            p.ordenar("despejar", i)
                            break
                continue
            mejor = None
            candidatas = libres if rng.random() < h else [rng.choice(libres)]   # sin criterio: la primera que ve
            for a in candidatas:
                op = p.opciones(p.origen_de(a), e.nodo)
                if op and (mejor is None or op[0][0] < mejor[1]):
                    mejor = (a, op[0][0], op)
            if mejor is None:
                continue
            a, _c, op = mejor
            opcion = 0
            if len(op) > 1 and (any(p.g.aviso[i] for i in op[0][2]) and h > 0.6 or rng.random() > 0.5 + h / 2):
                opcion = 1
            p.ordenar("despachar", a.k, e.id, opcion)
            libres.remove(a)
            if e.gravedad == "critico" and h > 0.7 and p.recursos["prioridad"] > 0 and op[opcion][0] > 8 * TICKS_S:
                p.ordenar("prioridad", a.k)


def jugar_bot(escenario, rng, habilidad=1.0):
    p = Central(escenario)
    bot = Despachador(rng, habilidad)
    while p.jugando():
        bot.ordenes(p)
        p.avanzar()
    return p


def config_cliente(escenario):
    """Todo lo que necesita el motor del navegador (central_motor.js): el mapa, las constantes y el escenario."""
    return {"escenario": escenario, "nodos": [list(n) for n in NODOS], "calles": [list(c) for c in CALLES], "base": list(BASE),
            "hospitales": [list(h) for h in HOSPITALES], "ambulancias": [list(a) for a in AMBULANCIAS],
            "gravedad": {k: list(v) for k, v in GRAVEDAD.items()},
            "constantes": {"TICKS_S": TICKS_S, "NIVELES_TRAFICO": list(NIVELES_TRAFICO), "RECOGER": RECOGER,
                           "ENTREGA": ENTREGA, "AUTO_HOSPITAL": AUTO_HOSPITAL, "DESPEJE": DESPEJE, "PRIORIDAD": PRIORIDAD,
                           "CAMA_CADA": CAMA_CADA}}
