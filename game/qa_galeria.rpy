## QA visual por etapas con el motor real: pantallas del sistema, escenas, CivitasNet/expediente y los cinco
## minijuegos jugados con entradas simuladas (mando) o jugadores automaticos. Inerte salvo con ALCALDE_QA=galeria.
##   ALCALDE_QA_ETAPA = menus | escenas | minijuegos | ritmo | finales     ALCALDE_QA_CAPTURAS = carpeta

init python:
    qa_gal = {"fotos": [], "eventos": []}

    def qa_gal_foto(nombre):
        qa_gal["fotos"].append(nombre)
        qa_captura(nombre)

    def qa_gal_volcar(**extra):
        qa_gal.update(extra)
        if qar_obs.get("muestras"):
            qa_gal["ritmo_muestras"] = qar_obs["muestras"]
        with open(QA_SALIDA, "w", encoding="utf-8") as f:
            _qam_json.dump({"galeria": qa_gal}, f, ensure_ascii=False, indent=1)

    def qa_gal_sim():
        s = renpy.get_screen("arcade_ui")
        return s.scope.get("sim") if s is not None else None

    def qa_gal_interceptar():
        sim = qa_gal_sim()
        if sim is not None and sim.jugando() and sim.paquetes:
            sim.interceptar(sim.paquetes[0])
            renpy.restart_interaction()

    def qa_gal_puzzle():
        s = renpy.get_screen("puzzle_rastreo_ui")
        return s.scope.get("p") if s is not None else None

    def qa_gal_puzzle_mal():
        p = qa_gal_puzzle()
        if p is None:
            return
        p.empezar()
        senuelos = [c for c in p.cartas if c not in p.solucion]
        cartas = (senuelos + list(p.solucion))[:p.eslabones]
        for i, c in enumerate(cartas):
            p.colocar(c, i)
        p.elegir_conclusion(p.opciones_conclusion[0])
        p.comprobar()
        renpy.restart_interaction()

    def qa_gal_puzzle_bien():
        p = qa_gal_puzzle()
        if p is None:
            return
        for i, c in enumerate(p.solucion):
            p.colocar(c, i)
        p.elegir_conclusion(p.tipo_origen())
        p.comprobar()
        if p.fase == "inferencia":
            for clave in p.opciones_inferencia:
                p.elegir_inferencia(clave) if hasattr(p, "elegir_inferencia") else None
                if p.inferencia_ok or not p.jugando():
                    break
        renpy.restart_interaction()

    def qa_gal_pasos_arcade(prefijo, ganar):
        pasos = [(1.5, "foto:%s_1_intro" % prefijo, None), (2.5, "a", "press"), (4.0, None, None),
                 (0.1, "foto:%s_2_juego" % prefijo, None)]
        if ganar:
            pasos += [(0.25, qa_gal_interceptar, None)] * 30
            pasos += [(0.1, "foto:%s_3_acierto" % prefijo, None)]
            pasos += [(0.25, qa_gal_interceptar, None)] * 80
        else:
            pasos += [(12.0, None, None), (0.1, "foto:%s_3_presion" % prefijo, None), (40.0, None, None)]
        return pasos

init python:
    def qa_gal_abandonar_duelo():
        s = renpy.get_screen("duelo_pantalla")
        if s is not None:
            s.scope["vista"].abandonar()

screen qa_gal_mirar_fin(nombre):
    zorder 1001
    timer 0.5 repeat True action If(qa_gal_sim() is not None and qa_gal_sim().terminado() and nombre not in qa_gal["fotos"],
                                    [Function(qa_gal_foto, nombre)])

label qa_galeria:
    # El QA arranca desde el splashscreen, donde Ren'Py desactiva historial y menu del juego: se restauran
    # como en una partida real.
    $ _history = True
    $ _game_menu_screen = "save"
    $ etapa_gal = _qa_os.environ.get("ALCALDE_QA_ETAPA", "menus")
    $ qa_pad_vigilante_hilo(500)
    $ qa_pad_limite = 450
    $ preparar_partida(feria=True)
    $ persistent.alias = "Vecina-2048"
    show screen qa_pad_inyector
    if etapa_gal == "menus":
        jump qa_gal_menus
    if etapa_gal == "escenas":
        jump qa_gal_escenas
    if etapa_gal == "minijuegos":
        jump qa_gal_minijuegos
    if etapa_gal == "ritmo":
        jump qa_gal_ritmo
    if etapa_gal == "finales":
        jump qa_gal_finales
    if etapa_gal == "dialogo":
        jump qa_gal_dialogo
    $ renpy.quit()

## ---------------- Pantallas del sistema ----------------
label qa_gal_menus:
    $ persistent.finales_vistos = set()
    scene bg despacho
    show claudia neutral at escena("claudia")
    # Texto instantaneo: con texto animado la primera A completa la linea y la segunda avanza.
    $ cps_previo = _preferences.text_cps
    $ _preferences.text_cps = 0
    $ qa_pad_programar([(1.0, "a", "press"), (1.0, "a", "press"), (1.0, "foto:m02_dialogo", None), (0.6, "a", "press")])
    c neutral "Alcalde. ¿Ya vio Civitas?"
    c seria "Una cuenta dice que el agua de Ciudad Nova está envenenada. Cuarenta mil reposts."
    c neutral "Claudia Reyes, de Noticias Nova. Esta semana trabajo con usted: alguien está fabricando miedo y quiero saber quién."
    $ _preferences.text_cps = cps_previo
    $ qa_gal["historial"] = [h.what[:40] for h in _history_list]
    $ renpy.show_screen("preferences")
    call qa_foto("m03_preferencias", 1.4)
    $ renpy.hide_screen("preferences")
    $ renpy.show_screen("save")
    call qa_foto("m04_guardar", 1.2)
    $ renpy.hide_screen("save")
    $ renpy.show_screen("load")
    call qa_foto("m05_cargar", 1.2)
    $ renpy.hide_screen("load")
    $ renpy.show_screen("history")
    call qa_foto("m06_historial", 1.2)
    $ renpy.hide_screen("history")
    $ renpy.show_screen("help")
    call qa_foto("m07_ayuda", 1.2)
    $ renpy.hide_screen("help")
    $ renpy.show_screen("about")
    call qa_foto("m08_creditos", 1.2)
    $ renpy.hide_screen("about")
    show screen confirm("¿Seguro que quieres salir?", NullAction(), NullAction())
    call qa_foto("m09_confirmar", 1.0)
    hide screen confirm
    hide claudia
    show screen archivo_destinos(None)
    call qa_foto("m10_archivo_vacio", 1.4)
    hide screen archivo_destinos
    $ persistent.finales_vistos = {"informada", "mandato"}
    show screen archivo_destinos("mandato")
    call qa_foto("m11_archivo_parcial", 1.6)
    hide screen archivo_destinos
    $ persistent.finales_vistos = set(destinos.FINALES)
    show screen archivo_destinos(None)
    call qa_foto("m12_archivo_completo", 1.6)
    hide screen archivo_destinos
    $ persistent.top_cache = {}
    $ persistent.mejor_local = {}
    show screen leaderboard_pantalla
    call qa_foto("m13_clasificacion_sin_conexion", 2.5)
    hide screen leaderboard_pantalla
    $ persistent.top_cache = {"historia": [
        {"rank": i + 1, "alias": a, "score": s, "final_title": t} for i, (a, s, t) in enumerate([
            ("Cronista-1180", 962, "Fuente Abierta"), ("Vecina-2048", 834, "Ciudad Informada"),
            ("Testigo-7731", 512, "Mandato Prestado"), ("Ciudadano-0042", 488, "Ciudad Dividida"),
            ("Lector-9001", 301, "Ciudad en Caos")])]}
    $ persistent.mejor_local = {"historia": {"score": 834, "final": "informada"}}
    show screen leaderboard_pantalla
    call qa_foto("m14_clasificacion", 2.5)
    hide screen leaderboard_pantalla
    show screen elegir_alias
    call qa_foto("m15_alias", 1.2)
    hide screen elegir_alias
    show screen ayuda_mando
    call qa_foto("m16_ayuda_mando", 1.2)
    hide screen ayuda_mando
    ## Al final: el menu principal nunca se muestra dentro de una partida en el juego real.
    show screen main_menu
    call qa_foto("m01_menu_principal", 2.0)
    hide screen main_menu
    $ qa_gal_volcar(etapa="menus", ok=True)
    $ renpy.quit()

## ---------------- Escenas, telefono, CivitasNet, expediente, mapa ----------------
label qa_gal_escenas:
    show screen titulo_acto("ACTO II  -  MIÉRCOLES", "El Barrio Sur", "Un rumor no necesita ser cierto. Solo necesita ser rápido.")
    call qa_foto("e01_titulo_acto", 1.6)
    hide screen titulo_acto
    scene bg barrio_sur at paneo
    show screen tarjeta_lugar("MIÉRCOLES  -  10:20 A.M.", "Barrio Sur")
    call qa_foto("e02_barrio_establecimiento", 1.4)
    scene bg barrio_sur conversacion
    show screen hud_ciudad
    show rodrigo enojada at escena("rodrigo")
    show screen qa_disparo("e03_barrio_conversacion", 1.0)
    r enojada "¡Alcalde! Todo el barrio dice que mañana cierran el hospital.{w=1.5}{nw}"
    hide screen qa_disparo
    hide screen tarjeta_lugar
    scene bg crisis
    show nova feliz at escena("nova", 0.78)
    show claudia triste at escena("claudia", 0.22)
    show screen qa_disparo("e04_crisis_dos_personajes", 1.0)
    n feliz "{cps=0}Todas las cuentas despiertan al mismo tiempo.{/cps}{w=1.5}{nw}"
    hide screen qa_disparo
    hide nova
    hide claudia
    scene bg operaciones
    $ sesion_gal = SesionPublicacion(banco.siguiente())
    show screen telefono_civitas(sesion=sesion_gal)
    call qa_foto("e05_telefono_publicacion", 1.6)
    hide screen telefono_civitas
    $ sesion_gal.elegir(1)
    show screen telefono_civitas(sesion=sesion_gal)
    call qa_foto("e06_telefono_verificar", 1.4)
    hide screen telefono_civitas
    show screen civitasnet()
    call qa_foto("e07_civitasnet_lunes", 1.6)
    hide screen civitasnet
    $ store.inv_mem_vacia = dict(mem()["pistas"])
    $ mem()["pistas"].clear()
    show screen expediente
    call qa_foto("e08_expediente_vacio", 1.4)
    hide screen expediente
    $ avanzar_momento(inv.MIERCOLES)
    $ [dar_pista(p, aviso=False) for p in list(inv.PISTAS)[:4]]
    show screen expediente
    call qa_foto("e09_expediente_parcial", 1.4)
    hide screen expediente
    $ avanzar_momento(inv.VIERNES)
    $ avanzar_momento(inv.DOMINGO)
    $ [dar_pista(p, aviso=False) for p in inv.PISTAS]
    show screen expediente
    call qa_foto("e10_expediente_completo", 1.4)
    hide screen expediente
    show screen civitasnet(llamada=True, destacar="net_audio_tomas")
    call qa_foto("e11_civitasnet_domingo", 1.6)
    hide screen civitasnet
    show screen misiones_ciudad
    call qa_foto("e12_misiones", 1.4)
    hide screen misiones_ciudad
    $ renpy.notify("Nueva pista: El audio de Tomás Vega")
    call qa_foto("e13_notificacion", 0.6)
    show screen mapa_viaje("barrio_sur")
    call qa_foto("e14_mapa_viaje", 2.0)
    $ qa_pad_programar([(0.2, "dpright", "press"), (1.5, "dpright", "release"), (0.1, "dpdown", "press"), (1.0, "dpdown", "release")])
    call qa_foto("e15_mapa_conduciendo", 2.8)
    hide screen mapa_viaje
    $ qa_gal_volcar(etapa="escenas", ok=True)
    $ renpy.quit()

## ---------------- Minijuegos 1-4 ----------------
label qa_gal_minijuegos:
    scene bg operaciones
    ## Moderacion: alterna borrar/aprobar para ver acierto y error.
    $ qa_pad_programar([(1.5, "foto:j01_moderador_inicio", None), (1.0, "dpleft", "press"), (0.25, "foto:j02_moderador_feedback_a", None),
                        (1.2, "dpright", "press"), (0.25, "foto:j03_moderador_feedback_b", None)]
                       + [(0.9, ("dpleft" if i % 2 else "dpright"), "press") for i in range(8)]
                       + [(1.2, "foto:j04_moderador_resultado", None)] + qa_pad_repetir("a", 30, 1.0))
    call minijuego_moderador(aplicar=False, cantidad=6)
    $ qa_gal["eventos"].append(("moderador", _return.get("exito"), _return.get("calificacion")))
    ## Caza-Rumores: victoria con jugador automatico.
    show screen qa_gal_mirar_fin("j08_contencion_resultado_victoria")
    $ qa_pad_programar(qa_gal_pasos_arcade("j05_contencion", True) + qa_pad_repetir("a", 60, 1.0))
    call minijuego_contencion(aplicar=False, ajustes={"duracion": 20.0})
    hide screen qa_gal_mirar_fin
    $ qa_gal["eventos"].append(("contencion", _return.get("exito"), _return.get("calificacion")))
    ## Gran Viralizacion: derrota (sin interceptar).
    show screen qa_gal_mirar_fin("j12_viral_resultado_derrota")
    $ qa_pad_programar(qa_gal_pasos_arcade("j09_viral", False) + qa_pad_repetir("a", 60, 1.0))
    call evento_gran_viralizacion(aplicar=False, ajustes={"duracion": 20.0})
    hide screen qa_gal_mirar_fin
    $ qa_gal["eventos"].append(("viralizacion", _return.get("exito"), _return.get("calificacion")))
    ## Rastreador: tutorial, error con explicacion y victoria.
    $ qa_pad_programar([(1.5, "foto:j13_rastreador_tutorial", None), (0.5, qa_gal_puzzle_mal, None),
                        (1.0, "foto:j14_rastreador_error", None), (0.5, qa_gal_puzzle_bien, None),
                        (1.2, "foto:j15_rastreador_siguiente", None), (0.5, qa_gal_puzzle_bien, None),
                        (1.5, "foto:j16_rastreador_resultado", None)] + qa_pad_repetir("a", 40, 1.0))
    call minijuego_rastreador(aplicar=False, ajustes=FERIA_RASTREO)
    $ qa_gal["eventos"].append(("rastreador", _return.get("exito"), _return.get("calificacion")))
    $ qa_gal_volcar(etapa="minijuegos", ok=True)
    $ renpy.quit()

## ---------------- Duelo de Frecuencias ----------------
label qa_gal_ritmo:
    $ perfil_qar = _qa_os.environ.get("ALCALDE_QA_PASOS", "perfecto")
    $ qar_instalar("nada" if perfil_qar == "nada" else "perfecto")
    scene bg operaciones
    $ p_ = "r_%s_" % perfil_qar
    $ salida_pausa = [(0.5, qa_gal_abandonar_duelo, None), (1.5, "foto:%s06_resultados" % p_, None)] if perfil_qar == "abandonar" else [
        (0.5, "a", "press"), (6.0, "foto:%s05_juego_combo" % p_, None), (40.0, None, None), (1.0, "foto:%s06_resultados" % p_, None)]
    $ qa_pad_programar([(1.5, "foto:%s01_tutorial" % p_, None), (0.5, "a", "press"), (1.2, "foto:%s02_cuenta_atras" % p_, None),
                        (9.0, "foto:%s03_juego" % p_, None), (0.3, "start", "press"), (1.0, "foto:%s04_pausa" % p_, None)]
                       + salida_pausa + qa_pad_repetir("a", 20, 1.0))
    call minijuego_ritmo(modo="feria", aplicar=False, aliado="claudia")
    $ qa_gal["eventos"].append(("ritmo", _return.get("exito"), _return.get("calificacion"), _return.get("precision")))
    $ qa_gal_volcar(etapa="ritmo", ok=True)
    $ renpy.quit()

## ---------------- Pantallas de final ----------------
label qa_gal_finales:
    $ resultado_qa = {"verificacion": 260, "decisiones": 210, "minijuegos": 170, "investigacion": 120, "ciudad": 74, "total": 834}
    $ registro_minijuegos.update({"moderador": {"exito": True, "calificacion": "S"}, "contencion": {"exito": True, "calificacion": "A"},
                                  "rastreador": {"exito": True, "calificacion": "B"}, "viralizacion": {"exito": False, "calificacion": "D"},
                                  "ritmo": {"exito": True, "calificacion": "A"}})
    $ modo_feria_activo = True
    $ envios_gal = [("ok", "Puesto 3 en la clasificación (Vecina-2048)"),
                    ("pendiente", "Sin conexión con la clasificación. Lo enviaremos en tu próxima partida."),
                    ("pendiente", "Resultado guardado como no verificado: no entra en la tabla pública."),
                    ("error", "El servidor no aceptó este resultado."),
                    ("local", "Clasificación online no configurada. Tu récord se guardó en este equipo.")]
    $ i_gal = 0
    while i_gal < len(destinos.FINALES):
        $ final_gal = destinos.FINALES[i_gal]
        $ estado_envio = envios_gal[i_gal]
        show screen pantalla_resultados(final_gal, resultado_qa, i_gal % 2 == 0)
        call qa_foto("f%02d_resultados_%s" % (i_gal + 1, final_gal), 2.4)
        hide screen pantalla_resultados
        $ i_gal += 1
    $ qa_gal_volcar(etapa="finales", ok=True)
    $ renpy.quit()

## ---------------- Avance de dialogo con A (narrador y personaje) ----------------
label qa_gal_dialogo:
    $ qa_pad_vigilante_hilo(60)
    scene bg despacho
    $ variante_dlg = _qa_os.environ.get("ALCALDE_QA_PASOS", "")
    if variante_dlg == "w":
        ## Como el prologo: pausas {w} dentro de la linea; A salta cada pausa y luego avanza.
        $ qa_pad_programar([(1.0, "a", "press")] * 6)
        c "Una cuenta dice que el agua está envenenada.{w=0.4} Cuarenta mil reposts.{w=0.4} En una hora."
        $ qa_gal["eventos"].append("w_ok")
    elif variante_dlg == "nw":
        c neutral "Línea que se cierra sola.{w=0.3}{nw}"
        $ qa_gal["eventos"].append("nw_ok")
    $ qa_pad_programar([(1.5, "a", "press"), (1.5, "a", "press"), (1.5, "a", "press")])
    "Línea de narración: A debe avanzar."
    $ qa_gal["eventos"].append("narrador_ok")
    $ qa_gal_volcar(etapa="dialogo")
    show claudia neutral at escena("claudia")
    c neutral "Línea de Claudia: A debe avanzar."
    $ qa_gal["eventos"].append("claudia_ok")
    $ qa_gal["historial"] = [h.what[:40] for h in _history_list]
    $ qa_gal["diag"] = {"_history": _history, "contextos": len(renpy.game.contexts), "history_length": config.history_length,
                        "label_cb": str(config.history_callbacks)[:200]}
    $ qa_gal_volcar(etapa="dialogo", ok=True)
    $ renpy.quit()
