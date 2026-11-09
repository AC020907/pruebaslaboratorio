"""
Sala de Arena independiente del transporte (la usa la Arena Online por HTTPS).

Envuelve la misma Partida de reglas.py (unica fuente de verdad) y anade lo que necesita una sala online:
codigo, tokens secretos por jugador, anfitrion, "listo", reloj autoritativo, presencia (sin peticiones en
PRESENCIA_S segundos = desconectado), reconexion con el mismo token, jugadores automaticos e idempotencia
por id de mensaje. El tiempo avanza de forma perezosa: cada peticion llama a tick(), asi no hacen falta
hilos en el servidor web y el estado es igual de autoritativo.
"""
import random
import secrets
import threading
import time

from clases.arena.bot import elegir_ruta
from clases.arena.reglas import Partida, ROLES, MIN_JUGADORES, MAX_JUGADORES, NOMBRE_ROL
from clases.arena import duelo_online as DO
from clases.arena.torneo import ResultadoInvalido, consecuencias, puntos_consejo, mensaje_final, no_entregado, MAX_PRUEBA

PRESENCIA_S = 20.0
PAUSA_RESULTADO_S = 10.0
PAUSA_DUELO_S = 15.0


class ErrorSala(Exception):
    def __init__(self, codigo, mensaje):
        super(ErrorSala, self).__init__(mensaje)
        self.codigo, self.mensaje = codigo, mensaje


class SalaArena(object):
    def __init__(self, codigo, semilla=None, rondas=5, segundos=25, reloj=time.monotonic, duelo=True, modo_duelo="feria"):
        self.codigo = codigo
        self.reloj = reloj
        self.lock = threading.RLock()
        self.partida = Partida(semilla if semilla is not None else random.randrange(10 ** 9), rondas, segundos)
        self.tokens = {}            # token -> jid
        self.visto = {}             # jid -> ultimo instante en que pidio algo
        self.bots = {}              # jid -> (rng, instante en que decidira en esta ronda)
        self.listos = set()
        self.anfitrion = None
        self.ids_vistos = {}        # jid -> set(id de mensaje)
        self.limite = None
        self.restante_pausa = None
        self.siguiente_en = None
        self.creada = self.ultima_actividad = reloj()
        self.version = 0            # crece con cada cambio: el cliente evita redibujar si no cambio
        # Duelo de Frecuencias: gran final antes de la ultima ronda del Consejo (minimo 2 rondas para que haya antes y despues).
        self.duelo = bool(duelo) and rondas >= 2
        self.modo_duelo = modo_duelo
        self.chart = DO.cargar_chart(modo_duelo) if self.duelo else None
        self.duelo_inicio = self.duelo_fin = None
        self.duelo_res = {}         # jid -> resultado validado
        self.duelo_prog = {}        # jid -> progreso en vivo (solo se muestra; no puntua)
        self.duelo_resumen = None
        self.duelo_hecho = False
        self.torneo_final = False

    # ---------- utilidades ----------
    def _jid(self, token):
        jid = self.tokens.get(token)
        if jid is None:
            raise ErrorSala("token", "No perteneces a esta sala.")
        self.visto[jid] = self.reloj()
        self.partida.jugadores[jid].conectado = True
        return jid

    def _tocar(self):
        self.version += 1
        self.ultima_actividad = self.reloj()

    def _repetido(self, jid, mid):
        if not mid:
            return False
        vistos = self.ids_vistos.setdefault(jid, set())
        if mid in vistos:
            return True
        vistos.add(mid)
        return False

    # ---------- lobby ----------
    def unir(self, nombre, rol, bot=False):
        with self.lock:
            self.tick()
            jid = "j%d" % (len(self.tokens) + 1)
            error = self.partida.unir(jid, nombre, rol)
            if error:
                codigo = "llena" if "llena" in error else ("empezada" if "empez" in error else "rol")
                raise ErrorSala(codigo, error)
            token = secrets.token_urlsafe(18)
            self.tokens[token] = jid
            self.visto[jid] = self.reloj()
            if bot:
                self.bots[jid] = [random.Random("%s|%s" % (self.partida.semilla, jid)), None]
                self.listos.add(jid)
            elif self.anfitrion is None:
                self.anfitrion = jid
            self._tocar()
            return jid, token

    def agregar_bots(self, token):
        """El anfitrion completa la sala con jugadores automaticos (roles libres)."""
        with self.lock:
            jid = self._jid(token)
            if jid != self.anfitrion:
                raise ErrorSala("permiso", "Solo el anfitrión puede añadir jugadores automáticos.")
            libres = [r for r in ROLES if r not in {j.rol for j in self.partida.jugadores.values()}]
            for rol in libres[:MAX_JUGADORES - len(self.partida.jugadores)]:
                self.unir("%s (bot)" % NOMBRE_ROL[rol], rol, bot=True)

    def listo(self, token, valor):
        with self.lock:
            jid = self._jid(token)
            (self.listos.add if valor else self.listos.discard)(jid)
            self._tocar()

    def empezar(self, token):
        with self.lock:
            jid = self._jid(token)
            if jid != self.anfitrion:
                raise ErrorSala("permiso", "Solo el anfitrión puede empezar.")
            if not self.partida.puede_empezar():
                raise ErrorSala("jugadores", "Se necesitan de %d a %d jugadores." % (MIN_JUGADORES, MAX_JUGADORES))
            faltan = set(self.partida.jugadores) - self.listos - {self.anfitrion}
            if faltan:
                raise ErrorSala("listos", "Faltan jugadores por marcar «Listo».")
            self._abrir_ronda()

    # ---------- ronda ----------
    def _abrir_ronda(self):
        self.partida.nueva_ronda()
        ahora = self.reloj()
        self.limite = ahora + self.partida.tiempo_ronda()
        self.restante_pausa = self.siguiente_en = None
        for jid, datos in self.bots.items():
            datos[1] = ahora + datos[0].uniform(2.0, min(8.0, self.partida.tiempo_ronda() - 2))
        self._tocar()

    def accion(self, token, ronda, ruta, mid=None):
        with self.lock:
            self.tick()
            jid = self._jid(token)
            if self._repetido(jid, mid):
                return
            if self.partida.fase != "ronda" or ronda != self.partida.ronda:
                raise ErrorSala("ronda", "Esa acción es de otra ronda.")
            if self.restante_pausa is not None:
                raise ErrorSala("pausa", "La partida está en pausa.")
            if not isinstance(ruta, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ruta):
                raise ErrorSala("ruta", "Ruta inválida.")
            error = self.partida.registrar_accion(jid, ruta)
            if error:
                raise ErrorSala("regla", error)
            self._tocar()
            if self.partida.todos_decidieron():
                self._cerrar_ronda()

    def pausa(self, token, pausar):
        with self.lock:
            jid = self._jid(token)
            if jid != self.anfitrion:
                raise ErrorSala("permiso", "Solo el anfitrión puede pausar.")
            if self.partida.fase == "duelo":
                raise ErrorSala("fase", "El duelo no se puede pausar: la canción suena a la vez para todos.")
            if self.partida.fase != "ronda":
                raise ErrorSala("fase", "Solo se puede pausar durante una ronda.")
            ahora = self.reloj()
            if pausar and self.restante_pausa is None:
                self.restante_pausa = max(0.0, self.limite - ahora)
            elif not pausar and self.restante_pausa is not None:
                self.limite = ahora + self.restante_pausa
                self.restante_pausa = None
            self._tocar()

    def continuar(self, token):
        with self.lock:
            jid = self._jid(token)
            if jid != self.anfitrion:
                raise ErrorSala("permiso", "Solo el anfitrión puede continuar.")
            if self.partida.fase in ("resultado", "duelo_resultado"):
                self.siguiente_en = self.reloj()
                self.tick()

    def _cerrar_ronda(self):
        self.partida.resolver_ronda()
        self.limite = None
        self.siguiente_en = self.reloj() + PAUSA_RESULTADO_S
        self._tocar()

    def tick(self):
        """Avanza el reloj de la sala: presencia, bots, fin de ronda por tiempo y paso de ronda."""
        with self.lock:
            ahora = self.reloj()
            p = self.partida
            for jid, j in p.jugadores.items():
                if jid not in self.bots:
                    conectado = ahora - self.visto.get(jid, ahora) <= PRESENCIA_S
                    if j.conectado != conectado:
                        j.conectado = conectado
                        self._tocar()
            if p.fase == "ronda" and self.restante_pausa is None:
                for jid, (rng, cuando) in self.bots.items():
                    if jid not in p.acciones and cuando is not None and ahora >= cuando:
                        p.registrar_accion(jid, elegir_ruta(p.arbol_de(jid), "responsable", rng))
                        self._tocar()
                if (self.limite is not None and ahora >= self.limite) or p.todos_decidieron():
                    self._cerrar_ronda()
            elif p.fase == "resultado" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                if self.duelo and not self.duelo_hecho and p.ronda == p.total_rondas - 1:
                    self._abrir_duelo()
                elif p.cerrar_resultado() is None:
                    self._abrir_ronda()
                else:
                    self._tocar()
            elif p.fase == "duelo":
                humanos = [jid for jid, j in p.jugadores.items() if jid not in self.bots and j.conectado]
                if ahora >= self.duelo_fin or (ahora >= self.duelo_inicio and all(h in self.duelo_res for h in humanos)):
                    self._cerrar_duelo()
            elif p.fase == "duelo_resultado" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                self._abrir_ronda()
            if p.fase == "final" and self.duelo and not self.torneo_final:
                self._final_torneo()

    # ---------- Duelo de Frecuencias (final) ----------
    def _abrir_duelo(self):
        ahora = self.reloj()
        self.partida.fase = "duelo"
        self.duelo_inicio = ahora + DO.PREPARACION_S
        self.duelo_fin = self.duelo_inicio + self.chart["duration_ms"] / 1000.0 + DO.MARGEN_FIN_S
        self.duelo_res, self.duelo_prog = {}, {}
        self.limite = self.siguiente_en = None
        self._tocar()

    def entregar_duelo(self, token, datos, mid=None):
        with self.lock:
            self.tick()
            jid = self._jid(token)
            if self._repetido(jid, mid):
                return self.duelo_res.get(jid)
            if self.partida.fase != "duelo":
                raise ErrorSala("fase", "No hay ningún duelo en curso.")
            if jid in self.duelo_res:
                raise ErrorSala("regla", "Ya entregaste tu duelo.")
            transcurrido = (self.reloj() - self.duelo_inicio) * 1000.0
            try:
                res = DO.validar_y_puntuar(self.chart, datos, transcurrido)
            except ResultadoInvalido as e:
                raise ErrorSala("regla", str(e))
            self.duelo_res[jid] = res
            self._tocar()
            self.tick()
            return res

    def progreso_duelo(self, token, juzgadas, puntos, combo, precision):
        with self.lock:
            jid = self._jid(token)
            if self.partida.fase != "duelo":
                return
            total = len(self.chart["notes"])
            self.duelo_prog[jid] = {"juzgadas": max(0, min(total, int(juzgadas))), "puntos": max(0, min(MAX_PRUEBA, int(puntos))),
                                    "combo": max(0, min(total, int(combo))), "precision": max(0.0, min(1.0, float(precision)))}

    def _cerrar_duelo(self):
        p = self.partida
        for jid in p.jugadores:
            if jid not in self.duelo_res:
                if jid in self.bots:
                    datos = DO.payload_bot(self.chart, 0.75, DO.bot_rng(p.semilla, jid))
                    self.duelo_res[jid] = DO.validar_y_puntuar(self.chart, datos, 10 ** 9)
                else:
                    self.duelo_res[jid] = no_entregado()
        normalizados = [self.duelo_res[jid]["normalizado"] for jid in p.jugadores]
        media, delta = consecuencias("ritmo", normalizados)
        for k, v in delta.items():
            p.indicadores[k] = max(0, min(100, p.indicadores[k] + v))
        ganador = max(p.jugadores, key=lambda j: (self.duelo_res[j]["normalizado"], -int(j[1:])))
        self.duelo_hecho = True   # antes de la clasificacion: ya incluye los puntos del duelo
        self.duelo_resumen = {"ganador": ganador, "ganador_nombre": p.jugadores[ganador].nombre, "media": round(media * 100),
                              "delta_ciudad": delta, "resultados": dict(self.duelo_res), "clasificacion": self.clasificacion()}
        p.fase = "duelo_resultado"
        self.siguiente_en = self.reloj() + PAUSA_DUELO_S
        self._tocar()

    def clasificacion(self):
        p = self.partida
        filas = []
        for jid, j in p.jugadores.items():
            consejo = puntos_consejo(j.puntos, p.total_rondas)
            duelo = self.duelo_res.get(jid, {}).get("normalizado", 0) if self.duelo_hecho else 0
            filas.append({"id": jid, "nombre": j.nombre, "rol": j.rol, "consejo": consejo, "duelo": duelo,
                          "total": consejo + duelo})
        filas.sort(key=lambda f: (-f["total"], -f["duelo"], f["id"]))
        for i, f in enumerate(filas):
            f["posicion"] = i + 1
        return filas

    def _final_torneo(self):
        p = self.partida
        tabla = self.clasificacion()
        if self.duelo_resumen and self.duelo_resumen["delta_ciudad"]:
            from clases.arena.reglas import NOMBRE_INDICADOR
            p.eleccion["explicacion"].append("Duelo de Frecuencias: la media del grupo fue %d/100, así que %s." % (
                self.duelo_resumen["media"], ", ".join("%s %+d" % (NOMBRE_INDICADOR[k].lower(), v)
                                                      for k, v in self.duelo_resumen["delta_ciudad"].items())))
        p.eleccion["torneo"] = {"campeon": tabla[0]["id"], "campeon_nombre": tabla[0]["nombre"], "clasificacion": tabla,
                                "duelo_ganador": self.duelo_resumen["ganador_nombre"] if self.duelo_resumen else None,
                                "mensaje": mensaje_final(tabla[0], p.eleccion["ciudad"])}
        self.torneo_final = True
        self._tocar()

    # ---------- vista para un jugador ----------
    def vista(self, token, con_grafo=False):
        with self.lock:
            self.tick()
            jid = self._jid(token)
            p = self.partida
            datos = p.estado_publico()
            restante = None
            if self.restante_pausa is not None:
                restante = self.restante_pausa
            elif p.fase == "ronda" and self.limite is not None:
                restante = max(0.0, self.limite - self.reloj())
            datos.update(codigo=self.codigo, yo=jid, anfitrion=self.anfitrion, listos=sorted(self.listos),
                         pausado=self.restante_pausa is not None, restante=None if restante is None else round(restante, 1),
                         version=self.version, bots=sorted(self.bots))
            if p.fase == "ronda":
                datos["ronda_info"] = p.vista_ronda_publica()
                datos["arbol"] = p.arbol_de(jid)
                datos["ya_decidiste"] = jid in p.acciones
            if p.fase in ("resultado", "final") and p.ultimo_resultado:
                datos["resultado"] = p.ultimo_resultado
            if p.fase == "final":
                datos["final"] = p.eleccion
            if self.duelo:
                datos["duelo_modo"] = self.modo_duelo
                datos["duelo_ronda"] = p.total_rondas   # el duelo abre la ultima ronda
            if p.fase == "duelo":
                ahora = self.reloj()
                datos["duelo"] = {"modo": self.modo_duelo, "inicio_en_ms": round((self.duelo_inicio - ahora) * 1000),
                                  "fin_en_ms": round((self.duelo_fin - ahora) * 1000), "ya_entregaste": jid in self.duelo_res,
                                  "mi_resultado": self.duelo_res.get(jid),
                                  "entregaron": sorted(self.duelo_res), "progreso": self.duelo_prog}
            if p.fase in ("duelo_resultado", "final") and self.duelo_resumen:
                datos["duelo_resumen"] = self.duelo_resumen
            if self.duelo:
                datos["clasificacion"] = self.clasificacion()
            if con_grafo:
                datos["grafo"] = p.grafo_publico()
            return datos
