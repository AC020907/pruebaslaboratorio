## Central de Emergencias: estrategia en tiempo real y rutas (motor en clases/CentralEmergencias.py).
## Sustituye a Caza-Rumores en el mismo lugar de la historia (clave de resultado "contencion").
## Raton: toca una ambulancia, luego una emergencia o un hospital, y elige la ruta en el panel.
## Esc o P: pausa. La simulacion avanza a paso fijo (30 ticks/s): no depende de los FPS.

init python:
    import math as _ce_math
    import pygame
    from clases import CentralEmergencias as CE

    CE_MX, CE_MY = 24, 158                 # esquina del mapa en pantalla (1360 x 900)
    CE_DIR = "images/central/"
    CE_TINTA, CE_PAPEL, CE_VINO, CE_RUMOR = "#2b2440", "#fbf6ee", "#8c2f4b", "#d1495b"
    CE_TEAL, CE_AMBAR, CE_LILA, CE_FRENO = "#2f9e8f", "#e8b04b", "#c9b8d8", "#3d7ea6"
    CE_COLOR_GRAV = {"critico": CE_RUMOR, "grave": CE_AMBAR, "moderado": "#9678be"}
    CE_HOSP_OFF = {0: (34, -64), 1: (34, 26), 2: (30, -64)}          # icono del hospital respecto a su cruce
    CE_ESTADO_AMB = {"inactiva": "En camino a la ciudad", "libre": "Libre", "ruta": "En ruta",
                     "detenida": "DETENIDA: calle cortada", "recogiendo": "Atendiendo en la escena",
                     "esperando_hospital": "Paciente a bordo: elige hospital", "entregando": "Entregando en el hospital"}
    CE_ESTADO_EM = {"espera": "Sin ambulancia", "asignada": "Ambulancia en camino", "atendiendo": "Atención en la escena",
                    "traslado": "Traslado al hospital", "a_tiempo": "Llegó a tiempo", "tarde": "Llegó tarde",
                    "sin_atender": "No se llegó a tiempo"}

    def ce_caja(color, tam):
        return Transform(Solid(color), xysize=(max(1, int(tam[0])), max(1, int(tam[1]))))

    def ce_t(ticks):
        s = max(0, int(ticks) // CE.TICKS_S)
        return "%d:%02d" % (s // 60, s % 60)

    class VistaCentral(renpy.Displayable):
        def __init__(self, escenario, tutorial=True, reinicio=True, titulo="CENTRAL DE EMERGENCIAS", **kw):
            super(VistaCentral, self).__init__(**kw)
            self.escenario, self.tutorial, self.reinicio, self.titulo = escenario, tutorial, reinicio, titulo
            self.textos, self.rot = {}, {}
            self.mapa = CE_DIR + "mapa.png"
            auto = getattr(store, "qa_central_auto", None)
            self.piloto_h = auto
            self.reiniciar(inicial=True)

        # ---------- estado de la vista ----------
        def reiniciar(self, inicial=False):
            self.p = CE.Central(self.escenario)
            self.piloto = CE.Despachador(__import__("random").Random(11), self.piloto_h) if self.piloto_h is not None else None
            self.sel = None                # ambulancia seleccionada (indice)
            self.destino = None            # ("em", id) | ("hosp", h) | ("desvio", k): para que son las opciones
            self.opciones = []
            self.despejar = False
            self.pausa = False
            self.cuenta = 2.0
            self.acum, self.ultimo, self.st = 0.0, None, 0.0
            self.st0, self.frames = None, 0
            self.vistos = 0
            self.avisos = []               # (texto, color, st)
            self.banner = None             # (titulo, subtitulo, st)
            self.fin_st = None
            self.refresco = 0.0
            self.recalc = 0.0
            self.despacho_hecho = False
            self.entrega_hecha = False
            self.ultima_pos = {}
            self.marcas = {}               # emergencia -> instante en que se resolvio (para el desvanecido)
            if not inicial:
                renpy.restart_interaction()

        def fps(self):
            return round(self.frames / max(0.001, self.st - self.st0), 1) if self.st0 is not None else 0.0

        def texto(self, s, size=22, color=CE_TINTA, bold=True, fina=False):
            k = (s, size, color, bold, fina)
            if k not in self.textos:
                if len(self.textos) > 400:
                    self.textos.clear()
                kw = {"font": "fonts/Roboto-Light.ttf"} if fina else {}
                self.textos[k] = Text(s, size=size, color=color, bold=bold, **kw)
            return self.textos[k]

        def girado(self, img, ang):
            a = int(round(ang / 5.0)) * 5 % 360
            k = (img, a)
            if k not in self.rot:
                self.rot[k] = Transform(CE_DIR + img + ".png", rotate=a, rotate_pad=False, anchor=(0.5, 0.5),
                                        transform_anchor=True)
            return self.rot[k]

        def pausar(self):
            if self.p.jugando():
                self.pausa = True
                renpy.restart_interaction()

        def reanudar(self):
            self.pausa = False
            self.ultimo = None
            renpy.restart_interaction()

        def abandonar(self):
            self.pausa = False
            self.p._terminar()
            renpy.restart_interaction()

        def resultado_listo(self):
            return not self.p.jugando() and self.fin_st is not None and self.st - self.fin_st > 1.2

        # ---------- ordenes desde la interfaz ----------
        def amb(self, k):
            return self.p.ambulancias[k]

        def seleccionar(self, k):
            a = self.amb(k)
            if not a.activa:
                return
            self.sel = None if self.sel == k else k
            self.destino, self.opciones, self.despejar = None, [], False
            if self.sel is not None and a.estado == "esperando_hospital":
                pass
            renpy.restart_interaction()

        def elegir_emergencia(self, em_id):
            e = self.p.emergencia(em_id)
            if e is None or e.estado != "espera":
                return
            if self.sel is None or self.amb(self.sel).estado != "libre":
                # Sin ambulancia elegida: se elige la libre mas cercana (el jugador confirma la ruta igualmente).
                libres = [a for a in self.p.ambulancias if a.activa and a.estado == "libre"]
                mejor = None
                for a in libres:
                    op = self.p.opciones(self.p.origen_de(a), e.nodo)
                    if op and (mejor is None or op[0][0] < mejor[1]):
                        mejor = (a.k, op[0][0])
                if mejor is None:
                    self.aviso("No hay ambulancias libres: espera a que una termine." if not libres else
                               "Zona aislada: no hay calle abierta hasta allí. Despeja una calle.", CE_RUMOR)
                    return
                self.sel = mejor[0]
            a = self.amb(self.sel)
            self.destino = ("em", em_id)
            self.opciones = self.p.opciones(self.p.origen_de(a), e.nodo, self.p.tick < a.prioridad_hasta)
            if not self.opciones:
                self.aviso("Zona aislada: no hay calle abierta hasta allí. Despeja una calle.", CE_RUMOR)
                self.destino = None
            renpy.restart_interaction()

        def elegir_hospital(self, h):
            if self.sel is None:
                return
            a = self.amb(self.sel)
            if a.estado != "esperando_hospital":
                return
            if self.p.camas[h] <= 0:
                self.aviso("%s no tiene camas libres." % CE.HOSPITALES[h][0], CE_RUMOR)
                return
            self.destino = ("hosp", h)
            self.opciones = self.p.opciones(self.p.origen_de(a), CE.HOSPITALES[h][1], self.p.tick < a.prioridad_hasta)
            if not self.opciones:
                self.aviso("No hay calle abierta hasta %s." % CE.HOSPITALES[h][0], CE_RUMOR)
                self.destino = None
            renpy.restart_interaction()

        def pedir_desvio(self, k):
            a = self.amb(k)
            if a.objetivo is None or a.estado not in ("ruta", "detenida"):
                return
            self.sel = k
            self.destino = ("desvio", k)
            self.opciones = [o for o in self.p.opciones(self.p.origen_de(a), self.p._destino(a), self.p.tick < a.prioridad_hasta)
                             if o[1][1:] != a.ruta]
            if not self.opciones:
                self.aviso("No hay otra ruta abierta: despeja una calle o espera a que la abran.", CE_RUMOR)
                self.destino = None
            renpy.restart_interaction()

        def confirmar(self, i):
            if self.destino is None or self.sel is None:
                return
            tipo, x = self.destino
            if tipo == "desvio":
                # El motor numera las opciones sin filtrar: se busca la que el jugador ve.
                todas = self.p.opciones(self.p.origen_de(self.amb(x)), self.p._destino(self.amb(x)),
                                        self.p.tick < self.amb(x).prioridad_hasta)
                ruta = self.opciones[i][1]
                idx = next((j for j, o in enumerate(todas) if o[1] == ruta), None)
                if idx is not None:
                    self.p.ordenar("desviar", x, idx)
            elif tipo == "em":
                self.p.ordenar("despachar", self.sel, x, i)
                self.despacho_hecho = True
            else:
                self.p.ordenar("hospital", self.sel, x, i)
            self.destino, self.opciones = None, []
            renpy.restart_interaction()

        def cancelar(self):
            self.destino, self.opciones, self.despejar = None, [], False
            renpy.restart_interaction()

        def alternar_despejar(self):
            if self.p.recursos["despejar"] <= 0:
                self.aviso("Ya no quedan mediaciones disponibles.", CE_RUMOR)
                return
            self.despejar = not self.despejar
            self.destino, self.opciones = None, []
            renpy.restart_interaction()

        def usar_prioridad(self):
            if self.sel is None:
                self.aviso("Primero elige una ambulancia.", CE_AMBAR)
                return
            self.p.ordenar("prioridad", self.sel)
            renpy.restart_interaction()

        def aviso(self, texto, color):
            self.avisos.append((texto, color, self.st))
            self.avisos = self.avisos[-3:]
            renpy.restart_interaction()

        # ---------- consultas para la interfaz ----------
        def pos_amb(self, a):
            if a.arista >= 0:
                xa, ya, _b = CE.NODOS[a.nodo]
                xb, yb, _b = CE.NODOS[a.hacia]
                k = min(1.0, (a.prog + self.acum * CE.TICKS_S) / float(max(1, a.dur)))
                ang = _ce_math.degrees(_ce_math.atan2(yb - ya, xb - xa))
                self.ultima_pos[a.k] = ang
                return xa + (xb - xa) * k, ya + (yb - ya) * k, ang
            x, y, _b = CE.NODOS[a.nodo]
            return x, y, self.ultima_pos.get(a.k, 0)

        def emergencias_visibles(self):
            return [e for e in self.p.emergencias if e.estado in ("espera", "asignada", "atendiendo", "traslado")
                    or self.st - self.marcas.get(e.id, self.st) < 3.0]

        def segundos_hasta(self, tipo, arista):
            for ev in self.p.pendientes:
                if ev["tipo"] == tipo and ev.get("arista") == arista:
                    return (ev["t"] - self.p.tick) // CE.TICKS_S + 1
            return None

        def paso_tutorial(self):
            if not self.tutorial or self.p.fase != 1:
                return None
            p = self.p
            a0 = p.ambulancias[0]
            if a0.estado == "detenida":
                return ("La calle está cortada. Pulsa DESVIAR en la tarjeta de la ambulancia.", None)
            if a0.estado == "esperando_hospital":
                return ("Paciente a bordo. Elige hospital: mira el tiempo y las CAMAS libres.", ("hosp", None))
            if not self.despacho_hecho:
                if self.destino is not None:
                    return ("Elige la ruta. A es la más rápida ahora; B evita la protesta anunciada (megáfono).", ("panel", None))
                if self.sel is None:
                    return ("Toca la AMBULANCIA 12, en la Base junto a la Alcaldía.", ("amb", 0))
                if p.emergencias:
                    return ("Ahora toca la EMERGENCIA. El anillo es el tiempo que le queda al paciente.", ("em", p.emergencias[0].id))
                return ("Espera la primera llamada…", None)
            if a0.estado in ("ruta", "recogiendo"):
                return ("En camino. Si una protesta corta la calle, la ambulancia se detiene: tendrás que desviarla.", None)
            if any(e.estado == "a_tiempo" for e in p.emergencias):
                return ("Bien hecho. Vienen más llamadas: prioriza a los críticos.", None)
            return None

        # ---------- simulacion a paso fijo ----------
        def simular(self, st):
            self.st = st
            if self.ultimo is None:
                self.ultimo = st
            dt = min(0.1, max(0.0, st - self.ultimo))
            self.ultimo = st
            if not self.p.jugando() and self.fin_st is None:
                self.fin_st = st
            if self.pausa or not self.p.jugando():
                return
            if self.cuenta > 0:
                self.cuenta -= dt
                return
            self.acum += dt
            paso = 1.0 / CE.TICKS_S
            while self.acum >= paso and self.p.jugando():
                self.acum -= paso
                if self.piloto:
                    self.piloto.ordenes(self.p)
                self.p.avanzar()
            if st - self.recalc > 0.3 and self.destino is not None:
                self.recalc = st
                tipo, x = self.destino
                if tipo == "em":
                    self.elegir_emergencia(x)
                elif tipo == "hosp":
                    self.elegir_hospital(x)
            for tick, tipo, dato in self.p.eventos[self.vistos:]:
                self.evento(tipo, dato)
            self.vistos = len(self.p.eventos)

        def evento(self, tipo, dato):
            p = self.p
            if tipo == "emergencia":
                e = p.emergencia(dato)
                renpy.sound.play("assets/audio/sfx/notificacion.wav")
                self.aviso("Llamada: paciente %s en %s." % (CE.GRAVEDAD[e.gravedad][0].lower(), CE.NODOS[e.nodo][2]),
                           CE_COLOR_GRAV[e.gravedad])
            elif tipo == "aviso":
                self.aviso("Protesta anunciada en %s: la cortarán pronto." % CE.CALLES[dato][3], CE_AMBAR)
            elif tipo == "bloqueo":
                sfx("alarma")
                self.aviso("Bloqueo: %s cerrada por una protesta." % CE.CALLES[dato][3], CE_RUMOR)
            elif tipo in ("ruta_bloqueada", "detenida"):
                renpy.sound.play("assets/audio/sfx/error.ogg")
                self.aviso("Ambulancia %d: su ruta está cortada. Desvíala." % CE.AMBULANCIAS[dato][0], CE_RUMOR)
            elif tipo in ("despacho", "hacia_hospital", "desvio", "mediacion", "prioridad"):
                renpy.sound.play("assets/audio/sfx/decision.ogg")
                if tipo == "mediacion":
                    self.despejar = False
                    self.aviso("Mediación en %s: la calle abrirá en 3 s." % CE.CALLES[dato][3], CE_TEAL)
                if tipo == "prioridad":
                    self.aviso("Ruta prioritaria: la Ambulancia %d no paga el tráfico durante 20 s." % CE.AMBULANCIAS[dato][0], CE_TEAL)
            elif tipo == "apertura":
                self.aviso("%s vuelve a estar abierta." % CE.CALLES[dato][3], CE_TEAL)
            elif tipo == "paciente_a_bordo":
                renpy.sound.play("assets/audio/sfx/ui_click.wav")
                self.sel = dato
                self.destino, self.opciones = None, []
                self.aviso("Ambulancia %d con paciente: elige hospital." % CE.AMBULANCIAS[dato][0], CE_AMBAR)
            elif tipo == "auto_hospital":
                self.aviso("La tripulación de la %d eligió el hospital más rápido con cama." % CE.AMBULANCIAS[dato][0], CE_LILA)
            elif tipo == "entregado":
                e = p.emergencia(dato)
                self.marcas[e.id] = self.st
                if e.estado == "a_tiempo":
                    renpy.sound.play("assets/audio/sfx/exito.wav")
                    self.aviso("Paciente %s entregado a tiempo en %s." % (CE.GRAVEDAD[e.gravedad][0].lower(),
                                                                          CE.HOSPITALES[e.hospital][0]), CE_TEAL)
                else:
                    self.aviso("Paciente entregado con retraso.", CE_LILA)
            elif tipo == "sin_atender":
                self.marcas[dato] = self.st
                renpy.sound.play("assets/audio/sfx/pagina.ogg")
                self.aviso("No se llegó a tiempo a un paciente.", "#8b84a8")
            elif tipo == "refuerzo":
                self.aviso("Se suma la Ambulancia %d." % CE.AMBULANCIAS[dato][0], CE_TEAL)
            elif tipo == "fase":
                f = [e for e in self.escenario["eventos"] if e["tipo"] == "fase" and e["fase"] == dato][0]
                renpy.sound.play("assets/audio/sfx/transicion.ogg")
                self.banner = (f["titulo"], f["subtitulo"], self.st)
            elif tipo == "fin":
                sfx("logro")
            if self.sel is not None and self.destino is not None and tipo in ("bloqueo", "apertura"):
                self.recalc = 0.0

        # ---------- dibujo ----------
        def render(self, width, height, st, at):
            if self.st0 is None:
                self.st0 = st
            self.frames += 1
            self.simular(st)
            p = self.p
            r = renpy.Render(1920, 1080)

            def poner(d, x, y, centrar=False):
                if isinstance(d, str):
                    d = renpy.displayable(d)
                cr = renpy.render(d, 1920, 1080, st, at)
                if centrar:
                    x, y = x - cr.width / 2.0, y - cr.height / 2.0
                r.blit(cr, (int(x), int(y)))
                return cr

            poner(self.mapa, CE_MX, CE_MY)
            mx, my = CE_MX, CE_MY

            def P(x, y):
                return int(mx + x), int(my + y)

            def seg(i):
                a, b, _t, _n = CE.CALLES[i]
                return CE.NODOS[a][:2], CE.NODOS[b][:2]

            # --- capa de lineas: trafico, avisos, bloqueos, rutas, zonas aisladas, anillos de tiempo ---
            capa = renpy.Render(1920, 1080)
            c = capa.canvas()
            for i in range(len(CE.CALLES)):
                (xa, ya), (xb, yb) = seg(i)
                if p.g.trafico[i] and not p.g.bloqueada[i]:
                    col = CE_AMBAR if p.g.trafico[i] == 1 else CE_RUMOR
                    c.line(col, P(xa, ya), P(xb, yb), 6)
                if p.g.aviso[i]:
                    largo = _ce_math.hypot(xb - xa, yb - ya)
                    ux, uy = (xb - xa) / largo, (yb - ya) / largo
                    t0 = (st * 40) % 24
                    while t0 < largo:
                        c.line(CE_AMBAR, P(xa + ux * t0, ya + uy * t0), P(xa + ux * min(largo, t0 + 12), ya + uy * min(largo, t0 + 12)), 12)
                        t0 += 24
            # Rutas en curso de las demas ambulancias (finas) y de la elegida (gruesa).
            for a in p.ambulancias:
                if not a.activa or a.objetivo is None or not a.ruta:
                    continue
                x, y, _g = self.pos_amb(a)
                pts = [P(x, y)] + [P(*CE.NODOS[v][:2]) for v in a.ruta]
                elegida = a.k == self.sel
                c.lines(CE_VINO if elegida else "#a596bd", False, pts, 8 if elegida else 4)
            # Opciones de ruta que se estan eligiendo: A (teal) y B (ambar), animadas.
            for j, op in reversed(list(enumerate(self.opciones))):
                pts = [P(*CE.NODOS[v][:2]) for v in op[1]]
                col = CE_TEAL if j == 0 else CE_AMBAR
                c.lines(CE_TINTA, False, pts, 16)
                c.lines(col, False, pts, 10)
                for k in range(len(pts) - 1):
                    (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                    u = (st * 1.2 + k * 0.3) % 1.0
                    c.circle(CE_PAPEL, (int(x0 + (x1 - x0) * u), int(y0 + (y1 - y0) * u)), 4)
            for i in range(len(CE.CALLES)):
                if p.g.bloqueada[i]:
                    (xa, ya), (xb, yb) = seg(i)
                    largo = _ce_math.hypot(xb - xa, yb - ya)
                    ux, uy = (xb - xa) / largo, (yb - ya) / largo
                    for k in range(8):
                        t0 = largo * (0.2 + 0.075 * k)
                        c.line(CE_RUMOR if k % 2 == 0 else CE_PAPEL, P(xa + ux * t0, ya + uy * t0),
                               P(xa + ux * (t0 + largo * 0.075), ya + uy * (t0 + largo * 0.075)), 14)
                    if self.despejar:
                        c.circle(CE_TEAL, P((xa + xb) / 2.0, (ya + yb) / 2.0), int(30 + 6 * _ce_math.sin(st * 8)), 4)
            for k in p.g.aislados():
                x, y, _b = CE.NODOS[k]
                c.circle(CE_RUMOR, P(x, y), int(30 + 4 * _ce_math.sin(st * 5)), 4)
            for e in self.emergencias_visibles():
                if e.estado in ("espera", "asignada"):
                    x, y, _b = CE.NODOS[e.nodo]
                    frac = max(0.0, (e.limite - p.tick) / float(max(1, e.limite - e.aparece)))
                    cx, cy = P(x, y)
                    c.circle(CE_TINTA, (cx, cy), 36, 9)
                    col = CE_TEAL if frac > 0.5 else (CE_AMBAR if frac > 0.25 else CE_RUMOR)
                    if frac > 0.01:
                        # Anillo de tiempo como polilinea (Canvas.arc no esta disponible en Ren'Py 8).
                        pasos = max(2, int(48 * frac))
                        pts = [(int(cx + 34 * _ce_math.cos(-_ce_math.pi / 2 + 2 * _ce_math.pi * frac * k / pasos)),
                                int(cy + 34 * _ce_math.sin(-_ce_math.pi / 2 + 2 * _ce_math.pi * frac * k / pasos))) for k in range(pasos + 1)]
                        c.lines(col, False, pts, 7)
            r.blit(capa, (0, 0))

            # --- trafico civil: coches que circulan mas despacio cuanto mas denso; se acumulan ante un bloqueo ---
            for i in range(len(CE.CALLES)):
                (xa, ya), (xb, yb) = seg(i)
                largo = _ce_math.hypot(xb - xa, yb - ya)
                ang = _ce_math.degrees(_ce_math.atan2(yb - ya, xb - xa))
                nx, ny = -(yb - ya) / largo, (xb - xa) / largo
                nivel = p.g.trafico[i]
                cuantos = 1 + nivel * 2
                for k in range(cuantos):
                    sentido = 1 if k % 2 == 0 else -1
                    if p.g.bloqueada[i]:
                        u = 0.12 + 0.07 * (k // 2)
                        u = u if sentido > 0 else 1 - u
                    else:
                        vel = 48.0 / (1 + nivel * 1.3) / largo
                        u = (st * vel + (i * 0.37 + k * 0.61)) % 1.0
                        u = u if sentido > 0 else 1 - u
                    x = xa + (xb - xa) * u + nx * 6 * sentido
                    y = ya + (yb - ya) * u + ny * 6 * sentido
                    poner(self.girado("auto_" + "abcdef"[(i + k) % 6], ang + (0 if sentido > 0 else 180)), mx + x, my + y, True)

            # --- hospitales con sus camas libres ---
            for h, (nombre, nodo, maximo) in enumerate(CE.HOSPITALES):
                x, y, _b = CE.NODOS[nodo]
                dx, dy = CE_HOSP_OFF[h]
                hx, hy = mx + x + dx, my + y + dy
                elegible = self.sel is not None and self.amb(self.sel).estado == "esperando_hospital"
                if elegible and p.camas[h] > 0:
                    poner(Transform(circulo(CE_TEAL, CE_TINTA, 40), alpha=0.5 + 0.3 * _ce_math.sin(st * 6)), hx, hy, True)
                poner(CE_DIR + "hospital.png", hx, hy, True)
                etiqueta = self.texto(nombre.upper(), 15, CE_TINTA)
                cr = renpy.render(etiqueta, 400, 40, st, at)
                poner(ce_caja(CE_PAPEL, (cr.width + 14, 24)), hx - (cr.width + 14) / 2.0, hy + 30)
                poner(etiqueta, hx - cr.width / 2.0, hy + 32)
                for k in range(maximo):
                    poner(circulo(CE_TEAL if k < p.camas[h] else "#d9d1e3", CE_TINTA, 7), hx - (maximo - 1) * 9 + k * 18, hy + 66, True)

            # --- bloqueos (barricada) y protestas anunciadas (megafono con cuenta atras) ---
            for i in range(len(CE.CALLES)):
                (xa, ya), (xb, yb) = seg(i)
                xm, ym = mx + (xa + xb) / 2.0, my + (ya + yb) / 2.0
                if p.g.bloqueada[i]:
                    bote = 0 if persistent.reducir_movimiento else 2 * _ce_math.sin(st * 6 + i)
                    poner(CE_DIR + "barricada.png", xm, ym + bote, True)
                    abre = self.segundos_hasta("apertura", i)
                    for t_abre, x_ in p.despejes:
                        if x_ == i:
                            abre = (t_abre - p.tick) // CE.TICKS_S + 1
                    if abre is not None:
                        poner(self.texto("abre en %d s" % abre, 15, CE_TEAL), xm - 34, ym + 22)
                elif p.g.aviso[i]:
                    s_ = self.segundos_hasta("bloqueo", i)
                    poner(Transform(CE_DIR + "aviso.png", zoom=1.0 + 0.08 * _ce_math.sin(st * 8)), xm, ym, True)
                    if s_ is not None:
                        poner(self.texto("%d s" % s_, 17, CE_VINO), xm + 22, ym - 34)

            # --- emergencias ---
            for e in self.emergencias_visibles():
                x, y, _b = CE.NODOS[e.nodo]
                ex, ey = mx + x, my + y
                cerrada = e.estado in ("a_tiempo", "tarde", "sin_atender")
                if cerrada:
                    alfa = max(0.0, 1 - (self.st - self.marcas.get(e.id, self.st)) / 3.0)
                    poner(Transform(CE_DIR + ("em_cerrada" if e.estado != "a_tiempo" else "em_" + e.gravedad) + ".png",
                                    alpha=alfa), ex, ey, True)
                    if e.estado == "a_tiempo":
                        poner(Transform(self.texto("A TIEMPO", 16, CE_TEAL), alpha=alfa), ex - 34, ey - 52)
                    continue
                if e.estado == "espera" and not persistent.reducir_movimiento:
                    u = (st * 0.9 + e.id * 0.3) % 1.0
                    poner(Transform(circulo(CE_COLOR_GRAV[e.gravedad], CE_TINTA, int(26 + 34 * u)), alpha=0.35 * (1 - u)), ex, ey, True)
                late = 1.0 + (0.06 * _ce_math.sin(st * 7) if e.estado == "espera" and not persistent.reducir_movimiento else 0)
                if e.estado in ("espera", "asignada"):
                    poner(Transform(CE_DIR + "em_" + e.gravedad + ".png", zoom=late), ex, ey, True)
                    resta = ce_t(e.limite - p.tick)
                    chip = self.texto("%s  %s" % (CE.GRAVEDAD[e.gravedad][0].upper(), resta), 15, CE_PAPEL)
                    cr = renpy.render(chip, 300, 30, st, at)
                    poner(ce_caja(CE_COLOR_GRAV[e.gravedad] if e.gravedad != "grave" else "#b07d1e", (cr.width + 14, 24)),
                          ex - (cr.width + 14) / 2.0, ey + 40)
                    poner(chip, ex - cr.width / 2.0, ey + 42)

            # --- ambulancias: sprite orientado, luces y estado ---
            for a in p.ambulancias:
                if not a.activa:
                    continue
                x, y, ang = self.pos_amb(a)
                ax, ay = mx + x, my + y
                if a.k == self.sel:
                    poner(Transform(circulo(CE_PAPEL, CE_VINO, 30), alpha=0.85), ax, ay, True)
                if a.estado in ("ruta", "detenida") or a.paciente >= 0:
                    rojo = int(st * 5) % 2 == 0
                    poner(circulo(CE_RUMOR if rojo else CE_FRENO, CE_TINTA, 9), ax + (-10 if rojo else 10), ay - 22, True)
                poner(self.girado("ambulancia", ang), ax, ay, True)
                chip = self.texto("%d" % CE.AMBULANCIAS[a.k][0], 15, CE_PAPEL)
                poner(ce_caja(CE_VINO if a.k == self.sel else CE_TINTA, (30, 22)), ax + 16, ay + 12)
                poner(chip, ax + 22 if CE.AMBULANCIAS[a.k][0] < 10 else ax + 18, ay + 13)
                if a.estado == "detenida" or a.bloqueo_avisado:
                    if int(st * 3) % 2 == 0 or persistent.reducir_movimiento:
                        poner(circulo(CE_RUMOR, CE_TINTA, 15), ax - 28, ay - 28, True)
                        poner(self.texto("!", 22, CE_PAPEL), ax - 32, ay - 42)
                if a.estado in ("recogiendo", "entregando"):
                    total = CE.RECOGER if a.estado == "recogiendo" else CE.ENTREGA
                    poner(ce_caja(CE_TINTA, (54, 10)), ax - 27, ay + 26)
                    poner(ce_caja(CE_TEAL, (max(1, int(50 * (1 - a.espera / float(total)))), 6)), ax - 25, ay + 28)
                if self.tick_prioridad(a):
                    poner(self.texto(">>", 16, CE_TEAL), ax - 40, ay + 6)

            # --- tutorial: anillos que laten sobre el siguiente paso ---
            paso = self.paso_tutorial()
            if paso and paso[1]:
                tipo, x_ = paso[1]
                obj = None
                if tipo == "amb":
                    x, y, _g = self.pos_amb(p.ambulancias[x_])
                    obj = (mx + x, my + y)
                elif tipo == "em" and p.emergencia(x_) is not None:
                    x, y, _b = CE.NODOS[p.emergencia(x_).nodo]
                    obj = (mx + x, my + y)
                if obj:
                    for k in range(2):
                        u = 0.0 if persistent.reducir_movimiento else (st * 0.8 + k * 0.5) % 1.0
                        poner(Transform(circulo(CE_TEAL, CE_TINTA, int(40 + 40 * u)), alpha=0.55 * (1 - u)), obj[0], obj[1], True)
                    etiqueta = self.texto("AQUÍ", 18, CE_PAPEL)
                    yy = obj[1] + 52 if obj[1] < my + 140 else obj[1] - 82
                    poner(ce_caja(CE_TEAL, (70, 28)), obj[0] - 35, yy)
                    poner(etiqueta, obj[0] - 22, yy + 3)

            # --- cartel de fase y avisos ---
            if self.banner and st - self.banner[2] < 3.0:
                k = min(1.0, (st - self.banner[2]) / 0.3, (3.0 - (st - self.banner[2])) / 0.3)
                poner(Transform(Solid(CE_TINTA), xysize=(760, 112), alpha=0.92 * k), mx + 300, my + 380)
                poner(Transform(Solid(CE_RUMOR), xysize=(760, 6), alpha=k), mx + 300, my + 380)
                poner(Transform(self.texto(self.banner[0].upper(), 22, CE_AMBAR), alpha=k), mx + 330, my + 396)
                poner(Transform(self.texto(self.banner[1], 40, CE_PAPEL, False, True), alpha=k), mx + 330, my + 428)
            y_aviso = my + 900 - 52
            for texto, col, t0 in reversed(self.avisos):
                if st - t0 > 5.0:
                    continue
                cr = renpy.render(self.texto(texto, 20, CE_TINTA), 1300, 40, st, at)
                poner(ce_caja(CE_TINTA, (cr.width + 40, 40)), mx + 16, y_aviso - 2)
                poner(ce_caja(CE_PAPEL, (cr.width + 36, 36)), mx + 18, y_aviso)
                poner(ce_caja(col, (8, 36)), mx + 18, y_aviso)
                poner(self.texto(texto, 20, CE_TINTA), mx + 38, y_aviso + 6)
                y_aviso -= 46
            if self.cuenta > 0:
                poner(Transform(Solid("#120d1c"), xysize=(1360, 900), alpha=0.5), mx, my)
                poner(self.texto(str(int(self.cuenta) + 1), 150, CE_PAPEL), mx + 680, my + 450, True)
            if not p.jugando() and self.fin_st is not None and not self.resultado_listo():
                poner(Transform(Solid("#120d1c"), xysize=(1360, 900), alpha=min(0.6, (st - self.fin_st))), mx, my)
                poner(self.texto("FIN DEL TURNO", 64, CE_PAPEL, False, True), mx + 680, my + 450, True)
            if st - self.refresco > 0.2:
                self.refresco = st
                renpy.restart_interaction()
            renpy.redraw(self, 0)
            return r

        def tick_prioridad(self, a):
            return self.p.tick < a.prioridad_hasta

        # ---------- raton y teclado ----------
        def event(self, ev, x, y, st):
            if not self.p.jugando() or self.pausa:
                return None
            if renpy.map_event(ev, "civ_pausa"):
                self.pausar()
                raise renpy.IgnoreEvent()
            if renpy.map_event(ev, "game_menu"):
                if self.destino is not None or self.despejar:
                    self.cancelar()
                else:
                    self.pausar()
                raise renpy.IgnoreEvent()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mxp, myp = x - CE_MX, y - CE_MY
                if not (0 <= mxp <= 1360 and 0 <= myp <= 900):
                    return None
                if self.clic_mapa(mxp, myp):
                    raise renpy.IgnoreEvent()
            return None

        def clic_mapa(self, x, y):
            p = self.p
            if self.despejar:
                mejor = None
                for i in range(len(CE.CALLES)):
                    if not p.g.bloqueada[i]:
                        continue
                    a, b, _t, _n = CE.CALLES[i]
                    xm = (CE.NODOS[a][0] + CE.NODOS[b][0]) / 2.0
                    ym = (CE.NODOS[a][1] + CE.NODOS[b][1]) / 2.0
                    d = _ce_math.hypot(xm - x, ym - y)
                    if d < 60 and (mejor is None or d < mejor[1]):
                        mejor = (i, d)
                if mejor:
                    p.ordenar("despejar", mejor[0])
                    renpy.restart_interaction()
                    return True
                self.aviso("Toca una calle cortada (barricada) para enviar una mediación.", CE_AMBAR)
                return True
            for a in p.ambulancias:
                if a.activa:
                    ax, ay, _g = self.pos_amb(a)
                    if _ce_math.hypot(ax - x, ay - y) < 34:
                        self.seleccionar(a.k)
                        return True
            for h, (_nom, nodo, _c) in enumerate(CE.HOSPITALES):
                hx, hy = CE.NODOS[nodo][0] + CE_HOSP_OFF[h][0], CE.NODOS[nodo][1] + CE_HOSP_OFF[h][1]
                if _ce_math.hypot(hx - x, hy - y) < 40 and self.sel is not None:
                    self.elegir_hospital(h)
                    return True
            for e in p.emergencias:
                if e.estado == "espera":
                    ex, ey, _b = CE.NODOS[e.nodo]
                    if _ce_math.hypot(ex - x, ey - y) < 38:
                        self.elegir_emergencia(e.id)
                        return True
            if self.destino is not None:
                self.cancelar()
                return True
            return False

        def visit(self):
            return [renpy.displayable(self.mapa)] + [renpy.displayable(CE_DIR + n + ".png") for n in
                    ("hospital", "barricada", "aviso", "ambulancia", "em_critico", "em_grave", "em_moderado", "em_cerrada")]


## ---------------- pantallas ----------------
style ce_tarjeta is default:
    background Solid("#fbf6ee")
    hover_background Solid("#efe8f5")
    padding (16, 10, 14, 10)
    xfill True
style ce_boton is default:
    background Solid("#2b2440")
    hover_background Solid("#8c2f4b")
    insensitive_background Solid("#c9b8d8")
    padding (14, 8)
    hover_sound "assets/audio/sfx/menu_hover.ogg"
style ce_boton_text is default:
    size 19
    bold True
    color "#fbf6ee"
    insensitive_color "#8b84a8"
style ce_etiqueta is default:
    size 15
    bold True
    color "#8c2f4b"
    kerning 3

screen central_intro(modo="historia"):
    modal True
    zorder 46
    add Solid("#120d1c")
    add CE_DIR + "mapa.png" pos (CE_MX, CE_MY) alpha 0.35
    frame:
        align (0.5, 0.5)
        xsize 1320
        background Frame("gui/frame.png", 30, 30)
        padding (56, 40)
        has vbox
        spacing 14
        xfill True
        text "CIUDAD NOVA · DESPACHO 123" style "civ_etiqueta" xalign 0.5
        text "Central de Emergencias" style "civ_titulo" size 64 xalign 0.5
        add Solid("#d1495b", xysize=(120, 5)) xalign 0.5
        text "El rumor ya cerró calles. Hay personas que necesitan un hospital y las ambulancias no alcanzan para todas. Decide a quién atender primero, por dónde ir y a qué hospital llevarlas." size 22 color "#2b2440" xalign 0.5 text_align 0.5
        hbox:
            xalign 0.5
            spacing 36
            for imagen, titulo, texto in (("ambulancia", "1. Ambulancia", "Tócala para elegirla."), ("em_critico", "2. Emergencia", "Tócala. El anillo es el tiempo que queda."),
                                          ("barricada", "3. Bloqueos", "Si cortan tu ruta, DESVÍA. Si aíslan un barrio, envía una mediación."),
                                          ("hospital", "4. Hospital", "Con el paciente a bordo, elige uno con camas libres.")):
                vbox:
                    xsize 270
                    spacing 6
                    add CE_DIR + imagen + ".png" xalign 0.5 zoom 1.4
                    text titulo size 21 bold True color "#2b2440" xalign 0.5
                    text texto size 17 color "#5b4f72" xalign 0.5 text_align 0.5
        text "Rutas: A es la más rápida ahora. B es una alternativa (evita las protestas anunciadas con megáfono). El tráfico denso (ámbar) y los atascos (rojo) cambian los tiempos." size 19 color "#2b2440" xalign 0.5 text_align 0.5
        text "Tres fases: primera emergencia, ciudad congestionada y crisis. Cuentan los pacientes que llegan a tiempo y lo urgentes que eran." size 19 color "#5b4f72" xalign 0.5 text_align 0.5
        textbutton "EMPEZAR EL TURNO" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True

screen central_ui(vista):
    modal True
    zorder 45
    add Solid("#120d1c")
    add vista
    $ p = vista.p
    # --- barra superior ---
    frame:
        pos (CE_MX, 24)
        xysize (1360, 110)
        background Solid("#fbf6ee")
        padding (24, 12)
        hbox:
            spacing 30
            yalign 0.5
            vbox:
                text vista.titulo style "ce_etiqueta" size 17
                $ f_ev = [e for e in vista.escenario["eventos"] if e["tipo"] == "fase" and e["fase"] == p.fase]
                text ("%s · %s" % (f_ev[0]["titulo"], f_ev[0]["subtitulo"]) if f_ev else "") font AP_FUENTE_FINA size 40 color "#2b2440"
            null width 30
            $ r_ = p.resumen()
            for etiqueta, valor, col in (("A TIEMPO", r_["a_tiempo"], "#2f9e8f"), ("EN CURSO", sum(1 for e in p.emergencias if e.estado in ("espera", "asignada", "atendiendo", "traslado")), "#2b2440"),
                                         ("SIN ATENDER", sum(1 for e in p.emergencias if e.estado == "sin_atender"), "#8b84a8"), ("TURNO", ce_t(p.fin_tick - p.tick), "#d1495b" if p.fin_tick - p.tick < 15 * CE.TICKS_S else "#2b2440")):
                vbox:
                    yalign 0.5
                    text etiqueta style "ce_etiqueta"
                    text str(valor) size 34 bold True color col
    if p.jugando() and not vista.pausa:
        textbutton "Pausa" style "civ_ficha" text_style "civ_ficha_text" xpos 1890 xanchor 1.0 ypos 40 action Function(vista.pausar)
    # --- panel de despacho ---
    frame:
        pos (1404, CE_MY)
        xysize (492, 900)
        background Solid("#2b2440")
        padding (12, 12)
        viewport:
            mousewheel True
            ysize 876
            vbox:
                spacing 8
                text "EMERGENCIAS" style "ce_etiqueta" color "#e8b04b"
                $ activas = [e for e in p.emergencias if e.estado in ("espera", "asignada", "atendiendo", "traslado")]
                if not activas:
                    text "Sin llamadas pendientes." size 18 color "#c9b8d8"
                for e in activas:
                    $ frac = max(0.0, (e.limite - p.tick) / float(max(1, e.limite - e.aparece)))
                    button:
                        style "ce_tarjeta"
                        action Function(vista.elegir_emergencia, e.id)
                        sensitive e.estado == "espera"
                        hbox:
                            spacing 12
                            add Solid(CE_COLOR_GRAV[e.gravedad], xysize=(10, 62))
                            vbox:
                                xsize 420
                                hbox:
                                    xfill True
                                    text "%s · %s" % (CE.GRAVEDAD[e.gravedad][0], CE.NODOS[e.nodo][2]) size 20 bold True color "#2b2440"
                                    text ce_t(e.limite - p.tick) size 20 bold True color ("#d1495b" if frac < 0.3 else "#2b2440") xalign 1.0
                                $ quien = (" · Amb %d" % CE.AMBULANCIAS[e.ambulancia][0]) if e.ambulancia >= 0 else ""
                                text CE_ESTADO_EM[e.estado] + quien size 16 color "#5b4f72"
                                add Solid("#e6deee", xysize=(410, 6))
                                add Solid(CE_TEAL if frac > 0.5 else (CE_AMBAR if frac > 0.25 else CE_RUMOR), xysize=(max(1, int(410 * frac)), 6)) yoffset -6
                null height 6
                text "AMBULANCIAS" style "ce_etiqueta" color "#e8b04b"
                for a in p.ambulancias:
                    button:
                        style "ce_tarjeta"
                        background Solid("#fbf6ee" if a.k != vista.sel else "#f3d9e0")
                        action Function(vista.seleccionar, a.k)
                        sensitive a.activa
                        vbox:
                            spacing 4
                            hbox:
                                xfill True
                                text "AMBULANCIA %d" % CE.AMBULANCIAS[a.k][0] size 19 bold True color ("#2b2440" if a.activa else "#8b84a8")
                                if vista.tick_prioridad(a):
                                    text "PRIORIDAD" size 15 bold True color "#2f9e8f" xalign 1.0
                            text CE_ESTADO_AMB[a.estado] size 16 bold (a.estado in ("detenida", "esperando_hospital")) color ("#d1495b" if a.estado == "detenida" else ("#8c2f4b" if a.estado == "esperando_hospital" else "#5b4f72"))
                            if a.estado in ("ruta", "detenida") and a.objetivo is not None:
                                textbutton ("DESVIAR" if (a.estado == "detenida" or a.bloqueo_avisado) else "Cambiar ruta") style "ce_boton" text_style "ce_boton_text" action Function(vista.pedir_desvio, a.k)
                            if a.estado == "esperando_hospital":
                                text "Elige hospital (si no, la tripulación irá al más rápido en %d s)" % max(0, a.espera // CE.TICKS_S) size 14 color "#5b4f72"
                                for h, coste, camas in p.eta_hospitales(a):
                                    textbutton ("%s · %s · %d cama%s" % (CE.HOSPITALES[h][0], ce_t(coste) if coste >= 0 else "sin camino", camas, "" if camas == 1 else "s")):
                                        style "ce_boton"
                                        text_style "ce_boton_text"
                                        text_size 16
                                        xfill True
                                        sensitive (camas > 0 and coste >= 0)
                                        action [Function(vista.seleccionar, a.k) if vista.sel != a.k else NullAction(), Function(vista.elegir_hospital, h)]
                null height 6
                text "RECURSOS" style "ce_etiqueta" color "#e8b04b"
                hbox:
                    spacing 8
                    textbutton ("Mediación (%d)" % p.recursos["despejar"]) style "ce_boton" text_style "ce_boton_text" action Function(vista.alternar_despejar) sensitive p.recursos["despejar"] > 0 selected vista.despejar
                    textbutton ("Ruta prioritaria (%d)" % p.recursos["prioridad"]) style "ce_boton" text_style "ce_boton_text" action Function(vista.usar_prioridad) sensitive p.recursos["prioridad"] > 0
                text "Mediación: toca una barricada y la calle abre en 3 s. Prioritaria: la ambulancia elegida no paga el tráfico 20 s." size 14 color "#c9b8d8"
    # --- caja de opciones / tutorial (sobre el mapa, abajo a la derecha) ---
    $ paso = vista.paso_tutorial()
    if vista.opciones:
        frame:
            xpos 1384 xanchor 1.0 ypos 1040 yanchor 1.0
            background Solid("#fbf6ee")
            padding (20, 16)
            vbox:
                spacing 8
                $ tipo_d = vista.destino[0] if vista.destino else ""
                text ("ELIGE LA RUTA" if tipo_d == "em" else ("RUTA AL HOSPITAL" if tipo_d == "hosp" else "DESVÍO")) style "ce_etiqueta"
                for j, op in enumerate(vista.opciones):
                    $ evita = j > 0 and any(p.g.aviso[i] for i in vista.opciones[0][2])
                    textbutton ("Ruta %s · %s%s" % ("AB"[j], ce_t(op[0]), " · más rápida" if j == 0 else (" · evita la protesta" if evita else " · alternativa"))):
                        style "ce_boton"
                        text_style "ce_boton_text"
                        background Solid(CE_TEAL if j == 0 else "#b07d1e")
                        hover_background Solid("#8c2f4b")
                        action Function(vista.confirmar, j)
                textbutton "Cancelar (Esc)" style "arena_link" action Function(vista.cancelar)
    elif paso:
        frame:
            xpos 1384 xanchor 1.0 ypos 1040 yanchor 1.0
            xmaximum 640
            background Solid("#fbf6ee")
            padding (20, 14)
            vbox:
                text "CÓMO SE JUEGA" style "ce_etiqueta"
                text paso[0] size 20 color "#2b2440"
    elif vista.despejar:
        frame:
            xpos 1384 xanchor 1.0 ypos 1040 yanchor 1.0
            background Solid("#fbf6ee")
            padding (20, 14)
            text "Toca una barricada para enviar la mediación (Esc cancela)." size 20 color "#2b2440"
    if vista.pausa:
        add Solid("#000000b8")
        frame:
            align (0.5, 0.5)
            background Frame("gui/frame.png", 30, 30)
            padding (56, 40)
            vbox:
                spacing 16
                text "Pausa" style "civ_titulo" xalign 0.5
                add Solid("#d1495b", xysize=(100, 5)) xalign 0.5
                textbutton "Continuar" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.reanudar) default_focus True
                if vista.reinicio:
                    textbutton "Reiniciar el turno" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.reiniciar)
                textbutton "Terminar el turno" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.abandonar)
        key "civ_pausa" action Function(vista.reanudar)
        key "game_menu" action Function(vista.reanudar)
    elif vista.resultado_listo():
        use central_resultado(vista.p)

screen central_resultado(p):
    zorder 100
    $ res = p.resultado()
    $ nota = res["calificacion"]
    $ exito = res["exito"]
    add Solid("#120d1cd0")
    fixed at plat_entra(0.0):
        align (0.5, 0.5)
        xysize (1240, 760)
        add Solid("#2b2440")
        frame:
            pos (10, 10)
            xysize (1220, 740)
            background Solid("#fbf6ee")
            padding (56, 40)
            vbox:
                spacing 16
                hbox:
                    spacing 34
                    fixed:
                        xysize (170, 170)
                        add circulo("#2f9e8f" if exito else "#c9b8d8", "#2b2440", 80) align (0.5, 0.5)
                        text nota size 110 bold True color "#2b2440" align (0.5, 0.52) at nota_golpe
                    vbox:
                        yalign 0.5
                        spacing 6
                        text ("TURNO CUMPLIDO" if exito else "TURNO DESBORDADO") size 50 bold True color ("#2f9e8f" if exito else "#8c2f4b")
                        text res["mensaje"] size 24 color "#2b2440"
                        text ("Objetivo: que al menos 3 de cada 5 pacientes lleguen a tiempo.") size 19 color "#5b4f72"
                hbox:
                    spacing 14
                    for i, (titulo, valor, col) in enumerate((("PUNTOS", "%d" % res["puntos"], "#2b2440"), ("A TIEMPO", "%d / %d" % (res["a_tiempo"], res["total"]), "#2f9e8f"),
                                                            ("TARDE", "%d" % res["tarde"], "#2b2440"), ("SIN ATENDER", "%d" % res["sin_atender"], "#8c2f4b" if res["sin_atender"] else "#2b2440"),
                                                            ("RESPUESTA", "%d s" % res["respuesta_media_s"], "#2b2440"))):
                        frame at plat_entra(0.2 + i * 0.07):
                            background Solid("#efe8f5")
                            xsize 208
                            padding (18, 12)
                            vbox:
                                text titulo size 14 bold True color "#8b84a8" kerning 3
                                text valor size 36 bold True color col
                text "PACIENTES" size 15 bold True color "#8c2f4b" kerning 3
                hbox:
                    spacing 10
                    box_wrap True
                    xmaximum 1110
                    for k, e in enumerate(p.emergencias):
                        frame at plat_entra(0.5 + k * 0.06):
                            background Solid("#ffffff")
                            xsize 268
                            padding (12, 8)
                            hbox:
                                spacing 8
                                add Solid(CE_COLOR_GRAV[e.gravedad], xysize=(8, 44))
                                vbox:
                                    text "%s · %s" % (CE.GRAVEDAD[e.gravedad][0], CE.NODOS[e.nodo][2]) size 16 bold True color "#2b2440"
                                    text CE_ESTADO_EM[e.estado] size 15 color ("#2f9e8f" if e.estado == "a_tiempo" else "#5b4f72")
                text "Desvíos: %d · Recursos usados: %d (cada uno resta 15 puntos) · Puntúan los pacientes a tiempo, su gravedad y el margen con que llegaron." % (res["desvios"], res["recursos"]) size 17 color "#5b4f72"
                textbutton "CONTINUAR" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True

## Minijuego reutilizable: Historia, Feria y Arena.
label minijuego_central(modo="historia", semilla=None, aplicar=True, tutorial=True, reinicio=True, escenario=None):
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    $ quick_menu_previo = quick_menu
    $ quick_menu = False
    window hide
    $ renpy.block_rollback()
    $ semilla_central = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ escenario_central = escenario or CE.generar_escenario(modo, semilla_central)
    if tutorial:
        call screen central_intro(modo)
    $ vista_central = VistaCentral(escenario_central, tutorial=tutorial, reinicio=reinicio)
    call screen central_ui(vista_central)
    $ central = vista_central.p
    $ quick_menu = quick_menu_previo
    if hud_estaba_visible:
        show screen hud_ciudad
    $ renpy.block_rollback()
    $ resultado_minijuego = registrar_minijuego(central.resultado(), aplicar)
    return resultado_minijuego
