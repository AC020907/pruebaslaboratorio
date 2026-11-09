"""
Prueba de extremo a extremo del Duelo de Frecuencias en la Arena Online con NAVEGADORES REALES.

Chrome (headless, el instalado en el equipo) abre 2, 3 o 4 contextos aislados -cada uno es un "telefono"-
contra el servidor local (uvicorn). Cada cliente juega el Consejo, entra al duelo con un gesto (como una
persona), reproduce la cancion con Web Audio y pulsa con el motor real (?autoplay=1, solo en localhost:
pulsa por el MISMO camino que un dedo). Se comprueba que:
  - todos terminan el mismo duelo y la final (clasificacion y eleccion) es identica en todos;
  - la puntuacion que muestra cada navegador coincide con la que recalcula el servidor;
  - con latencia simulada distinta por jugador (CDP) los resultados siguen siendo validos;
  - una recarga en mitad de la cancion vuelve a entrar (lo que paso cuenta como Miss);
  - una desconexion en mitad de la cancion no bloquea: ese jugador recibe 0 al vencer el margen.

Uso:  python tests/e2e_duelo_online.py --base http://localhost:8791 --jugadores 2,3,4 --capturas <dir>
"""
import argparse
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROLES = ["ciudadano", "periodista", "influencer", "candidato"]
LATENCIAS = [0, 180, 400, 60]          # ms de ida extra por jugador (simulados con CDP)
HABILIDAD = [(12, 0.0), (35, 0.05), (60, 0.12), (90, 0.25)]   # error humano (ms) y notas olvidadas del autojugador


def log(*a):
    print(*a, flush=True)


def estado(page):
    return page.evaluate("() => S.estado && {fase:S.estado.fase, ronda:S.estado.ronda, version:S.estado.version}")


def jugar_consejo(page):
    """Recorre el arbol de decisiones con clics reales hasta decidir."""
    for _ in range(4):
        botones = page.query_selector_all("[data-op]")
        if not botones or botones[0].is_disabled():
            return
        botones[0].click()
        page.wait_for_timeout(150)


def correr(pw, base, n, capturas, escenario):
    navegador = pw.chromium.launch(channel="chrome", headless=True,
                                   args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"])
    paginas = []
    try:
        for i in range(n):
            movil = i % 2 == 1
            ctx = navegador.new_context(viewport={"width": 390, "height": 844} if movil else {"width": 1366, "height": 768},
                                        has_touch=movil, is_mobile=movil)
            page = ctx.new_page()
            page.on("console", lambda m, i=i: m.type == "error" and log("  consola j%d:" % (i + 1), m.text))
            page.on("pageerror", lambda e, i=i: log("  ERROR JS j%d:" % (i + 1), e))
            if LATENCIAS[i]:
                cdp = ctx.new_cdp_session(page)
                cdp.send("Network.enable")
                cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": LATENCIAS[i],
                                                              "downloadThroughput": -1, "uploadThroughput": -1})
            page.goto(base + "/arena?autoplay=1&sigma=%d&fallo=%.2f" % (HABILIDAD[i][0], HABILIDAD[i][1]))
            page.fill("#nombre", "Jugador%d" % (i + 1))
            page.click('[data-rol="%s"]' % ROLES[i])
            if i == 0:
                page.click("#btnCrear")
                page.wait_for_selector(".codigo-grande")
                codigo = page.inner_text(".codigo-grande").strip()
            else:
                page.fill("#codigo", codigo)
                page.click("#btnUnir")
                page.wait_for_selector("#listo")
                page.click("#listo")
            paginas.append(page)
        host = paginas[0]
        host.wait_for_selector("#empezar:not([disabled])", timeout=15000)
        if capturas:
            host.screenshot(path=os.path.join(capturas, "n%d_01_sala.png" % n))
        host.click("#empezar")
        log("sala %s con %d navegadores" % (codigo, n))

        # Consejo Civico hasta el duelo
        fin = time.time() + 240
        while time.time() < fin:
            fases = [estado(p) for p in paginas]
            if all(f and f["fase"] == "duelo" for f in fases):
                break
            for p, f in zip(paginas, fases):
                if f and f["fase"] == "ronda":
                    jugar_consejo(p)
            if fases[0] and fases[0]["fase"] == "resultado" and host.query_selector("#seguir"):
                host.click("#seguir")
            time.sleep(0.4)
        else:
            raise AssertionError("no se llego al duelo: %s" % fases)
        log("  duelo abierto (ronda %s)" % fases[0]["ronda"])
        for p in paginas:
            p.wait_for_selector("#btnEntrar", timeout=10000)
        if capturas:
            paginas[-1].screenshot(path=os.path.join(capturas, "n%d_02_duelo_entrar_%s.png" % (n, "movil" if n % 2 == 0 else "pc")))
        for p in paginas:
            p.click("#btnEntrar")          # el gesto que desbloquea el audio en un telefono real
        paginas[0].wait_for_function("() => D.activo === true", timeout=30000)
        log("  la cancion empezo en todos")
        time.sleep(14)
        if capturas:
            paginas[0].screenshot(path=os.path.join(capturas, "n%d_03_duelo_pc.png" % n))
            if n > 1:
                paginas[1].screenshot(path=os.path.join(capturas, "n%d_04_duelo_movil.png" % n))
        for k, p in enumerate(paginas):
            log("  j%d a mitad:" % (k + 1), p.evaluate("() => ({t: tiempoCancion(), conteo: D.motor.conteo, raf: !!D.raf, vis: document.visibilityState, lat: D.ctx.outputLatency, base: D.ctx.baseLatency})"))
        caido = None
        if escenario == "recarga" and n >= 2:
            p = paginas[1]
            p.goto(base + "/arena?sala=%s&autoplay=1&sigma=35&fallo=0.05" % codigo)   # recarga (con la URL que el juego deja: ?sala=...)
            p.wait_for_selector("#btnEntrar", timeout=15000)
            p.click("#btnEntrar")
            p.wait_for_function("() => D.activo === true", timeout=20000)
            p.wait_for_timeout(3000)
            info = p.evaluate("() => ({t: tiempoCancion(), conteo: D.motor.conteo, ctx: D.ctx.state, sig: D.motor.siguiente})")
            log("  j2 recargo en mitad de la cancion y volvio a entrar:", info)
            assert info["conteo"]["perfect"] + info["conteo"]["good"] > 0, info
        if escenario == "desconexion" and n >= 3:
            caido = n - 1
            paginas[caido].context.close()
            log("  j%d se desconecto en mitad de la cancion" % n)
        vivas = [p for k, p in enumerate(paginas) if k != caido]
        for p in vivas:
            p.wait_for_function("() => S.estado && S.estado.fase === 'duelo_resultado' || (S.estado && S.estado.fase === 'final')", timeout=120000)
        resumenes = [p.evaluate("() => S.estado.duelo_resumen") for p in vivas]
        assert all(json.dumps(r, sort_keys=True) == json.dumps(resumenes[0], sort_keys=True) for r in resumenes), "resumen distinto"
        locales = [p.evaluate("() => D.miResultado ? D.miResultado.normalizado : null") for p in vivas]
        jids = [p.evaluate("() => S.estado.yo") for p in vivas]
        srv = {j: resumenes[0]["resultados"][j]["normalizado"] for j in resumenes[0]["resultados"]}
        for jid, loc in zip(jids, locales):
            assert loc == srv[jid], ("puntos distintos", jid, loc, srv[jid])
        if caido is not None:
            assert srv["j%d" % n] == 0, srv
        log("  puntuaciones (servidor = navegador):", srv, "ganador:", resumenes[0]["ganador_nombre"])
        if capturas:
            vivas[0].screenshot(path=os.path.join(capturas, "n%d_05_resultado_duelo.png" % n), full_page=True)
            if len(vivas) > 1:
                vivas[1].screenshot(path=os.path.join(capturas, "n%d_06_resultado_duelo_movil.png" % n), full_page=True)
        # Ultima ronda del Consejo y final
        h = vivas[0]
        if h.query_selector("#seguir"):
            h.click("#seguir")
        fin = time.time() + 120
        while time.time() < fin:
            fases = [estado(p) for p in vivas]
            if all(f and f["fase"] == "final" for f in fases):
                break
            for p, f in zip(vivas, fases):
                if f and f["fase"] == "ronda":
                    jugar_consejo(p)
            if fases[0] and fases[0]["fase"] in ("resultado", "duelo_resultado") and h.query_selector("#seguir"):
                h.click("#seguir")
            time.sleep(0.4)
        finales = [p.evaluate("() => S.estado.final") for p in vivas]
        assert all(json.dumps(f, sort_keys=True) == json.dumps(finales[0], sort_keys=True) for f in finales), "final distinto"
        t = finales[0]["torneo"]
        assert len(t["clasificacion"]) == n
        log("  final sincronizado: campeon %s, alcalde %s" % (t["campeon_nombre"], finales[0]["ganador_nombre"]))
        if capturas:
            vivas[0].screenshot(path=os.path.join(capturas, "n%d_07_final.png" % n), full_page=True)
        return {"jugadores": n, "escenario": escenario, "duelo": srv, "campeon": t["campeon_nombre"],
                "alcalde": finales[0]["ganador_nombre"]}
    finally:
        navegador.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8791")
    ap.add_argument("--jugadores", default="2,3,4")
    ap.add_argument("--capturas", default="")
    args = ap.parse_args()
    if args.capturas:
        os.makedirs(args.capturas, exist_ok=True)
    escenarios = {2: "recarga", 3: "desconexion", 4: "normal"}
    resultados = []
    with sync_playwright() as pw:
        for n in [int(x) for x in args.jugadores.split(",")]:
            resultados.append(correr(pw, args.base, n, args.capturas, escenarios.get(n, "normal")))
    print(json.dumps(resultados, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
