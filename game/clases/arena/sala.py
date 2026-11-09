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

PRESENCIA_S = 20.0
PAUSA_RESULTADO_S = 10.0


class ErrorSala(Exception):
    def __init__(self, codigo, mensaje):
        super(ErrorSala, self).__init__(mensaje)
        self.codigo, self.mensaje = codigo, mensaje


class SalaArena(object):
    def __init__(self, codigo, semilla=None, rondas=5, segundos=25, reloj=time.monotonic):
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
            if self.partida.fase == "resultado":
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
                if p.cerrar_resultado() is None:
                    self._abrir_ronda()
                else:
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
            if con_grafo:
                datos["grafo"] = p.grafo_publico()
            return datos
