"""
Duelo de Frecuencias en la Arena Online (HTTPS) con reloj simulado:
2, 3 y 4 clientes completan el MISMO duelo; puntuaciones individuales recalculadas por el servidor;
clasificacion y final sincronizados; latencia (entregas tardias), desconexion, pausa rechazada,
resultados manipulados, duplicados y entrega antes de que suene la cancion.
"""
import random

import pytest

from clases.arena import duelo_online as DO


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture
def reloj(client):
    r = Reloj()
    client.app.state.arena.reloj = r
    return r


def post(client, codigo, orden, **datos):
    return client.post("/api/arena/salas/%s/%s" % (codigo, orden), json=datos)


def vista(client, codigo, token):
    r = client.get("/api/arena/salas/%s" % codigo, params={"token": token})
    assert r.status_code == 200, r.text
    return r.json()


def preparar(client, n, rondas_hasta_duelo=True):
    roles = ["ciudadano", "periodista", "influencer", "candidato"][:n]
    r = client.post("/api/arena/salas", json={"nombre": "J1", "rol": roles[0], "duelo": True, "modo_duelo": "feria"})
    assert r.status_code == 200, r.text
    codigo, tokens = r.json()["codigo"], [r.json()["token"]]
    for i, rol in enumerate(roles[1:]):
        t = client.post("/api/arena/salas/%s/unir" % codigo, json={"nombre": "J%d" % (i + 2), "rol": rol}).json()["token"]
        tokens.append(t)
        assert post(client, codigo, "listo", token=t, listo=True).status_code == 200
    assert post(client, codigo, "empezar", token=tokens[0]).status_code == 200
    return codigo, tokens


def jugar_consejo_hasta(client, reloj, codigo, tokens, fase):
    for _ in range(300):
        v = vista(client, codigo, tokens[0])
        if v["fase"] == fase:
            return v
        if v["fase"] == "ronda":
            for t in tokens:
                vt = vista(client, codigo, t)
                if not vt["ya_decidiste"]:
                    assert post(client, codigo, "accion", token=t, ronda=vt["ronda"], ruta=[2]).status_code == 200
            reloj.t += 1   # los jugadores automaticos deciden unos segundos despues
        elif v["fase"] in ("resultado", "duelo_resultado"):
            post(client, codigo, "continuar", token=tokens[0])
        else:
            reloj.t += 1
    raise AssertionError("no se llego a la fase %s (estoy en %s)" % (fase, v["fase"]))


def avanzar(client, reloj, codigo, tokens, segundos):
    """El tiempo pasa mientras los telefonos siguen consultando (presencia), como durante la cancion."""
    while segundos > 0:
        paso = min(5.0, segundos)
        reloj.t += paso
        segundos -= paso
        for t in tokens:
            client.get("/api/arena/salas/%s" % codigo, params={"token": t})


def entrega(chart, nivel, semilla):
    return DO.payload_bot(chart, nivel, random.Random(semilla))


@pytest.mark.parametrize("n", [2, 3, 4])
def test_2_3_4_clientes_completan_el_mismo_duelo(client, reloj, n):
    codigo, tokens = preparar(client, n)
    v = jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    assert v["ronda"] == v["total_rondas"] - 1          # el duelo abre la ultima ronda
    cfg = client.get("/api/arena/ritmo/feria").json()
    chart = cfg["chart"]
    # Todos reciben el mismo inicio y el mismo chart.
    inicios = {vista(client, codigo, t)["duelo"]["inicio_en_ms"] for t in tokens}
    assert len(inicios) == 1 and inicios.pop() > 0
    avanzar(client, reloj, codigo, tokens, DO.PREPARACION_S + chart["duration_ms"] / 1000.0 + 0.5)
    niveles = (0.95, 0.7, 0.45, 0.2)
    esperados = {}
    for i, t in enumerate(tokens):
        datos = entrega(chart, niveles[i], i)
        r = post(client, codigo, "duelo", token=t, id="d%d" % i, **datos)
        assert r.status_code == 200, r.text
        esperados[i] = DO.validar_y_puntuar(chart, datos, 10 ** 9)["normalizado"]
        assert r.json()["resultado"]["normalizado"] == esperados[i]   # el servidor recalcula, no confia
    v = vista(client, codigo, tokens[0])
    assert v["fase"] == "duelo_resultado"
    resumen = v["duelo_resumen"]
    assert resumen["ganador"] == "j1"
    assert [resumen["resultados"]["j%d" % (i + 1)]["normalizado"] for i in range(n)] == [esperados[i] for i in range(n)]
    for t in tokens[1:]:
        assert vista(client, codigo, t)["duelo_resumen"] == resumen
    # Despues: la ultima ronda civica, sus consecuencias y la eleccion con el campeon.
    v = jugar_consejo_hasta(client, reloj, codigo, tokens, "final")
    finales = [vista(client, codigo, t)["final"] for t in tokens]
    assert all(f == finales[0] for f in finales)
    torneo = finales[0]["torneo"]
    assert len(torneo["clasificacion"]) == n
    assert all(f["total"] == f["consejo"] + f["duelo"] for f in torneo["clasificacion"])
    assert torneo["duelo_ganador"] == "J1"
    assert all(f["duelo"] == resumen["resultados"][f["id"]]["normalizado"] for f in resumen["clasificacion"])


def test_desconexion_durante_el_duelo_no_bloquea(client, reloj):
    codigo, tokens = preparar(client, 3)
    jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    chart = client.get("/api/arena/ritmo/feria").json()["chart"]
    avanzar(client, reloj, codigo, tokens, DO.PREPARACION_S + chart["duration_ms"] / 1000.0)
    for i, t in enumerate(tokens[:2]):
        assert post(client, codigo, "duelo", token=t, **entrega(chart, .8, i)).status_code == 200
    # j3 dejo de responder: al vencer el margen el duelo se cierra y recibe 0.
    avanzar(client, reloj, codigo, tokens[:2], DO.MARGEN_FIN_S + 1)
    v = vista(client, codigo, tokens[0])
    assert v["fase"] == "duelo_resultado"
    assert v["duelo_resumen"]["resultados"]["j3"]["normalizado"] == 0


def test_latencia_entrega_tardia_dentro_del_margen(client, reloj):
    codigo, tokens = preparar(client, 2)
    jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    chart = client.get("/api/arena/ritmo/feria").json()["chart"]
    avanzar(client, reloj, codigo, tokens, DO.PREPARACION_S + chart["duration_ms"] / 1000.0 + DO.MARGEN_FIN_S - 1)   # red muy lenta
    assert post(client, codigo, "duelo", token=tokens[0], **entrega(chart, .9, 1)).status_code == 200
    assert vista(client, codigo, tokens[0])["fase"] == "duelo"           # aun espera a j2


def test_pausa_rechazada_y_reconexion_ve_el_mismo_inicio(client, reloj):
    codigo, tokens = preparar(client, 2)
    jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    assert post(client, codigo, "pausa", token=tokens[0], pausar=True).status_code == 409
    a = vista(client, codigo, tokens[1])["duelo"]["inicio_en_ms"]
    avanzar(client, reloj, codigo, tokens, 3)
    b = vista(client, codigo, tokens[1])["duelo"]["inicio_en_ms"]   # "recargar la pagina": mismo instante absoluto
    assert a - b == 3000


def test_resultados_manipulados_rechazados(client, reloj):
    codigo, tokens = preparar(client, 2)
    jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    chart = client.get("/api/arena/ritmo/feria").json()["chart"]
    n = len(chart["notes"])
    # Antes de que suene la cancion no se puede entregar un duelo perfecto.
    perfecto = {"juicios": ["perfect"] * n, "desvios": [((i % 7) - 3) * 9 for i in range(n)]}
    r = post(client, codigo, "duelo", token=tokens[0], **perfecto)
    assert r.status_code == 409 and "antes" in r.text
    avanzar(client, reloj, codigo, tokens, DO.PREPARACION_S + chart["duration_ms"] / 1000.0)
    casos = [
        {"juicios": ["perfect"] * n, "desvios": [80] * n},                      # juicio no corresponde al desvio
        {"juicios": ["perfect"] * n, "desvios": [0] * n},                       # robot: dispersion nula
        {"juicios": ["perfect"] * (n - 1), "desvios": [0] * (n - 1)},           # chart distinto
        {"juicios": ["miss"] * n, "desvios": [10] * n},                          # fallo con desvio
        dict(entrega(chart, .9, 3), dificultad="facil"),                         # otra dificultad
        dict(entrega(chart, .9, 3), calibracion_ms=900),                         # calibracion absurda
    ]
    for datos in casos:
        r = post(client, codigo, "duelo", token=tokens[0], **datos)
        assert r.status_code in (409, 422), (datos.get("desvios", [None])[:2], r.text)
    bueno = entrega(chart, .9, 3)
    assert post(client, codigo, "duelo", token=tokens[0], id="x1", **bueno).status_code == 200
    assert post(client, codigo, "duelo", token=tokens[0], id="x1", **bueno).status_code == 200   # mismo id: idempotente
    assert post(client, codigo, "duelo", token=tokens[0], id="x2", **bueno).status_code == 409   # segunda entrega


def test_progreso_en_vivo_visible_para_todos(client, reloj):
    codigo, tokens = preparar(client, 2)
    jugar_consejo_hasta(client, reloj, codigo, tokens, "duelo")
    assert post(client, codigo, "progreso", token=tokens[1], juzgadas=10, puntos=420, combo=7, precision=.8).status_code == 200
    prog = vista(client, codigo, tokens[0])["duelo"]["progreso"]
    assert prog["j2"]["combo"] == 7 and prog["j2"]["puntos"] == 420


def test_bots_juegan_el_duelo(client, reloj):
    r = client.post("/api/arena/salas", json={"nombre": "Ana", "rol": "ciudadano", "duelo": True})
    codigo, token = r.json()["codigo"], r.json()["token"]
    assert post(client, codigo, "bots", token=token).status_code == 200
    assert post(client, codigo, "empezar", token=token).status_code == 200
    jugar_consejo_hasta(client, reloj, codigo, [token], "duelo")
    chart = client.get("/api/arena/ritmo/feria").json()["chart"]
    avanzar(client, reloj, codigo, [token], DO.PREPARACION_S + chart["duration_ms"] / 1000.0)
    assert post(client, codigo, "duelo", token=token, **entrega(chart, .9, 9)).status_code == 200
    res = vista(client, codigo, token)["duelo_resumen"]["resultados"]
    assert len(res) == 4 and all(v["normalizado"] > 0 for v in res.values())


def test_config_ritmo_sale_del_juego():
    from clases.Ritmo import VENTANAS_MS, VALOR_JUICIO
    cfg = DO.config_cliente("historia")
    assert cfg["ventanas"] == VENTANAS_MS and cfg["valores"] == VALOR_JUICIO
    assert cfg["chart"] == DO.cargar_chart("historia")
