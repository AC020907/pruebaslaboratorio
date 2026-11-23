"""
Juega el Duelo de Frecuencias en dificultad DIFICIL dentro del motor real de Ren'Py (audio real, reloj real) con
pulsaciones de TECLADO reales (D, F, Espacio, J, K) inyectadas en el bucle de eventos en el instante de cada nota.

    python tests/qa_ritmo_dificil.py --salida <carpeta> [--capturas] [--pasos teclado|mando|nada]

Sin --capturas mide la sincronizacion (desvio del reloj de la cancion, juicios) sin los tirones que provocan las
capturas de pantalla; con --capturas guarda la cuenta atras, el juego a los 20 s y los resultados.
"""
import argparse
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from qa_visual import SDK_DEFECTO, lanzar  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sdk", default=SDK_DEFECTO)
    ap.add_argument("--capturas", action="store_true")
    ap.add_argument("--pasos", default="teclado")
    ap.add_argument("--modo", default="historia")
    args = ap.parse_args()
    carpeta = os.path.abspath(args.salida)
    env = {"ALCALDE_QA": "ritmo", "ALCALDE_QA_PASOS": args.pasos, "ALCALDE_QA_MODO": args.modo,
           "ALCALDE_QA_DIFICULTAD": "dificil", "ALCALDE_QA_CAPTURAS": carpeta}
    proc, timeout = lanzar(args.sdk, env, carpeta)
    if args.capturas:
        # lanzar() desactiva las capturas por defecto: se relanza igual pero con ellas.
        proc.kill()
        proc.wait()
        entorno = dict(os.environ, ALCALDE_QA_SALIDA=os.path.join(carpeta, "salida.json"), ALCALDE_SEMILLA="123", **env)
        entorno.pop("CIVITAS_API", None)
        proc = subprocess.Popen([os.path.join(args.sdk, "renpy.exe"), os.path.join(AQUI, ".."), "--savedir",
                                 os.path.join(carpeta, "saves")], env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        proc.kill()
        sys.exit("tiempo agotado")
    with open(os.path.join(carpeta, "salida.json"), encoding="utf-8") as f:
        d = json.load(f)
    r = d["resultado"]
    resumen = {"dificultad": d.get("dificultad"), "carriles": d.get("carriles"), "notas": d["notas"], "estado": d["estado"],
               "conteo": r["conteo"], "precision": r["precision"], "calificacion": r["calificacion"], "max_combo": r["max_combo"],
               "exito": r["exito"], "drift_max_ms": d["drift_max_ms"], "hueco_max_ms": d.get("hueco_max_ms"),
               "fallos": d["fallos"][:10]}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    ok = (d["estado"] == "results" and d.get("carriles") == 5 and
          (args.pasos == "nada" or (r["conteo"]["miss"] <= 0.05 * d["notas"] and r["exito"])))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
