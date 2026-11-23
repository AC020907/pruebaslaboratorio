## Cinematica de apertura «Un año antes» (dramatizacion de ficcion, ~39 s), antes del prologo interactivo.
## Noticiero -> ambulancia atrapada en un bloqueo -> paciente critico -> monitor: ultimo latido y linea plana ->
## noticia del fallecimiento -> titulo. Guia: docs/CINEMATICA_APERTURA.md.
##
## Una sola linea de tiempo determinista (clases/cinematica_tiempos.py) gobierna imagen, pitidos y voces.
## El reloj de la imagen es la posicion real del audio (canal "cine"): el pico R y su pitido caen en el mismo
## cuadro. No toca ninguna variable de la partida: solo dibuja y suena.

init -2 python:
    renpy.music.register_channel("cine", mixer="sfx", loop=False, stop_on_mute=False, tight=True)
    renpy.music.register_channel("cine_voz", mixer="voice", loop=False, stop_on_mute=False, tight=True)

init -1 python:
    import math as _cine_math
    from clases import cinematica_tiempos as CT

    CINE_FX = "assets/audio/cine/apertura_fx.ogg"
    CINE_VOCES = "assets/audio/cine/apertura_voces.ogg"
    CINE_IMG = "images/cinematica/"
    CINE_PANTALLA = (120, 110)          # esquina de la pantalla dentro de monitor_marco.png
    CINE_MON_W, CINE_MON_H = 1680, 790

    def cine_audio_iniciar():
        renpy.music.play(CINE_FX, channel="cine", loop=False, synchro_start=True)
        renpy.music.play(CINE_VOCES, channel="cine_voz", loop=False, synchro_start=True)

    def cine_audio_detener(fadeout=0.25):
        renpy.music.stop(channel="cine", fadeout=fadeout)
        renpy.music.stop(channel="cine_voz", fadeout=fadeout)

    def cine_suave(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)

    def cine_interp(claves, t):
        """Camara por claves [(t, a, b, ...)]: entre claves, interpolacion suavizada."""
        if t <= claves[0][0]:
            return claves[0][1:]
        for a, b in zip(claves, claves[1:]):
            if t <= b[0]:
                k = cine_suave((t - a[0]) / max(0.001, b[0] - a[0]))
                return tuple(a[i] + (b[i] - a[i]) * k for i in range(1, len(a)))
        return claves[-1][1:]

    class CineReloj(object):
        """Tiempo de la cinematica. Sigue la posicion del canal de audio; sin audio (o al terminar), el reloj de pantalla."""
        def __init__(self):
            self.desfase = None
            self.ultimo = 0.0

        def __call__(self, st):
            pos = renpy.music.get_pos(channel="cine")
            if pos is not None and pos > 0.05:
                d = st - pos
                if self.desfase is None or abs(d - self.desfase) > 0.04:
                    self.desfase = d
            t = st - (self.desfase or 0.0)
            self.ultimo = max(self.ultimo, t)
            return self.ultimo

    class MonitorVital(renpy.Displayable):
        """Pantalla del monitor de signos vitales, dibujada en cada cuadro a partir de CT (no es una imagen en bucle).

        La senal se desplaza de derecha a izquierda: lo mas reciente entra por la derecha (CT.VENTANA segundos
        visibles). Despues de CT.PLANA la senal es 0 y la linea plana empuja fuera al ultimo latido; durante
        CT.CONGELADO la imagen se detiene.
        """
        TRAZO_X0, TRAZO_X1 = 24, 1160
        ECG_Y, ECG_A = 270, 150
        PLETH_Y, PLETH_A = 590, 95

        def __init__(self, **kw):
            super(MonitorVital, self).__init__(**kw)
            self.t = 0.0
            self.cache = {}

        def txt(self, s, size, color, font=None, bold=False, kerning=0):
            clave = (s, size, color, font, bold, kerning)
            if clave not in self.cache:
                kw = {"font": font} if font else {}
                self.cache[clave] = Text(s, size=size, color=color, bold=bold, kerning=kerning, **kw)
            return self.cache[clave]

        def trazo(self, c, f, y0, amp, color, td, paso):
            ancho = self.TRAZO_X1 - self.TRAZO_X0
            v = ancho / CT.VENTANA
            puntos = [(self.TRAZO_X0 + k, int(y0 - f(td - (ancho - k) / v) * amp)) for k in range(0, ancho + 1, paso)]
            c.lines(color, False, puntos, 4)
            c.circle(color, (self.TRAZO_X1, puntos[-1][1]), 8)

        def render(self, width, height, st, at):
            W, H = CINE_MON_W, CINE_MON_H
            t = self.t
            td = min(t, CT.CONGELADO[0])
            plana = t >= CT.PLANA
            r = renpy.Render(W, H)
            r.blit(renpy.render(Solid("#0a1116"), W, H, st, at), (0, 0))
            c = r.canvas()
            for x in range(self.TRAZO_X0, self.TRAZO_X1 + 1, 38):
                c.line("#122830", (x, 80), (x, 700), 1)
            for y in range(80, 701, 38):
                c.line("#122830", (self.TRAZO_X0, y), (self.TRAZO_X1, y), 1)
            c.rect("#15232c", (0, 0, W, 64))
            c.line("#1f3a45", (1190, 80), (1190, H - 20), 2)
            c.line("#1f3a45", (1200, 360), (W - 20, 360), 2)
            c.line("#1f3a45", (1200, 560), (W - 20, 560), 2)
            self.trazo(c, CT.ecg, self.ECG_Y, self.ECG_A, "#5fe3cf", td, 2)
            self.trazo(c, CT.pletismografia, self.PLETH_Y, self.PLETH_A, "#e8b04b", td, 4)
            fc, spo2, pas, pad = CT.vitales(t)
            latido = any(0 <= td - rr < 0.14 for rr, _a in CT.LATIDOS)
            if latido and not plana:
                c.circle("#5fe3cf", (1630, 132), 13)
            # Cabecera: cama, diagnostico (ficcion), hora.
            r.blit(renpy.render(self.txt("AMB 12  ·  TRASLADO", 24, "#8fb3bd", bold=True, kerning=2), W, H, st, at), (24, 18))
            diag = renpy.render(self.txt(CT.DIAGNOSTICO, 30, "#fbf6ee", bold=True), W, H, st, at)
            r.blit(diag, (int(W / 2 - diag.width / 2) - 40, 14))
            r.blit(renpy.render(self.txt("21:58", 24, "#8fb3bd"), W, H, st, at), (W - 96, 18))
            r.blit(renpy.render(self.txt("II", 26, "#5fe3cf", bold=True), W, H, st, at), (34, 88))
            r.blit(renpy.render(self.txt("PLETH", 22, "#e8b04b", bold=True), W, H, st, at), (34, 486))
            # Panel derecho.
            rojo = "#ff5a6e"
            r.blit(renpy.render(self.txt("FC  lpm", 26, "#5fe3cf", bold=True), W, H, st, at), (1220, 92))
            r.blit(renpy.render(self.txt("--" if plana else "%d" % fc, 150, rojo if (plana or fc < 60) else "#5fe3cf",
                                         font=AP_FUENTE_FINA), W, H, st, at), (1240, 140))
            r.blit(renpy.render(self.txt("SpO2  %", 26, "#e8b04b", bold=True), W, H, st, at), (1220, 376))
            r.blit(renpy.render(self.txt("--" if plana else "%d" % spo2, 110, "#e8b04b", font=AP_FUENTE_FINA), W, H, st, at), (1240, 412))
            r.blit(renpy.render(self.txt("PA  mmHg", 26, "#c9b8d8", bold=True), W, H, st, at), (1220, 576))
            r.blit(renpy.render(self.txt("--/--" if plana else "%d/%d" % (pas, pad), 74, "#c9b8d8", font=AP_FUENTE_FINA), W, H, st, at), (1240, 616))
            # Aviso: frecuencia baja y, al final, alarma (parpadea mientras suena el tono; congelada despues).
            aviso = None
            if plana:
                if t >= CT.CONGELADO[0] or int(td * 2.5) % 2 == 0:
                    aviso = ("ALARMA", rojo)
            elif fc < 60:
                aviso = ("FC BAJA", "#e8b04b")
            if aviso:
                txt = renpy.render(self.txt(aviso[0], 40, "#0a1116", bold=True, kerning=6), W, H, st, at)
                caja = renpy.render(Solid(aviso[1]), txt.width + 56, 60, st, at)
                r.blit(caja, (self.TRAZO_X1 - caja.width - 20, 84))
                r.blit(txt, (self.TRAZO_X1 - caja.width + 8, 92))
            r.blit(renpy.render(self.txt("DRAMATIZACIÓN", 18, "#4b6670", kerning=4), W, H, st, at), (24, H - 34))
            if t < CT.CONGELADO[0]:
                renpy.redraw(self, 0)
            return r

    class CinematicaApertura(renpy.Displayable):
        """Los seis planos de la apertura, dibujados en cada cuadro a partir del tiempo de la linea CT."""

        AUTOS = (("auto_gris", 120, 0.0), ("ambulancia", 620, 1.3), ("auto_vino", 1420, 2.1), ("taxi", 1890, 0.7),
                 ("bus", 2360, 1.7), ("auto_azul", 3380, 2.6))
        AMB_X = 620
        BARRICADA_X = 3920
        GENTE = ((4060, 0, 0.86), (4420, 2, 0.9), (4700, 4, 0.84), (3840, 1, 0.92), (4240, 3, 0.8), (4560, 5, 0.95),
                 (3700, 6, 0.88), (4880, 7, 0.9))
        BLOQUEOS = ((1180, 700), (1420, 860), (1660, 640), (1900, 980), (1300, 1120), (2140, 820), (980, 980),
                    (1600, 1300), (2300, 1100), (1750, 1500), (820, 760), (2480, 760), (1440, 560), (2050, 1350))
        CALLE_Y = 1000   # suelo de los vehiculos (coordenadas de la calle)

        def __init__(self, **kw):
            super(CinematicaApertura, self).__init__(**kw)
            self.reloj = CineReloj()
            self.reducido = bool(persistent.reducir_movimiento)
            self.t = 0.0
            self.cuadros = 0
            self.cache = {}
            self.monitor = MonitorVital()
            self.titulo = TituloRed()
            self.feed = self.crear_feed()

        # ---------- utilidades ----------
        def img(self, nombre):
            return CINE_IMG + nombre + ".png"

        def txt(self, s, size, color, font=None, bold=False, kerning=0, **kw):
            clave = (s, size, color, font, bold, kerning, repr(sorted(kw.items())))
            if clave not in self.cache:
                extra = dict(kw)
                if font:
                    extra["font"] = font
                self.cache[clave] = Text(s, size=size, color=color, bold=bold, kerning=kerning, **extra)
            return self.cache[clave]

        def pon(self, r, d, x, y, ctx, zoom=1.0, alpha=1.0, xanchor=0.0, yanchor=0.0, rotar=None, aditivo=False, **kw):
            if alpha <= 0.003:
                return None
            if isinstance(d, str):
                if d not in self.cache:
                    self.cache[d] = renpy.displayable(d)
                d = self.cache[d]
            if zoom != 1.0 or alpha != 1.0 or rotar or aditivo or kw:
                props = dict(kw)
                props.update(zoom=zoom, alpha=alpha)
                if rotar:
                    props["rotate"] = rotar
                if aditivo:
                    props["additive"] = 1.0
                d = Transform(d, **props)
            w, h, st, at = ctx
            cr = renpy.render(d, w, h, st, at)
            r.blit(cr, (int(x - xanchor * cr.width), int(y - yanchor * cr.height)))
            return cr

        def velo(self, r, ctx, color, alpha):
            if alpha > 0.003:
                self.pon(r, Solid(color), 0, 0, ctx, alpha=alpha)

        def sacudida(self, t, fuerza=1.0):
            if self.reducido:
                return 0, 0
            return (int((_cine_math.sin(t * 1.7) * 5 + _cine_math.sin(t * 4.3) * 2) * fuerza),
                    int((_cine_math.sin(t * 1.3 + 1) * 4 + _cine_math.sin(t * 5.1) * 1.5) * fuerza))

        # ---------- la calle (parallax) ----------
        def calle(self, r, ctx, t, cx, cy, z, luces=True, gente=True, sirena_global=0.0, desat=False):
            w, h = ctx[0], ctx[1]
            sx, sy = self.sacudida(t, 0.6 if luces else 0.0)
            ox, oy = 960 + sx, 540 + sy
            self.pon(r, self.img("calle_cielo"), 0, 0, ctx)

            def capa(nombre, factor):
                self.pon(r, self.img(nombre), ox - cx * factor * z, oy - cy * z, ctx, zoom=z)

            capa("calle_lejos", 0.3)
            capa("calle_medio", 0.82)
            capa("calle_via", 1.0)

            def mundo(x, y):
                return ox + (x - cx) * z, oy + (y - cy) * z

            if gente:
                for gx, i, esc in self.GENTE[:3]:
                    self.persona(r, ctx, t, mundo, gx, i, esc * 0.9, z, self.CALLE_Y - 40)
            # Barricada.
            bx, by = mundo(self.BARRICADA_X, self.CALLE_Y + 8)
            self.pon(r, self.img("barricada"), bx, by, ctx, zoom=z * 0.92, yanchor=1.0)
            # Vehiculos (ralenti: vibran un pixel).
            ambulancia_xy = None
            for nombre, x, fase in self.AUTOS:
                vib = 0 if self.reducido else _cine_math.sin(t * 31 + fase * 7) * 1.2
                px, py = mundo(x, self.CALLE_Y + vib)
                cr = self.pon(r, self.img(nombre), px, py, ctx, zoom=z, yanchor=1.0)
                if cr is None:
                    continue
                if nombre == "ambulancia":
                    ambulancia_xy = (px, py, cr)
                elif luces:
                    pulso = 0.75 + 0.25 * _cine_math.sin(t * 3 + fase)
                    self.pon(r, self.img("luz_freno"), px + 8 * z, py - 82 * z * (1.9 if nombre == "bus" else 1.0),
                             ctx, zoom=z, alpha=pulso, xanchor=0.5, yanchor=0.5, aditivo=True)
            if gente:
                for gx, i, esc in self.GENTE[3:]:
                    self.persona(r, ctx, t, mundo, gx, i, esc, z, self.CALLE_Y + 46)
            # Sirena: barra de luces de la ambulancia y destellos rojo/azul sobre la escena.
            if ambulancia_xy and luces:
                px, py, cr = ambulancia_xy
                fase = (t * 2.6) % 1.0
                rojo = fase < 0.5
                lx = px + (200 if rojo else 300) * z
                ly = py - 288 * z
                self.pon(r, self.img("luz_roja" if rojo else "luz_azul"), lx, ly, ctx, zoom=z * 1.25,
                         xanchor=0.5, yanchor=0.5, aditivo=True)
                cerca = max(0.0, 1.0 - abs(px + 350 * z - 960) / 1700.0)
                self.velo(r, ctx, "#d1495b" if rojo else "#3d7ea6", (0.10 + sirena_global) * cerca)
            capa("calle_primer_plano", 1.32)
            if desat:
                self.velo(r, ctx, "#120d1c", 0.42)

        def persona(self, r, ctx, t, mundo, gx, i, esc, z, suelo):
            bote = 0 if self.reducido else abs(_cine_math.sin(t * 3.4 + i * 1.7)) * 10
            giro = 0 if self.reducido else _cine_math.sin(t * 2.2 + i) * 3
            px, py = mundo(gx, suelo - bote)
            self.pon(r, self.img("persona_%d" % i), px, py, ctx, zoom=z * esc, rotar=giro, xanchor=0.5, yanchor=1.0)

        # ---------- graficos del noticiero ----------
        def mosca(self, r, ctx, t, hora):
            self.pon(r, Solid("#fbf6ee"), 56, 48, ctx, xsize=318, ysize=58)
            self.pon(r, Solid("#8c2f4b"), 56, 48, ctx, xsize=10, ysize=58)
            self.pon(r, self.txt("NOTICIAS NOVA", 30, "#2b2440", bold=True, kerning=3), 82, 60, ctx)
            self.pon(r, Solid("#d1495b"), 386, 48, ctx, xsize=150, ysize=58)
            if int(t * 1.6) % 2 == 0:
                self.pon(r, Solid("#fbf6ee"), 404, 70, ctx, xsize=14, ysize=14)
            self.pon(r, self.txt("EN VIVO", 24, "#fbf6ee", bold=True, kerning=2), 428, 62, ctx)
            self.pon(r, self.txt(hora, 30, "#fbf6ee", font=AP_FUENTE_FINA, outlines=[(2, "#120d1c", 0, 0)]),
                     1864, 58, ctx, xanchor=1.0)

        def zocalo(self, r, ctx, t, t0, etiqueta, titular, color="#d1495b"):
            k = cine_suave((t - t0) / 0.45)
            if k <= 0:
                return
            dx = 0 if self.reducido else int((1 - k) * -700)
            self.pon(r, Solid(color), 80 + dx, 784, ctx, xsize=268, ysize=70, alpha=k)
            self.pon(r, self.txt(etiqueta, 28, "#fbf6ee", bold=True, kerning=3), 104 + dx, 803, ctx, alpha=k)
            cr = renpy.render(self.txt(titular, 36, "#2b2440", bold=True), ctx[0], ctx[1], ctx[2], ctx[3])
            self.pon(r, Solid("#fbf6ee"), 348 + dx, 784, ctx, xsize=cr.width + 64, ysize=70, alpha=k)
            self.pon(r, self.txt(titular, 36, "#2b2440", bold=True), 380 + dx, 797, ctx, alpha=k)

        def cintillo(self, r, ctx, t, texto):
            self.pon(r, Solid("#120d1c"), 0, 1024, ctx, xsize=1920, ysize=56)
            self.pon(r, Solid("#8c2f4b"), 0, 1024, ctx, xsize=250, ysize=56)
            cr = renpy.render(self.txt(texto, 26, "#c9b8d8"), ctx[0], ctx[1], ctx[2], ctx[3])
            x = 1920 - ((t * 190) % (cr.width + 1700))
            self.pon(r, self.txt(texto, 26, "#c9b8d8"), int(x), 1037, ctx)
            self.pon(r, Solid("#8c2f4b"), 0, 1024, ctx, xsize=250, ysize=56)
            self.pon(r, self.txt("CIUDAD NOVA", 24, "#fbf6ee", bold=True, kerning=3), 24, 1038, ctx)

        def subtitulo(self, r, ctx, t):
            for a, b, quien, texto in CT.SUBTITULOS:
                if a <= t < b:
                    k = min(1.0, (t - a) / 0.15, (b - t) / 0.15)
                    cuerpo = self.txt(texto, 32, "#fbf6ee", xmaximum=1500, text_align=0.5, layout="subtitle")
                    etiq = self.txt(quien, 20, "#e8b04b", bold=True, kerning=4)
                    cr = renpy.render(cuerpo, 1500, 300, ctx[2], ctx[3])
                    ce = renpy.render(etiq, 800, 100, ctx[2], ctx[3])
                    alto = cr.height + ce.height + 34
                    ancho = max(cr.width, ce.width) + 60
                    y = 1006 - alto
                    self.pon(r, Solid("#120d1cd8"), 960 - ancho / 2, y, ctx, xsize=int(ancho), ysize=int(alto), alpha=k)
                    r.blit(ce, (int(960 - ce.width / 2), int(y + 12)))
                    r.blit(cr, (int(960 - cr.width / 2), int(y + 18 + ce.height)))
                    return

        # ---------- CivitasNet: el rumor se multiplica ----------
        def crear_feed(self):
            posts = (("@alerta.ciudadana", "NO TOMEN AGUA DEL GRIFO. Ya hay gente en urgencias. COMPARTAN", "18,4 mil"),
                     ("@barrio.norte.unido", "Bloqueemos la avenida hasta que alguien nos dé la cara.", "9,1 mil"),
                     ("@mama_de_tres", "¿Alguien sabe algo oficial? Mis hijos tomaron agua esta mañana.", "2,3 mil"),
                     ("@taxista_247", "Av. Central cerrada. Nadie pasa. Ni las ambulancias.", "6,7 mil"),
                     ("@despierta.ya", "#AguaEnvenenada #AguaEnvenenada #AguaEnvenenada", "31,0 mil"),
                     ("@vecina.del.sur", "Me llegó por tres grupos distintos. Tiene que ser verdad.", "4,8 mil"))
            cajas = []
            for quien, dice, reposts in posts:
                cajas.append(Fixed(
                    Solid("#2b2440", xsize=780, ysize=196),
                    Transform(Solid("#fbf6ee"), xsize=772, ysize=188, xpos=4, ypos=4),
                    Transform(Solid("#d1495b"), xsize=12, ysize=188, xpos=4, ypos=4),
                    Text(quien, size=24, bold=True, color="#8c2f4b", xpos=40, ypos=22),
                    Text(dice, size=30, bold=True, color="#2b2440", xpos=40, ypos=60, xmaximum=700),
                    Text("%s reposts" % reposts, size=22, color="#d1495b", bold=True, xpos=40, ypos=152),
                    xysize=(780, 196)))
            return VBox(*cajas, spacing=26)

        # ---------- planos ----------
        def p_noticias(self, r, ctx, t):
            m = dict((n, (a, b)) for n, a, b in CT.MONTAJE)
            sub = next(n for n, a, b in CT.MONTAJE if a <= t < b) if t < CT.MONTAJE[-1][2] else "atasco"
            if sub == "cortinilla":
                self.velo(r, ctx, "#120d1c", 1.0)
                for i, (col, y, alto, ret) in enumerate((("#8c2f4b", 360, 120, 0.0), ("#d1495b", 480, 18, 0.12),
                                                       ("#2b2440", 498, 120, 0.2))):
                    k = cine_suave((t - ret) / 0.4)
                    self.pon(r, Solid(col), int(-1920 * (1 - k)), y, ctx, xsize=1920, ysize=alto)
                k = cine_suave((t - 0.3) / 0.35)
                self.pon(r, self.txt("NOTICIAS NOVA", 84, "#fbf6ee", font=AP_FUENTE_FINA, kerning=16), 960, 420, ctx,
                         alpha=k, xanchor=0.5, yanchor=0.5)
                self.pon(r, self.txt("ÚLTIMA HORA", 40, "#fbf6ee", bold=True, kerning=12), 960, 560, ctx,
                         alpha=k, xanchor=0.5, yanchor=0.5)
                self.pon(r, self.txt("CIUDAD NOVA  ·  UN AÑO ANTES DE LAS ELECCIONES", 26, "#c9b8d8",
                                     font=AP_FUENTE_FINA, kerning=6), 960, 690, ctx,
                         alpha=cine_suave((t - 0.45) / 0.3), xanchor=0.5)
                return
            if sub == "mapa":
                a, b = m["mapa"]
                p = (t - a) / (b - a)
                z = 0.62 + 0.1 * (0 if self.reducido else p)
                cx, cy = 1600 + 120 * p, 1000
                ox, oy = 960 - cx * z, 540 - cy * z
                self.pon(r, "images/bg/mapa.jpg", ox, oy, ctx, zoom=z)
                self.velo(r, ctx, "#120d1c", 0.38)
                n = min(len(self.BLOQUEOS), int((t - a) / 0.09) + 1)
                for i, (x, y) in enumerate(self.BLOQUEOS[:n]):
                    k = cine_suave((t - a - i * 0.09) / 0.18)
                    self.pon(r, self.img("icono_bloqueo"), ox + x * z, oy + y * z, ctx, zoom=0.6 + 0.4 * k,
                             alpha=k, xanchor=0.5, yanchor=0.5)
                ax, ay = 1500, 960
                pulso = (t * 1.5) % 1.0
                self.pon(r, Solid("#fbf6ee"), ox + ax * z, oy + ay * z, ctx, alpha=0.5 * (1 - pulso),
                         xsize=int(40 + 90 * pulso), ysize=int(40 + 90 * pulso), xanchor=0.5, yanchor=0.5)
                self.pon(r, self.img("icono_ambulancia"), ox + ax * z, oy + ay * z, ctx, xanchor=0.5, yanchor=0.5)
                self.pon(r, Solid("#fbf6ee"), 1450, 150, ctx, xsize=400, ysize=120)
                self.pon(r, Solid("#d1495b"), 1450, 150, ctx, xsize=10, ysize=120)
                self.pon(r, self.txt("PUNTOS BLOQUEADOS", 20, "#8c2f4b", bold=True, kerning=3), 1480, 168, ctx)
                self.pon(r, self.txt("%d" % n, 60, "#2b2440", font=AP_FUENTE_FINA), 1480, 192, ctx)
            elif sub == "barricada":
                a, b = m["barricada"]
                p = (t - a) / (b - a)
                self.calle(r, ctx, t, 4260 - 140 * p, 800, 1.12 + 0.12 * p, luces=False)
            elif sub == "feed":
                a, b = m["feed"]
                self.velo(r, ctx, "#1d1530", 1.0)
                for i in range(0, 1920, 64):
                    self.pon(r, Solid("#251c3a"), i, 0, ctx, xsize=2, ysize=1080)
                dy = 0 if self.reducido else -(t - a) * 520
                self.pon(r, self.feed, 960, 120 + dy, ctx, xanchor=0.5)
                k = cine_suave((t - a - 0.35) / 0.3)
                self.pon(r, Solid("#d1495b"), 1300, 190, ctx, xsize=520, ysize=96, alpha=k)
                self.pon(r, self.txt("CIVITAS  ·  ALERTA", 20, "#fbf6ee", bold=True, kerning=3), 1326, 206, ctx, alpha=k)
                self.pon(r, self.txt("#AguaEnvenenada es tendencia", 30, "#fbf6ee", bold=True), 1326, 236, ctx, alpha=k)
            else:
                a, b = m["atasco"]
                p = (t - a) / (b - a)
                self.calle(r, ctx, t, 1500 + 500 * p, 770, 0.74, sirena_global=0.0)
            self.mosca(r, ctx, t, "21:47")
            self.zocalo(r, ctx, t, CT.MONTAJE[1][1], "ÚLTIMA HORA", "BLOQUEOS SE EXTIENDEN POR CIUDAD NOVA")
            self.cintillo(r, ctx, t, "Bloqueos en 14 puntos de la ciudad   ·   Autoridades piden no compartir "
                                     "información sin verificar   ·   Hospitales reportan demoras en los traslados   ·   ")
            if sub == "barricada":
                self.pon(r, Solid("#120d1cc0"), 56, 120, ctx, xsize=360, ysize=44)
                self.pon(r, self.txt("EN DIRECTO  ·  AV. CENTRAL", 22, "#fbf6ee", bold=True, kerning=2), 72, 130, ctx)

        def p_ambulancia(self, r, ctx, t):
            t0 = CT.inicio("ambulancia")
            cam = ((t0, 980, 800, 1.5), (t0 + 1.4, 1040, 800, 1.42), (t0 + 5.6, 3900, 790, 1.0), (t0 + 6.0, 3980, 790, 0.98))
            cx, cy, z = cine_interp(cam, t)
            self.calle(r, ctx, t, cx, cy, z, sirena_global=0.04)
            k = cine_suave((t - t0 - 0.3) / 0.4) * (1 - cine_suave((t - t0 - 3.6) / 0.4))
            if k > 0:
                self.pon(r, Solid("#fbf6ee"), 72, 64, ctx, xsize=430, ysize=94, alpha=k)
                self.pon(r, Solid("#d1495b"), 72, 64, ctx, xsize=10, ysize=94, alpha=k)
                self.pon(r, self.txt("AV. CENTRAL  ·  21:52", 22, "#8c2f4b", bold=True, kerning=3), 100, 80, ctx, alpha=k)
                self.pon(r, self.txt("Ambulancia 12, detenida", 30, "#2b2440", bold=True), 100, 112, ctx, alpha=k)
            self.dramatizacion(r, ctx)

        def p_paciente(self, r, ctx, t):
            t0 = CT.inicio("paciente")
            # La camara recorre a la paciente y sube al monitor; al final se acelera hacia la pantalla
            # (corte en movimiento al primer plano del monitor).
            cam = ((t0, 860, 600, 1.0), (t0 + 3.4, 1300, 420, 1.12), (t0 + 4.2, 1410, 380, 1.75))
            if self.reducido:
                cam = ((t0, 960, 540, 1.0),)
            fx, fy, z = cine_interp(cam, t)
            sx, sy = self.sacudida(t, 0.35)
            # El encuadre nunca sale del interior (1920 x 1080 a escala z).
            ox = min(0.0, max(1920 - 1920 * z, 960 - fx * z + sx))
            oy = min(0.0, max(1080 - 1080 * z, 540 - fy * z + sy))

            def en(x, y):
                return ox + x * z, oy + y * z

            x, y = en(0, 0)
            self.pon(r, self.img("interior_fondo"), x, y, ctx, zoom=z)
            # Luz de la sirena entrando por la ventana trasera.
            rojo = (t * 2.6) % 1.0 < 0.5
            x, y = en(200, 330)
            self.pon(r, self.img("luz_roja" if rojo else "luz_azul"), x, y, ctx, zoom=z * 1.8, xanchor=0.5, yanchor=0.5,
                     aditivo=True)
            # Monitor en la pared (con su senal viva).
            self.monitor.t = t
            x, y = en(930 + CINE_PANTALLA[0] * 0.5, 110 + CINE_PANTALLA[1] * 0.5)
            self.pon(r, self.monitor, x, y, ctx, zoom=z * 0.5)
            x, y = en(930, 110)
            self.pon(r, self.img("monitor_marco"), x, y, ctx, zoom=z * 0.5)
            # Suero que se balancea, camilla y paramedica (respira, se inclina).
            giro = 0 if self.reducido else _cine_math.sin(t * 1.9) * 4
            x, y = en(760, 128)
            self.pon(r, self.img("interior_suero"), x, y, ctx, zoom=z, rotar=giro, xanchor=0.5)
            x, y = en(240, 470)
            self.pon(r, self.img("interior_camilla"), x, y, ctx, zoom=z)
            resp = 0 if self.reducido else _cine_math.sin(t * 2.4) * 6
            x, y = en(-40, 330 + resp)
            self.pon(r, self.img("interior_paramedico"), x, y, ctx, zoom=z * 0.78)
            self.velo(r, ctx, "#d1495b" if rojo else "#3d7ea6", 0.07)
            self.dramatizacion(r, ctx)

        def p_monitor(self, r, ctx, t):
            t0 = CT.inicio("monitor")
            fin_empuje = CT.TONO[0]
            p = min(t, fin_empuje) - t0
            z = 1.0 + (0 if self.reducido else 0.05 * p / (fin_empuje - t0))
            entrada = 0 if self.reducido else 0.22 * (1 - cine_suave((t - t0) / 0.6))
            z += entrada
            sx, sy = self.sacudida(t, 0.25 if t < CT.PLANA else 0.0)
            ox, oy = 960 - 960 * z + sx, 520 - 520 * z + sy
            self.velo(r, ctx, "#0d0a14", 1.0)
            self.monitor.t = t
            self.pon(r, self.monitor, ox + CINE_PANTALLA[0] * z, oy + CINE_PANTALLA[1] * z, ctx, zoom=z)
            self.pon(r, self.img("monitor_marco"), ox, oy, ctx, zoom=z)
            if CT.TONO[0] <= t < CT.CONGELADO[1] and (t >= CT.CONGELADO[0] or int(t * 2.5) % 2 == 0):
                self.pon(r, Solid("#ff5a6e"), ox + 1504 * z, oy + 950 * z, ctx, xsize=int(32 * z), ysize=int(24 * z))
            # Viñeta: la luz de la sala se apaga en cuanto la senal es plana.
            self.velo(r, ctx, "#0d0a14", 0.25 * cine_suave((t - CT.PLANA) / 1.2))

        def p_noticia_muerte(self, r, ctx, t):
            t0 = CT.inicio("noticia_muerte")
            p = (t - t0) / 10.0
            self.calle(r, ctx, t, 980 + 60 * p, 800, 1.08 + (0 if self.reducido else 0.08 * p), gente=False, desat=True)
            self.mosca(r, ctx, t, "23:10")
            if t < CT.TITULAR:
                self.zocalo(r, ctx, t, t0 + 0.4, "ÚLTIMA HORA", "FALLECE PACIENTE TRAS DEMORA EN SU TRASLADO")
            else:
                k = cine_suave((t - CT.TITULAR) / 0.5)
                dx = 0 if self.reducido else int((1 - k) * 1920)
                self.pon(r, Solid("#120d1c"), dx, 300, ctx, xsize=1920, ysize=330, alpha=0.9)
                self.pon(r, Solid("#8c2f4b"), dx, 330, ctx, xsize=1920, ysize=170)
                self.pon(r, Solid("#d1495b"), dx, 500, ctx, xsize=1920, ysize=8)
                self.pon(r, self.txt("LA DESINFORMACIÓN COBRÓ OTRA VÍCTIMA", 76, "#fbf6ee", bold=True, kerning=2),
                         960 + dx, 415, ctx, xanchor=0.5, yanchor=0.5)
                self.pon(r, self.txt("Se investiga si los bloqueos retrasaron la atención del paciente", 32, "#c9b8d8",
                                     font=AP_FUENTE_FINA), 960 + dx, 562, ctx, alpha=cine_suave((t - CT.TITULAR - 0.5) / 0.4),
                         xanchor=0.5, yanchor=0.5)
            self.cintillo(r, ctx, t, "Autoridades piden verificar antes de compartir   ·   El rumor sobre el agua no tiene "
                                     "respaldo de ningún análisis   ·   Siguen los bloqueos en la Av. Central   ·   ")

        def p_titulo(self, r, ctx, t):
            t0 = CT.inicio("titulo")
            s = t - t0
            self.velo(r, ctx, "#120d1c", 1.0)
            self.pon(r, "images/bg/mapa.jpg", 0, 0, ctx, zoom=0.625, alpha=0.16 * cine_suave(s / 1.0))
            cr = renpy.render(self.titulo, ctx[0], ctx[1], s, ctx[3])
            r.blit(cr, (0, 0))
            self.pon(r, self.txt("ALCALDE DIGITAL", 34, "#d1495b", font=AP_FUENTE_FINA, kerning=22), 960, 690, ctx,
                     alpha=cine_suave((s - 1.4) / 0.5), xanchor=0.5)
            self.pon(r, self.txt("Una mentira puede recorrer una ciudad. Sus consecuencias también.", 30, "#c9b8d8",
                                 font=AP_FUENTE_FINA, kerning=2), 960, 772, ctx,
                     alpha=cine_suave((s - 2.0) / 0.6), xanchor=0.5)

        def dramatizacion(self, r, ctx):
            self.pon(r, self.txt("DRAMATIZACIÓN", 18, "#c9b8d8", kerning=5), 1864, 1040, ctx, xanchor=1.0, alpha=0.55)

        PLANOS = {"noticias": "p_noticias", "ambulancia": "p_ambulancia", "paciente": "p_paciente",
                  "monitor": "p_monitor", "noticia_muerte": "p_noticia_muerte", "titulo": "p_titulo"}

        def plano_render(self, nombre, ctx, t):
            w, h = ctx[0], ctx[1]
            r = renpy.Render(w, h)
            getattr(self, self.PLANOS[nombre])(r, ctx, t)
            return r

        def render(self, width, height, st, at):
            t = self.reloj(st)
            self.t = t
            self.cuadros += 1
            ctx = (width, height, st, at)
            r = renpy.Render(width, height)
            r.blit(renpy.render(Solid("#000000"), width, height, st, at), (0, 0))
            nombre = CT.plano(t)
            inicio = CT.inicio(nombre)
            fundido = CT.FUNDIDO.get(nombre, 0.0)
            if fundido and t - inicio < fundido:
                previo = [n for n, a, b in CT.PLANOS if b == inicio][0]
                r.blit(self.plano_render(previo, ctx, t), (0, 0))
                actual = self.plano_render(nombre, ctx, t)
                actual.alpha = cine_suave((t - inicio) / fundido)
                r.blit(actual, (0, 0))
            else:
                r.blit(self.plano_render(nombre, ctx, t), (0, 0))
            if nombre != "titulo":
                self.subtitulo(r, ctx, t)
            # Cierre a negro en el ultimo medio segundo.
            self.velo(r, ctx, "#000000", cine_suave((t - (CT.DURACION - 0.5)) / 0.5))
            renpy.redraw(self, 0)
            return r


screen cinematica_apertura():
    modal True
    zorder 40
    default cine = CinematicaApertura()
    add cine
    textbutton "Omitir ›" style "arena_link_claro" xalign 0.985 yalign 0.025 action Return("omitida")
    key "game_menu" action Return("omitida")
    timer CT.DURACION action Return("completa")
    on "show" action Function(cine_audio_iniciar)
    on "hide" action Function(cine_audio_detener)
    on "replaced" action Function(cine_audio_detener)

## Se llama desde start y modo_feria, justo antes del prologo. No cambia puntos, pistas, finales ni estadisticas.
label cinematica_apertura:
    if renpy.config.skipping:
        return "saltada"
    $ quick_menu = False
    window hide
    stop music fadeout 0.4
    stop ambiente fadeout 0.4
    scene negro
    call screen cinematica_apertura
    $ cine_audio_detener(0.3)
    scene negro
    return _return
