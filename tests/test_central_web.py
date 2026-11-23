"""
Paridad de Central de Emergencias: leaderboard/app/static/central_motor.js (navegador, Arena Online) frente a
clases/CentralEmergencias.py. Las mismas ordenes en los mismos ticks (las del despachador automatico mas ordenes
al azar, validas e invalidas) deben dar el mismo estado cada 10 ticks, las mismas ordenes aceptadas y la misma
puntuacion; y el servidor debe puntuar igual la lista de ordenes que produce el JS.
"""
import json
import os
import random
import shutil
import subprocess
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases import CentralEmergencias as CE  # noqa: E402

MOTOR = os.path.join(RAIZ, "leaderboard", "app", "static", "central_motor.js")
NODE = shutil.which("node")
RUNNER = r"""
const M = require(process.argv[process.argv.length - 1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(casos.map(c => {
  const p = new M.Central(c.cfg), huellas = [];
  let k = 0;
  while (p.jugando()) {
    while (k < c.ordenes.length && c.ordenes[k][0] === p.tick) { const o = c.ordenes[k++]; p.ordenar(o[1], o[2], o[3], o[4]); }
    p.avanzar();
    if (p.tick % 10 === 0 || !p.jugando()) huellas.push(p.huella());
  }
  return {huellas, resumen: p.resumen(), aceptadas: p.ordenes, exito: p.exito()};
})));
"""
TIPOS = CE.TIPOS_ORDEN


def huella(p):
    h = [p.tick, p.estado, p.fase, list(p.camas), p.recursos["despejar"], p.recursos["prioridad"]]
    for a in p.ambulancias:
        h.append([a.nodo, a.arista, a.prog, a.dur, a.estado, len(a.ruta), a.paciente])
    for e in p.emergencias:
        h.append(e.estado)
    h.append(sum(1 for b in p.g.bloqueada if b))
    return h


def partida_python(esc, semilla, habilidad, ruido):
    """Juega con el despachador y anade ordenes al azar; devuelve TODAS las ordenes emitidas y las huellas."""
    rng = random.Random(semilla)
    p = CE.Central(esc)
    bot = CE.Despachador(random.Random(semilla + 1), habilidad)
    emitidas, huellas = [], []
    while p.jugando():
        bot.ordenes(p)
        if rng.random() < ruido:
            p.ordenar(rng.choice(TIPOS), rng.randrange(4), rng.randrange(8), rng.randrange(3))
        emitidas.extend(list(o) for o in p._cola_ordenes)
        p.avanzar()
        if p.tick % 10 == 0 or not p.jugando():
            huellas.append(huella(p))
    return emitidas, huellas, p


@unittest.skipIf(NODE is None, "Node.js no esta instalado")
class TestCentralWeb(unittest.TestCase):
    def test_paridad_tick_a_tick(self):
        casos, esperado = [], []
        for modo in ("feria", "historia", "arena"):
            for semilla, habilidad, ruido in ((1, 1.0, 0.0), (2, 0.5, 0.03), (3, 0.15, 0.08), (4, 0.8, 0.02)):
                esc = CE.generar_escenario(modo, semilla, tension=semilla % 2)
                emitidas, huellas, p = partida_python(esc, semilla, habilidad, ruido)
                cfg = json.loads(json.dumps(CE.config_cliente(esc)))
                casos.append({"cfg": cfg, "ordenes": emitidas})
                esperado.append((huellas, p))
        r = subprocess.run([NODE, "-e", RUNNER, MOTOR], input=json.dumps(casos), capture_output=True, text=True,
                           encoding="utf-8", timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        salida = json.loads(r.stdout)
        for k, ((huellas, p), js) in enumerate(zip(esperado, salida)):
            self.assertEqual(json.loads(json.dumps(huellas)), js["huellas"], "caso %d" % k)
            self.assertEqual(p.resumen(), js["resumen"], "caso %d" % k)
            self.assertEqual(p.ordenes, js["aceptadas"], "caso %d" % k)
            self.assertEqual(p.exito(), js["exito"])
            # El servidor puntua las ordenes que acepto el navegador exactamente igual.
            self.assertEqual(CE.rejugar(casos[k]["cfg"]["escenario"], js["aceptadas"]).resumen(), js["resumen"])


if __name__ == "__main__":
    unittest.main()
