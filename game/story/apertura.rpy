## Apertura «Ciudad Nova en crisis» (Feria Gamer): la ciudad despierta, una decision inmediata, la propagacion
## real del rumor en el grafo de Civitas, Claudia y una microprueba de Moderacion Express antes del titulo.
## La usan Historia y Modo Feria desde story/prologo.rpy. Las consecuencias del prologo se aplican una sola vez.

default apertura_decision = None
default apertura_micro = None
default apertura_tiempos = {}

init python:
    import time as _apertura_time
    from clases.Publicacion import Publicacion

    # Lo que cada respuesta hace con el rumor dentro del grafo (ver apertura_propagacion):
    # - desmentir: quienes siguen a la alcaldia leen el desmentido y no lo reenvian (vecinos bloqueados);
    # - analisis: los medios esperan los datos antes de repetir nada, pero el rumor sigue corriendo;
    # - ignorar: sin respuesta, cada cuenta lo reenvia con mas fuerza.
    APERTURA_SEMILLA = "apertura"
    APERTURA_ORIGEN = "@verdad.oculta"
    APERTURA_MEDIOS = ("@salud.nova", "@investigador.nova", "@noticias.nova")
    APERTURA_RESPUESTA = {
        "desmentir": {"titulo": "Desmentiste sin datos", "consecuencia": {"confianza": 2, "info_verificada": -2},
                      "texto": "Tus seguidores lo leen y frenan el rumor. Pero el desmentido no tiene ningún análisis detrás.",
                      "voz": ("@vecina.ana", "La alcaldía dice que es 100% segura. ¿Con qué análisis?")},
        "analisis": {"titulo": "Pediste los análisis", "consecuencia": {"info_verificada": 3, "desinformacion": 2},
                     "texto": "Los medios esperan los datos antes de repetir nada. Mientras tanto, el rumor sigue corriendo.",
                     "voz": ("@noticias.nova", "La alcaldía pidió los análisis del agua. Informaremos con datos.")},
        "ignorar": {"titulo": "No interviniste", "consecuencia": {"desinformacion": 4, "confianza": -2},
                    "texto": "Sin una respuesta de la alcaldía, cada cuenta lo reenvía con más fuerza.",
                    "voz": ("@preocupado99", "¿Y el alcalde? ¿Nadie va a decir nada? Yo ya no tomo agua.")},
    }

    # Comentarios propios de la microprueba: no estan en el banco de Moderacion Express (no se repiten luego).
    COMENTARIOS_APERTURA = [
        ("@aguasegura_YA_77", "NO TOMEN AGUA DEL GRIFO. La alcaldía lo sabía desde ayer. COMPARTE", True),
        ("@rosa.del.sur", "Mi bebé toma tetero con agua de la llave. ¿Alguien sabe algo oficial?", False),
        ("@despierta_nova_x", "#AguaEnvenenada #AguaEnvenenada #AguaEnvenenada RT RT RT", True),
        ("@hector.taxi", "Alcalde, usted nunca responde a tiempo. Esta vez dé la cara.", False),
    ]

    def apertura_marca(nombre):
        """Tiempos de la apertura (segundos desde que empieza). Sin datos personales."""
        t = _apertura_time.time()
        if "_t0" not in store.apertura_tiempos or nombre == "inicio":
            store.apertura_tiempos = {"_t0": t}
        store.apertura_tiempos[nombre] = round(t - store.apertura_tiempos["_t0"], 1)

    def apertura_propagacion(eleccion):
        """BFS real sobre red_civitas desde la cuenta que inventa el rumor; depende de la respuesta del jugador."""
        red = store.red_civitas
        if eleccion == "desmentir":
            bloqueados, factor = set(red.vecinos("jugador")), 1.0
        elif eleccion == "analisis":
            bloqueados, factor = set(APERTURA_MEDIOS), 1.0
        else:
            bloqueados, factor = set(), 1.35
        padres = {}
        niveles = red.bfs_propagacion(APERTURA_ORIGEN, semilla=APERTURA_SEMILLA, factor=factor,
                                      bloqueados=bloqueados, padres=padres)
        return niveles, padres, bloqueados

    def apertura_decidir(eleccion):
        """Aplica la decision del prologo una sola vez (rollback y reintentos no la repiten)."""
        if store.apertura_decision is not None:
            return False
        store.apertura_decision = eleccion
        if eleccion == "desmentir":
            hecho("desmintio_sin_datos")
            calidad_decision("prologo_agua", 0.4)
        elif eleccion == "analisis":
            hecho("pidio_analisis")
            calidad_decision("prologo_agua", 1.0)
            subir_afinidad("claudia", 1)
        else:
            hecho("ignoro_rumor_agua")
            calidad_decision("prologo_agua", 0.0)
            subir_afinidad("claudia", -1)
        aplicar_consecuencia(APERTURA_RESPUESTA[eleccion]["consecuencia"])
        return True

    def apertura_micro_resultado(cola):
        """Consecuencia de la microprueba: una vez, y sin tocar el registro del Moderacion Express completo."""
        if store.apertura_micro is not None:
            return store.apertura_micro
        censuro = any(eliminar and not p.es_falsa for p, eliminar, _ok in cola.historial)
        bots_quedaron = any((not eliminar) and p.es_falsa for p, eliminar, _ok in cola.historial)
        decididos = len(cola.historial)
        if decididos == 0:
            r = "sin_jugar"
        elif censuro:
            r = "censuro"
            aplicar_consecuencia({"convivencia": -1})
        elif bots_quedaron:
            r = "bots"
            aplicar_consecuencia({"desinformacion": 1})
        else:
            r = "limpio"
            aplicar_consecuencia({"confianza": 1})
        store.apertura_micro = r
        return r


transform apertura_entra(retraso):
    alpha 0.0 yoffset (0 if persistent.reducir_movimiento else 26)
    pause retraso
    easein 0.32 alpha 1.0 yoffset 0

transform apertura_vibra(retraso):
    alpha 0.0
    pause retraso
    alpha 1.0
    block:
        xoffset 0
        linear 0.05 xoffset (0 if persistent.reducir_movimiento else 6)
        linear 0.05 xoffset (0 if persistent.reducir_movimiento else -6)
        linear 0.05 xoffset 0
        pause 1.1
        repeat 3

transform apertura_titular(retraso):
    alpha 0.0 zoom (1.0 if persistent.reducir_movimiento else 1.12)
    pause retraso
    easein 0.35 alpha 1.0 zoom 1.0

transform apertura_fondo:
    alpha 0.0
    linear 2.4 alpha 0.55

## ---------------- A. La ciudad despierta ----------------
## Coreografia de ~9 s. Clic, Enter o «Saltar» la terminan; termina sola si nadie toca nada.
screen apertura_montaje():
    modal True
    add Solid("#07050c")
    add "bg ciudad noche" at apertura_fondo
    add Solid("#07050c99")

    text "LUNES  ·  6:09 A.M." size 22 bold True color "#e86a7e" kerning 6 pos (80, 60) at apertura_entra(0.2)
    hbox at apertura_vibra(0.3):
        pos (80, 100)
        spacing 12
        text "BZZZ" size 30 bold True color "#c9b8d8"
        text "Tu teléfono no deja de vibrar." size 26 color "#c9b8d8" yalign 0.5

    vbox:
        pos (80, 190)
        spacing 14
        for i, (quien, texto, color, t) in enumerate([
                ("CIVITAS · @verdad.oculta", "URGENTE: el agua de Ciudad Nova está contaminada. No la tomen.", "#e86a7e", 0.9),
                ("CIVITAS · @noticias.nova", "Estamos verificando. Por ahora no hay ningún dato oficial.", "#5eead4", 1.9),
                ("CIVITAS · @vecina.ana", "Alcalde, ¿qué está pasando? Mis hijos van al colegio en una hora.", "#a7a5f2", 3.6),
                ("CIVITAS · Tendencia", "#AguaEnvenenada  ·  18.900 reposts en una hora", "#facc15", 4.6),
            ]):
            frame at apertura_entra(t):
                background Frame(Solid("#fbf6eeee"), 0, 0)
                padding (24, 12)
                xsize 820
                vbox:
                    spacing 2
                    text quien size 17 bold True color color
                    text texto size 24 color "#2b2440"

    vbox at apertura_titular(2.7):
        pos (980, 300)
        xsize 860
        spacing 10
        text "¿EL AGUA ESTÁ ENVENENADA?" size 58 bold True color "#fbf6ee" outlines [(3, "#8c2f4b", 0, 0)]
        text "Miles de personas comparten la noticia. Nadie sabe de dónde salió." size 28 color "#f4b6c2"

    frame at apertura_entra(5.8):
        pos (980, 560)
        background Frame(Solid("#8c2f4bdd"), 0, 0)
        padding (24, 14)
        hbox:
            spacing 14
            text "3" size 46 bold True color "#fbf6ee" yalign 0.5
            vbox:
                text "LLAMADAS PERDIDAS" size 18 bold True color "#f4b6c2" kerning 3
                text "Claudia Reyes · Noticias Nova" size 26 bold True color "#fbf6ee"

    text "Ciudad Nova elige alcalde en seis días. Y el alcalde eres tú." size 30 bold True color "#fbf6ee" pos (980, 700) at apertura_entra(7.0)
    text "Clic o Enter para responder" size 22 color "#c9b8d8" pos (980, 760) at apertura_entra(7.8)

    textbutton "Saltar ›" style "arena_link_claro" xalign 0.98 yalign 0.97 action Return()
    timer 11.0 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()
    timer 0.35 action Function(sfx, "notificacion")
    timer 2.7 action Function(sfx, "alarma")

## ---------------- B. Una decision inmediata ----------------
## Se usa como pantalla del menu (menu (screen="apertura_decision")): las opciones son las del menu real,
## asi las respetan el guardado, el rollback y los recorridos automaticos.
screen apertura_decision(items):
    modal True
    default ver_fuente = False
    add "bg civitas"
    add Solid("#120d1cd9")

    text "TU PRIMERA DECISIÓN COMO ALCALDE  ·  TODA LA CIUDAD ESTÁ MIRANDO" size 20 bold True color "#e86a7e" kerning 3 xalign 0.5 ypos 40

    frame:
        xalign 0.5
        ypos 90
        xsize 1180
        background Frame(Solid("#fbf6ee"), 0, 0)
        padding (40, 28)
        vbox:
            spacing 10
            hbox:
                spacing 14
                add circulo("#3a3350", "#e86a7e", 24) yalign 0.5
                vbox:
                    text "@verdad.oculta" size 24 bold True color "#2b2440"
                    text "Civitas · hace 58 min" size 18 color "#8b84a8"
            text "El agua de Ciudad Nova podría estar contaminada. Miles de personas están compartiendo la noticia." size 34 bold True color "#2b2440"
            text "URGENTE: el Acueducto CONFIRMA que el agua está contaminada. No la tomen. #AntesDeQueLoBorren" size 24 color "#5b4f72"
            hbox:
                spacing 40
                text "40.210 me gusta" size 20 color "#8c2f4b" bold True
                text "18.900 reposts" size 20 color "#8c2f4b" bold True
                text "Subiendo" size 20 color "#c0392b" bold True
            if ver_fuente:
                frame:
                    background Frame(Solid("#f3eefe"), 0, 0)
                    padding (18, 10)
                    xfill True
                    vbox:
                        spacing 4
                        text "Fuente: una captura sin enlace ni fecha." size 21 bold True color "#2b2440"
                        text "La captura está cortada justo debajo del título. La cuenta no tiene foto." size 21 color "#5b4f72"
            else:
                textbutton "Ver de dónde salió" style "arena_link" action [SetScreenVariable("ver_fuente", True), Function(dar_pista, "captura_veneno")]

    vbox:
        xalign 0.5
        ypos 590
        spacing 16
        for i, item in enumerate(items):
            textbutton item.caption style "apertura_opcion" text_style "apertura_opcion_texto" action item.action at opcion_entrada(i * 0.07) default_focus (i == 0)

style apertura_opcion is default:
    background Frame(Solid("#fbf6ee"), 0, 0)
    hover_background Frame(Solid("#e9e1f3"), 0, 0)
    xsize 900
    padding (30, 18)
    hover_sound "assets/audio/sfx/menu_hover.ogg"
    activate_sound "assets/audio/sfx/decision.ogg"
style apertura_opcion_texto is default:
    size 28
    bold True
    color "#2b2440"
    hover_color "#8c2f4b"
    xalign 0.5

## ---------------- C. La ciudad reacciona ----------------
## Dibuja el BFS real (niveles y padres) nivel por nivel. Clic: muestra todo; segundo clic: continuar.
screen apertura_reaccion(eleccion, niveles, padres, bloqueados):
    modal True
    default paso = (len(niveles) if persistent.reducir_movimiento else 1)
    $ red = red_civitas
    $ pos = posiciones_grafo(red)
    $ estados, efectos, subtitulos, resaltadas = vista_bfs(red, niveles, padres, paso, "infectado")
    $ terminado = paso >= len(niveles)
    $ alcanzados = sum(len(n) for n in niveles[:paso]) - (1 if niveles else 0)
    $ resp = APERTURA_RESPUESTA[eleccion]
    for b in bloqueados:
        $ estados[b] = "contenido"

    add FONDO_CONTENCION
    use grafo_red(red, pos, estados, efectos, {}, resaltadas, {})

    text "CIVITASNET · ASÍ CORRE EL RUMOR" size 30 bold True color "#fbf6ee" pos (40, 40) outlines [(2, "#1b1426", 0, 0)]

    frame:
        style_prefix "grafo"
        xpos 1270
        ypos 130
        xsize 620
        vbox:
            text resp["titulo"].upper() size 28 color "#facc15" bold True
            text resp["texto"] size 21 color "#e2e8f0"
            null height 8
            text "Cuentas alcanzadas" size 18 color "#94a3b8"
            text "%d de %d" % (alcanzados, red.cantidad_nodos() - 1) size 52 bold True color ("#fb7185" if alcanzados > 18 else "#fbbf24")
            text "%d saltos desde @verdad.oculta" % max(0, min(paso, len(niveles)) - 1) size 20 color "#cbd5e1"
            if bloqueados:
                text "En azul: cuentas que no lo reenviaron por tu respuesta." size 18 color "#7dd3fc"
            null height 6
            frame:
                background Frame(Solid("#fbf6eeee"), 0, 0)
                padding (16, 10)
                xfill True
                vbox:
                    text resp["voz"][0] size 17 bold True color "#8c2f4b"
                    text resp["voz"][1] size 21 color "#2b2440"
            if terminado:
                null height 8
                text "Ciudad Nova" size 18 color "#94a3b8"
                for k, v in resp["consecuencia"].items():
                    $ bueno = (v > 0) != (k in INDICADOR_NEGATIVO)
                    text "%s %+d" % (NOMBRES_INDICADOR[k], v) size 24 bold True color ("#5eead4" if bueno else "#fb7185")
                null height 8
                textbutton "Continuar" action Return() default_focus True

    if not terminado:
        timer 0.55 repeat True action [SetScreenVariable("paso", paso + 1), Function(sonar_nodo)]
        key "dismiss" action SetScreenVariable("paso", len(niveles))
        key "civ_accion" action SetScreenVariable("paso", len(niveles))
    else:
        key "civ_accion" action Return()

## ---------------- F. Titulo ----------------
transform apertura_logo:
    alpha 0.0 zoom (1.0 if persistent.reducir_movimiento else 1.25)
    easein 0.5 alpha 1.0 zoom 1.0

screen apertura_titulo():
    modal True
    add Solid("#120d1c")
    add "bg ciudad" at apertura_fondo
    add Solid("#120d1cbb")
    vbox:
        align (0.5, 0.46)
        spacing 6
        text "CIVITAS" size 150 bold True color "#fbf6ee" xalign 0.5 kerning 18 outlines [(5, "#8c2f4b", 0, 0)] at apertura_logo
        text "ALCALDE DIGITAL" size 44 bold True color "#e86a7e" xalign 0.5 kerning 12 at apertura_entra(0.45)
        null height 18
        text "«Cada publicación cambia la ciudad»" size 32 color "#c9b8d8" xalign 0.5 at apertura_entra(0.9)
    timer 3.4 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()


## ---------------- E. Microprueba de Moderacion Express ----------------
## El mismo motor y la misma pantalla del minijuego (ColaModeracion + moderador_ui), con 4 comentarios
## propios y sin tocar registro_minijuegos (el reto completo del lunes puntua aparte).
label apertura_microprueba:
    $ comentarios_ap = [Publicacion(a, t, bot, 0, None) for a, t, bot in COMENTARIOS_APERTURA]
    $ creadas_ap = {"@aguasegura_YA_77": "hace 2 días", "@rosa.del.sur": "2018", "@despierta_nova_x": "ayer", "@hector.taxi": "2016"}
    $ moderacion_ap = ColaModeracion(comentarios_ap, tiempo_por_tarjeta=6.0, cuenta_regresiva=1.5)
    $ ocultar_avisos_juego()
    window hide
    $ apertura_marca("microprueba")
    call screen moderador_ui(moderacion_ap, creadas_ap)
    hide screen moderador_feedback
    $ renpy.block_rollback()
    return apertura_micro_resultado(moderacion_ap)
