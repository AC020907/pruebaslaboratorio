## Duelo de Frecuencias: minijuego ritmico original (motor en clases/Ritmo.py).
## Las notas se dibujan desde el tiempo de la cancion (posicion real del audio); los frames solo pintan.
##   Teclado: D F J K o flechas · Mando: cruceta o X A Y RB · Tactil: tocar el carril · Pausa: Esc / Start
##   Dificil (5 carriles): D F Espacio J K · Mando: izquierda, abajo, A, arriba, derecha

default persistent.ritmo_offset_ms = 0
default persistent.ritmo_velocidad = 1.0

init python:
    import json as _json_ritmo
    import time as _time_ritmo
    from clases import Ritmo

    renpy.music.register_channel("ritmo", mixer="music", loop=False, stop_on_mute=False, tight=True)

    config.keymap.update({
        "civ_r0": ["K_d", "K_LEFT"], "civ_r1": ["K_f", "K_DOWN"],
        "civ_r2": ["K_j", "K_UP"], "civ_r3": ["K_k", "K_RIGHT"],
        "civ_pausa": ["K_ESCAPE", "K_p"],
        # Dificil: cinco carriles, dos manos (D F | Espacio con el pulgar | J K).
        "civ_q0": ["K_d"], "civ_q1": ["K_f"], "civ_q2": ["K_SPACE"], "civ_q3": ["K_j"], "civ_q4": ["K_k"],
    })
    for _ev, _carril in (("pad_dpleft_press", 0), ("pad_x_press", 0), ("pad_dpdown_press", 1), ("pad_a_press", 2),
                         ("pad_dpup_press", 3), ("pad_y_press", 3), ("pad_dpright_press", 4), ("pad_rightshoulder_press", 4)):
        config.pad_bindings[_ev] = list(config.pad_bindings.get(_ev, [])) + ["civ_q%d" % _carril]
    for _ev, _carril in (("pad_dpleft_press", 0), ("pad_x_press", 0), ("pad_dpdown_press", 1), ("pad_a_press", 1),
                         ("pad_dpup_press", 2), ("pad_y_press", 2), ("pad_dpright_press", 3), ("pad_rightshoulder_press", 3)):
        config.pad_bindings[_ev] = list(config.pad_bindings.get(_ev, [])) + ["civ_r%d" % _carril]
    config.pad_bindings["pad_start_press"] = list(config.pad_bindings.get("pad_start_press", [])) + ["civ_pausa"]

    RITMO_CARRIL_W = 150
    RITMO_GAP = 22
    RITMO_X0 = 960 - (4 * RITMO_CARRIL_W + 3 * RITMO_GAP) // 2
    RITMO_RECEPTOR_Y = 860
    RITMO_RECORRIDO_MS = 1500
    RITMO_NACE_Y = 150              # centro de la nota al aparecer: por debajo de la cabecera
    RITMO_FUNDIDO_PX = 120
    # Paleta de Civitas: ambar (perfecto), teal (bien), lila (justo), gris (fallo). La forma del anillo tambien cambia.
    COLOR_JUICIO = {"perfect": "#e8b04b", "good": "#3fbfae", "bad": "#c9b8d8", "miss": "#8b84a8"}
    RITMO_TINTA = "#2b2440"
    TEXTO_JUICIO = {"perfect": "¡PERFECTO!", "good": "BIEN", "bad": "JUSTO", "miss": "FALLO"}
    # Modo competitivo de la Arena: nombres de juicio de juego de ritmo (mismas ventanas que Normal).
    TEXTO_JUICIO_COMPETITIVO = {"perfect": "PERFECT", "good": "GREAT", "bad": "GOOD", "miss": "MISS"}
    duelo_competitivo = False

    def texto_juicio(j):
        return (TEXTO_JUICIO_COMPETITIVO if duelo_competitivo else TEXTO_JUICIO)[j]
    DIFICULTADES = {
        "normal": {"chart": "normal", "ventanas": None, "umbral": Ritmo.UMBRAL_EXITO},
        "facil": {"chart": "facil", "ventanas": None, "umbral": Ritmo.UMBRAL_EXITO},
        # Asistido: notas en pulsos enteros, ventanas amplias y meta baja. Nadie queda fuera del duelo.
        "asistido": {"chart": "facil", "ventanas": {"perfect": 70, "good": 140, "bad": 210}, "umbral": 0.45},
        # Dificil: cancion original a 144 BPM y 5 carriles (tools/musica/duelo_dificil.py). Mismas ventanas y meta
        # que Normal: la dificultad esta en las notas (densidad, rafagas, dobles, cambios de carril), no en el juez.
        "dificil": {"chart": "dificil", "archivo": "ritmo/duelo_dificil.json", "audio": "assets/audio/music/duelo_dificil.ogg",
                    "ventanas": None, "umbral": Ritmo.UMBRAL_EXITO},
    }
    RITMO_TECLAS_5 = ("D", "F", "ESPACIO", "J", "K")
    RITMO_IMAGEN_5 = (0, 1, 4, 2, 3)        # circulo, rombo, hexagono (centro), triangulo, cuadrado

    def cargar_chart(modo, dificultad):
        nombre = DIFICULTADES[dificultad].get("archivo") or "ritmo/duelo_%s_%s.json" % (modo, DIFICULTADES[dificultad]["chart"])
        with renpy.open_file(nombre, encoding="utf-8") as f:
            return _json_ritmo.loads(f.read())

    class VistaDuelo(renpy.Displayable):
        def __init__(self, modo, dificultad, **kwargs):
            super(VistaDuelo, self).__init__(**kwargs)
            cfg = DIFICULTADES[dificultad]
            self.modo = modo
            self.duelo = Ritmo.Duelo(cargar_chart(modo, dificultad), cfg["ventanas"], cfg["umbral"])
            self.reloj = Ritmo.RelojCancion(persistent.ritmo_offset_ms)
            self.audio = cfg.get("audio") or "assets/audio/music/duelo_%s.ogg" % modo
            self.dificultad = dificultad
            self.arrancado = False
            self.t = 0.0
            self.pulsados = {}            # carril -> tiempo de cancion del ultimo toque (brillo del receptor)
            self.n = self.duelo.carriles
            figuras = RITMO_IMAGEN_5 if self.n == 5 else tuple(range(4))
            self.ancho_c = RITMO_CARRIL_W if self.n == 4 else 132
            self.gap = RITMO_GAP if self.n == 4 else 16
            self.x0 = 960 - (self.n * self.ancho_c + (self.n - 1) * self.gap) // 2
            self.notas = [Image("gui/ritmo/nota_%d.png" % k) for k in figuras]
            # Las notas nacen con un fundido por debajo de la cabecera (titulo y barra de senal).
            self.notas_fundido = [[Transform(n, alpha=a / 4.0) for a in range(1, 4)] for n in self.notas]
            self.receptores = [Image("gui/ritmo/receptor_%d.png" % k) for k in figuras]
            self.receptores_on = [Image("gui/ritmo/receptor_on_%d.png" % k) for k in figuras]
            self.hito = None              # (combo, tiempo): COMBO x25, x50... late en el centro
            self.textos = {}
            self.fondo_carril = Solid("#1b142699")
            self.estado_visto = None
            self.combo_visto, self.combo_t = 0, -9999.0      # el contador de combo "late" cuando sube
            self.bpm = float(self.duelo.chart.get("bpm") or 120)

        def texto(self, s, size, color):
            clave = (s, size, color)
            if clave not in self.textos:
                self.textos[clave] = Text(s, size=size, color=color, bold=True, outlines=[(3, "#1b1426", 0, 0)])
            return self.textos[clave]

        def x_carril(self, k):
            return self.x0 + k * (self.ancho_c + self.gap)

        # ----- ciclo -----
        def arrancar(self):
            renpy.music.stop(channel="music", fadeout=0.8)
            renpy.music.play(self.audio, channel="ritmo", loop=False)
            self.arrancado = True
            self.duelo.empezar()

        def pausar(self):
            if self.duelo.estado == Ritmo.PLAYING:
                self.duelo.pausar()
                self.reloj.pausar()
                renpy.music.set_pause(True, channel="ritmo")
                renpy.restart_interaction()

        def reanudar(self):
            if self.duelo.estado == Ritmo.PAUSED:
                renpy.music.set_pause(False, channel="ritmo")
                self.reloj.reanudar()
                self.duelo.reanudar()
                # render() solo se reprograma mientras se juega: en pausa deja de pedir cuadros, asi que
                # al reanudar hay que pedir el primero o el duelo queda congelado.
                renpy.redraw(self, 0)
                renpy.restart_interaction()

        def abandonar(self):
            self.duelo.abortar()
            renpy.music.stop(channel="ritmo", fadeout=0.5)
            renpy.redraw(self, 0)
            renpy.restart_interaction()

        def ajustar_offset(self, delta):
            persistent.ritmo_offset_ms = max(-200, min(200, persistent.ritmo_offset_ms + delta))
            self.reloj.offset_ms = persistent.ritmo_offset_ms
            renpy.restart_interaction()

        # ----- dibujo -----
        def render(self, width, height, st, at):
            if not self.arrancado:
                self.arrancar()
            quieto = persistent.reducir_movimiento
            d = self.duelo
            if d.estado == Ritmo.PLAYING:
                self.t = self.reloj.actualizar(renpy.music.get_pos(channel="ritmo"), _time_ritmo.time())
                d.actualizar(self.t)
            if d.estado != self.estado_visto:
                self.estado_visto = d.estado
                renpy.restart_interaction()
            r = renpy.Render(width, height)
            recorrido = RITMO_RECORRIDO_MS / max(0.5, persistent.ritmo_velocidad)
            # Pista (remaster): franja con contorno de tinta, separadores, linea de golpe y pulsos del compas.
            x0p = self.x0 - 26
            x1p = self.x_carril(self.n - 1) + self.ancho_c + 26
            m_img = (self.ancho_c - 110) // 2
            r.blit(renpy.render(Solid(RITMO_TINTA), x1p - x0p + 8, 1080, st, at), (x0p - 4, 0))
            r.blit(renpy.render(Solid("#120d1cf0"), x1p - x0p, 1080, st, at), (x0p, 0))
            c = r.canvas()
            for k in range(1, self.n):
                xs = self.x_carril(k) - self.gap // 2
                c.line("#3a3350", (xs, 0), (xs, 1080), 2)
            pulso = 60000.0 / self.bpm
            if d.estado in (Ritmo.PLAYING, Ritmo.PAUSED):
                base = int(self.t // pulso)
                for i in range(0, 8):
                    tb = (base + i) * pulso
                    yb = RITMO_RECEPTOR_Y - (tb - self.t) / recorrido * (RITMO_RECEPTOR_Y + 60)
                    if RITMO_NACE_Y < yb < RITMO_RECEPTOR_Y:
                        fuerte = (base + i) % 4 == 0
                        c.line("#4a3f66" if fuerte else "#2f2744", (x0p + 6, int(yb)), (x1p - 6, int(yb)), 3 if fuerte else 2)
            c.line(RITMO_TINTA, (x0p, RITMO_RECEPTOR_Y), (x1p, RITMO_RECEPTOR_Y), 12)
            c.line("#c9b8d8", (x0p, RITMO_RECEPTOR_Y), (x1p, RITMO_RECEPTOR_Y), 4)
            for k in range(self.n):
                x = self.x_carril(k)
                edad_p = self.t - self.pulsados.get(k, -9999)
                if 0 <= edad_p < 160 and not quieto:
                    alto = int(320 * (1 - edad_p / 160.0))
                    r.blit(renpy.render(Transform(Solid("#fbf6ee"), xysize=(self.ancho_c, alto), alpha=0.10), self.ancho_c, alto, st, at),
                           (x, RITMO_RECEPTOR_Y - alto))
                brillo = edad_p < 110
                rec = (self.receptores_on if brillo else self.receptores)[k]
                r.blit(renpy.render(rec, 110, 110, st, at), (x + m_img, RITMO_RECEPTOR_Y - 55))
                if self.n == 5:
                    tecla = renpy.render(self.texto(RITMO_TECLAS_5[k], 22, "#fbf6ee" if brillo else "#c9b8d8"), 200, 40, st, at)
                    r.blit(tecla, (x + self.ancho_c // 2 - tecla.get_size()[0] // 2, RITMO_RECEPTOR_Y + 64))
            for n in (d.visibles(self.t, recorrido) if d.estado in (Ritmo.PLAYING, Ritmo.PAUSED) else ()):
                y = RITMO_RECEPTOR_Y - (n["time_ms"] - self.t) / recorrido * (RITMO_RECEPTOR_Y + 60)
                if y < RITMO_NACE_Y:
                    continue
                nivel = int((y - RITMO_NACE_Y) / RITMO_FUNDIDO_PX * 4)
                img = self.notas[n["lane"]] if nivel >= 3 else self.notas_fundido[n["lane"]][nivel]
                r.blit(renpy.render(img, 110, 110, st, at), (self.x_carril(n["lane"]) + m_img, int(y) - 55))
            for t_j, carril, juicio in d.ultimos:
                edad = self.t - t_j
                if 0 <= edad < 450:
                    cx = self.x_carril(carril) + self.ancho_c // 2
                    # Anillo en el receptor: doble (perfecto), simple (bien/justo), cruz (fallo).
                    if juicio != "miss":
                        k_a = edad / 450.0
                        rad = int(58 + (0 if quieto else 40 * k_a))
                        c.circle(COLOR_JUICIO[juicio], (cx, RITMO_RECEPTOR_Y), rad, 5)
                        if juicio == "perfect":
                            c.circle(COLOR_JUICIO[juicio], (cx, RITMO_RECEPTOR_Y), max(10, rad - 16), 3)
                    elif edad < 250:
                        c.line("#8b84a8", (cx - 22, RITMO_RECEPTOR_Y - 22), (cx + 22, RITMO_RECEPTOR_Y + 22), 6)
                        c.line("#8b84a8", (cx + 22, RITMO_RECEPTOR_Y - 22), (cx - 22, RITMO_RECEPTOR_Y + 22), 6)
                    zoom_j = 1.0 if quieto else (1.25 - 0.25 * min(1.0, edad / 120.0))
                    txt = renpy.render(Transform(self.texto(texto_juicio(juicio), 38 if self.n == 4 else 27, COLOR_JUICIO[juicio]), zoom=zoom_j), 500, 80, st, at)
                    w, _h = txt.get_size()
                    subida = 0 if quieto else int(edad / 12)
                    r.blit(txt, (cx - w // 2, RITMO_RECEPTOR_Y - 140 - subida))
            if d.combo > self.combo_visto:
                self.combo_t = self.t
                if d.combo // 25 > self.combo_visto // 25:
                    self.hito = (d.combo // 25 * 25, self.t)
            self.combo_visto = d.combo
            if d.combo >= 5:
                late = 1.0 if quieto else (1.0 + 0.18 * max(0.0, 1 - (self.t - self.combo_t) / 140.0))
                num = renpy.render(Transform(Text("%d" % d.combo, font="fonts/Roboto-Light.ttf", size=96, color="#fbf6ee",
                                                  outlines=[(3, RITMO_TINTA, 0, 0)]), zoom=late), 400, 160, st, at)
                etq = renpy.render(self.texto("COMBO", 22, "#c9b8d8"), 300, 40, st, at)
                xc = x0p - 40 - max(etq.get_size()[0], num.get_size()[0])
                r.blit(etq, (xc, 470))
                r.blit(num, (xc - 4, 494))
            if self.hito and 0 <= self.t - self.hito[1] < 700:
                k_h = (self.t - self.hito[1]) / 700.0
                txt_h = renpy.render(Transform(Text("COMBO x%d" % self.hito[0], font="fonts/Roboto-Light.ttf", size=88, color="#e8b04b",
                                                    outlines=[(4, RITMO_TINTA, 0, 0)]), zoom=1.0 if quieto else 1.0 + 0.2 * (1 - k_h),
                                               alpha=1 - k_h * k_h), 900, 160, st, at)
                r.blit(txt_h, (960 - txt_h.get_size()[0] // 2, 300))
            if self.arrancado and d.estado == Ritmo.PLAYING:
                primera = d.chart["notes"][0]["time_ms"]
                if self.t < primera:
                    falta = int((primera - self.t) / 1000.0) + 1
                    letrero = "¡YA!" if self.t > primera - 500 else str(min(3, falta))
                    cr = renpy.render(self.texto(letrero, 120, "#fbf6ee"), 600, 200, st, at)
                    r.blit(cr, (960 - cr.get_size()[0] // 2, 380))
            if d.estado in (Ritmo.PLAYING, Ritmo.COUNTDOWN):
                renpy.redraw(self, 0)
            return r

        # ----- entrada -----
        def pulsar(self, carril):
            if self.duelo.estado != Ritmo.PLAYING:
                return
            t = self.reloj.actualizar(renpy.music.get_pos(channel="ritmo"), _time_ritmo.time())
            self.pulsados[carril] = t
            self.duelo.pulsar(carril, t)
            renpy.redraw(self, 0)

        def event(self, ev, x, y, st):
            if self.duelo.estado == Ritmo.PLAYING:
                prefijo = "civ_q%d" if self.n == 5 else "civ_r%d"
                for k in range(self.n):
                    if renpy.map_event(ev, prefijo % k):
                        self.pulsar(k)
                        raise renpy.IgnoreEvent()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for k in range(self.n):
                        if self.x_carril(k) <= x < self.x_carril(k) + self.ancho_c and y > 300:
                            self.pulsar(k)
                            raise renpy.IgnoreEvent()
                if renpy.map_event(ev, "civ_pausa") or renpy.map_event(ev, "game_menu"):
                    self.pausar()
                    raise renpy.IgnoreEvent()
            return None

        def visit(self):
            return self.notas + self.receptores + self.receptores_on

    def expresion_rival(duelo):
        if duelo.combo >= 10:
            return "enojada"
        if duelo.ultimos and duelo.ultimos[-1][2] == "miss":
            return "feliz"
        return "seria"


transform duelo_respira:
    block:
        easein 0.5 yoffset -6
        easeout 0.5 yoffset 0
        repeat

screen duelo_pantalla(vista, aliado):
    modal True
    zorder 45
    add "bg operaciones"
    add Solid("#120d1ccc")
    $ d = vista.duelo
    ## NOVA a la izquierda, el aliado a la derecha: reaccionan a los combos y fallos.
    if persistent.reducir_movimiento:
        add retrato_escena("nova", expresion_rival(d)) xpos 0.12 xanchor 0.5 yalign 1.0 zoom 0.8
    else:
        add retrato_escena("nova", expresion_rival(d)) xpos 0.12 xanchor 0.5 yalign 1.0 zoom 0.8 at duelo_respira
    if aliado:
        add retrato_escena(aliado, "feliz" if d.combo >= 5 else "seria"):
            xpos 0.88
            xanchor 0.5
            yalign 1.0
            zoom 0.8
    add vista
    ## Senal vs interferencia: lectura del duelo sin depender solo del color (texto y porcentaje).
    vbox:
        xalign 0.5
        ypos 26
        spacing 6
        text "DUELO DE FRECUENCIAS" font "fonts/Roboto-Light.ttf" size 32 color "#fbf6ee" xalign 0.5 kerning 8
        $ juzgadas = max(1, d.juzgadas())
        $ senal = sum(Ritmo.VALOR_JUICIO[j] * c for j, c in d.conteo.items()) / juzgadas
        hbox:
            spacing 12
            text "INTERFERENCIA" size 16 color "#d1495b" yalign 0.5
            bar value StaticValue(senal if d.juzgadas() else 0.5, 1.0) xsize 520 ysize 16 left_bar Solid("#3fbfae") right_bar Solid("#d1495b")
            text "SEÑAL %d%%" % int((senal if d.juzgadas() else 0.5) * 100) size 16 color "#3fbfae" yalign 0.5

    if d.estado == "playing":
        textbutton "Pausa" style "boton_vn" text_style "boton_vn_text" xalign 0.98 yalign 0.03 action Function(vista.pausar)
    if d.estado == "paused":
        use duelo_pausa(vista)
    elif d.estado in ("results", "aborted"):
        use duelo_resultados(vista)

screen duelo_pausa(vista):
    add Solid("#000000b8")
    frame:
        align (0.5, 0.5)
        xsize 1040
        background Frame("gui/frame.png", 30, 30)
        padding (48, 36)
        has vbox
        spacing 16
        xfill True
        text "PAUSA" size 44 bold True color "#2b2440" xalign 0.5
        text ("Calibración: %+d ms   (si las notas parecen llegar tarde, sube; si llegan antes, baja)" % persistent.ritmo_offset_ms) size 18 color "#5b4f72" xalign 0.5 text_align 0.5
        hbox:
            xalign 0.5
            spacing 16
            textbutton "-10 ms" style "boton_vn_compacto" text_style "boton_vn_text" action Function(vista.ajustar_offset, -10)
            textbutton "+10 ms" style "boton_vn_compacto" text_style "boton_vn_text" action Function(vista.ajustar_offset, 10)
        hbox:
            xalign 0.5
            spacing 16
            for v in (0.75, 1.0, 1.25):
                textbutton ("» %s «" % v if persistent.ritmo_velocidad == v else "Velocidad %s" % v) style "boton_vn_compacto" text_style "boton_vn_text" action SetField(persistent, "ritmo_velocidad", v)
        textbutton "CONTINUAR" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.reanudar) default_focus True
        textbutton "Abandonar el duelo" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.abandonar)
    key "civ_pausa" action Function(vista.reanudar)
    key "game_menu" action Function(vista.reanudar)

screen duelo_resultados(vista):
    $ d = vista.duelo
    $ res = d.resultado()
    use resultado_tarjeta(res["exito"], ("¡SEÑAL LIMPIA!" if res["exito"] else ("DUELO ABANDONADO" if res["abandonado"] else "NOVA SATURÓ LA SEÑAL")),
                          res["calificacion"], ("Precisión %d%%   ·   Mejor combo x%d" % (int(res["precision"] * 100), res["max_combo"])),
                          [(texto_juicio("perfect").strip("¡!").upper(), "%d" % d.conteo["perfect"], "#8c2f4b"),
                           (texto_juicio("good").upper(), "%d" % d.conteo["good"], "#2b2440"),
                           (texto_juicio("bad").upper(), "%d" % d.conteo["bad"], "#2b2440"),
                           (texto_juicio("miss").upper(), "%d" % d.conteo["miss"], "#d1495b" if d.conteo["miss"] else "#2b2440")],
                          valor=res)
    key "game_menu" action Return(res)

screen duelo_tutorial(modo):
    modal True
    zorder 46
    add "bg operaciones"
    add Solid("#120d1cd8")
    frame:
        align (0.5, 0.5)
        xsize 1180
        background Frame("gui/frame.png", 30, 30)
        padding (56, 40)
        has vbox
        spacing 14
        xfill True
        text "DUELO DE FRECUENCIAS" size 44 bold True color "#8c2f4b" xalign 0.5
        text "NOVA lanza una frase distorsionada. Tú respondes con la señal de Ciudad Nova: toca cada nota cuando llegue a su marca." size 22 color "#2b2440" xalign 0.5 text_align 0.5
        hbox:
            xalign 0.5
            spacing 26
            for k, (teclas, forma) in enumerate([("D · izquierda", "círculo"), ("F · abajo", "rombo"), ("J · arriba", "triángulo"), ("K · derecha", "cuadrado")]):
                vbox:
                    spacing 4
                    add "gui/ritmo/nota_%d.png" % k xalign 0.5
                    text teclas size 16 bold True color "#2b2440" xalign 0.5
                    text forma size 16 color "#5b4f72" xalign 0.5
        text "Teclado: D F J K   ·   Mando: cruceta (o X A Y RB)   ·   Pantalla táctil: toca el carril   ·   Pausa: Esc / Start" size 18 color "#5b4f72" xalign 0.5 text_align 0.5
        text "Pulsar sin nota no resta. Antes de empezar suenan ocho golpes de cuenta atrás." size 18 color "#5b4f72" xalign 0.5
        null height 6
        hbox:
            xalign 0.5
            spacing 20
            textbutton "Normal" style "boton_vn_compacto" text_style "boton_vn_text" action Return("normal") default_focus (not renpy.variant("touch"))
            textbutton "Fácil" style "boton_vn_compacto" text_style "boton_vn_text" action Return("facil") default_focus renpy.variant("touch")
            textbutton "Asistido" style "boton_vn_compacto" text_style "boton_vn_text" action Return("asistido")
            textbutton "Difícil" style "boton_vn_compacto" text_style "boton_vn_text" action Return("dificil")
        text "Asistido: menos notas y más margen para acertar. El duelo cuenta igual para la historia." size 16 italic True color "#8b84a8" xalign 0.5
        text "Difícil: cinco carriles con D · F · ESPACIO · J · K (mando: izquierda, abajo, A, arriba, derecha), canción propia a 144 BPM, ráfagas y notas dobles." size 16 italic True color "#8c2f4b" xalign 0.5 text_align 0.5


label minijuego_ritmo(modo="historia", aplicar=True, aliado=None, dificultad=None, **kwargs):
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    $ quick_menu_previo = quick_menu
    $ quick_menu = False
    window hide
    $ renpy.block_rollback()
    if dificultad is None:
        call screen duelo_tutorial(modo)
        $ dificultad_duelo = _return
    else:
        $ dificultad_duelo = dificultad   # Arena: todos el mismo chart, sin elegir
    $ duelo_competitivo_previo = duelo_competitivo
    if dificultad_duelo == "dificil":
        $ duelo_competitivo = True         # PERFECT / GREAT / GOOD / MISS
    $ vista_duelo = VistaDuelo(modo, dificultad_duelo)
    call screen duelo_pantalla(vista_duelo, aliado)
    $ duelo_competitivo = duelo_competitivo_previo
    $ resultado_duelo = dict(_return, dificultad=dificultad_duelo)
    $ renpy.music.stop(channel="ritmo", fadeout=0.6)
    $ quick_menu = quick_menu_previo
    if hud_estaba_visible:
        show screen hud_ciudad
    $ renpy.block_rollback()
    return registrar_minijuego(resultado_duelo, aplicar)
