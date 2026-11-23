"""Buscador de rutas de la Ruta de la Verdad: demuestra que cada nivel se puede completar con TODAS las evidencias.

    python tools/plataformas_rutas.py              # todos los niveles
    python tools/plataformas_rutas.py feria        # uno

Busqueda A* ponderada sobre el MOTOR REAL (clases/Plataformas.py), con macro-acciones de 4 ticks (derecha, saltar,
izquierda, quieto...). Va de objetivo en objetivo: cada evidencia (de izquierda a derecha) y despues la meta, sin
morir nunca. El estado visitado incluye posicion, velocidad, suelo y la fase de los bloques intermitentes y
escaneres, asi que los tramos con tiempo se resuelven esperando el momento justo.

Escribe game/clases/plataformas_rutas.json: {nivel: traza RLE}. La traza se REJUEGA con Plataformas.rejugar y se
comprueba antes de guardarla; las pruebas, los bots de la Arena y la QA visual usan esas rutas.
"""
import copy
import heapq
import json
import os
import sys
import time

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RAIZ, "game"))
from clases import Plataformas as P  # noqa: E402

SALIDA = os.path.join(RAIZ, "game", "clases", "plataformas_rutas.json")
ACCIONES = (P.DER, P.DER | P.SALTO, 0, P.SALTO, P.IZQ, P.IZQ | P.SALTO)
K = 4
FASES = 2400            # mcm(2 * PARPADEO, ESCANER_CICLO)


def clonar(p):
    q = copy.copy(p)
    q.recogidas = list(p.recogidas)
    q.eventos = []
    q.traza = []
    return q


def clave(p, columnas_tiempo):
    """La fase de intermitentes y escaneres solo cuenta cerca de ellos (lejos, esperar no cambia nada)."""
    fx = p.x // P.T
    cerca = any(c in columnas_tiempo for c in range(fx - 5, fx + 8))
    return (p.x // (3 * P.SUB), p.y // (3 * P.SUB), p.vx // 12, p.vy // 24, p.en_suelo, p.salto_previo, p.coyote > 0,
            (p.tick % FASES) // 6 if cerca else 0, len(p.recogidas), p.impulsado)


def buscar(p0, meta_fn, objetivo_px, con_fase, max_exp=600000):
    tx, ty = objetivo_px

    def h(p):
        cx = p.x + P.ANCHO // 2
        cy = p.y + P.ALTO // 2
        return abs(cx - tx) / float(P.V_MAX) + abs(cy - ty) / float(P.V_MAX) * 0.6

    cola = [(h(p0), 0, 0, p0, None)]
    vistos = {clave(p0, con_fase)}
    nodos = []           # (padre, accion)
    contador = 1
    exp = 0
    while cola and exp < max_exp:
        _f, g, ident, p, ref = heapq.heappop(cola)
        exp += 1
        for a in ACCIONES:
            q = clonar(p)
            muertes = q.muertes
            ok = True
            for _ in range(K):
                q.avanzar(a)
                if q.muertes > muertes or q.estado in ("tiempo", "abandono"):
                    ok = False
                    break
                if meta_fn(q):
                    break
            if not ok:
                continue
            nodos.append((ref, a))
            nid = len(nodos) - 1
            if meta_fn(q):
                plan = []
                k = nid
                while k is not None:
                    padre, acc = nodos[k]
                    plan.append(acc)
                    k = padre
                return q, list(reversed(plan)), exp
            c = clave(q, con_fase)
            if c in vistos:
                continue
            vistos.add(c)
            contador += 1
            heapq.heappush(cola, (g + K + 2.2 * h(q), g + K, contador, q, nid))
    return None, None, exp


def ruta_nivel(nivel):
    p = P.Partida(nivel)
    n = p.nivel
    con_fase = {fx for fila in n.filas for fx, ch in enumerate(fila) if ch in (P.INTERMITENTE, P.ESCANER)}
    plan_total = []
    objetivos = [("evidencia", i, n.evidencias[i]) for i in range(len(n.evidencias))] + [("meta", None, n.meta)]
    for tipo, i, (fx, fy) in objetivos:
        if tipo == "evidencia":
            if i in p.recogidas:
                continue
            meta_fn = (lambda i_: lambda q: i_ in q.recogidas)(i)
        else:
            meta_fn = lambda q: q.estado == "meta"   # noqa: E731
        objetivo = (fx * P.T + P.T // 2, fy * P.T + P.T // 2)
        t0 = time.time()
        q, plan, exp = buscar(clonar(p), meta_fn, objetivo, con_fase)
        if q is None:
            raise SystemExit("%s: no se encontro camino hasta %s %s (%d expansiones)" % (nivel, tipo, (fx, fy), exp))
        # Avanzar la partida real con el plan (deterministico: mismo resultado que en la busqueda).
        for a in plan:
            for _ in range(K):
                if meta_fn(p):
                    break
                p.avanzar(a)
        print("  %s %-9s %-10s %5d expansiones %5.1f s  t=%5.1f s" % (nivel, tipo, (fx, fy), exp, time.time() - t0, p.tick / 60.0))
        plan_total.extend(plan)
    traza = [list(s) for s in p.traza]
    r = P.rejugar(nivel, traza)
    assert r.completado() and len(r.recogidas) == len(n.evidencias) and r.muertes == 0, (nivel, r.estado, r.recogidas)
    return traza, r


def main():
    niveles = sys.argv[1:] or list(P.NIVELES)
    rutas = {}
    if os.path.exists(SALIDA):
        with open(SALIDA, encoding="utf-8") as f:
            rutas = json.load(f)
    for nivel in niveles:
        traza, r = ruta_nivel(nivel)
        rutas[nivel] = traza
        print("%s: meta en %.1f s de %d s, %d/%d evidencias, 0 detecciones, %d segmentos" % (
            nivel, r.tick / 60.0, r.nivel.limite_ticks // 60, len(r.recogidas), len(r.nivel.evidencias), len(traza)))
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(rutas, f, separators=(",", ":"))
    print("ok:", SALIDA)


if __name__ == "__main__":
    main()
