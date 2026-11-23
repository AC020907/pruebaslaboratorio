## QA de Central de Emergencias (ALCALDE_QA=galeria, ALCALDE_QA_ETAPA=central). Motor real de Ren'Py:
## 1) Historia: la fase 1 se juega con CLICS sobre el mapa (VistaCentral.clic_mapa, la misma funcion que el raton):
##    ambulancia -> emergencia -> rutas A/B -> se elige B. Despues termina el turno el despachador automatico
##    (mismas ordenes que una persona). Se fotografian las rutas, el bloqueo, el desvio, las fases, la zona aislada,
##    la eleccion de hospital y el resultado.
## 2) Feria: turno completo con el despachador automatico (habilidad 0,6) para medir resultado y FPS.

init python:
    qa_ce = {"hechas": [], "paso": 0, "t_paso": 0.0, "eventos": []}

    def qa_ce_foto(nombre):
        if nombre not in qa_ce["hechas"]:
            qa_ce["hechas"].append(nombre)
            qa_gal_foto(nombre)

    def qa_ce_tick():
        import time as _t
        ahora = _t.time()
        if renpy.get_screen("central_intro"):
            if qa_ce.get("intro_desde") is None:
                qa_ce["intro_desde"] = ahora
            elif ahora - qa_ce["intro_desde"] > 1.2:
                qa_ce_foto("ce00_intro_%s" % qa_ce["modo"])
                qa_ce["intro_desde"] = None
                return True
            return None
        s = renpy.get_screen("central_ui")
        if s is None:
            return None
        v = s.scope["vista"]
        p = v.p
        # Duracion efectiva: reloj de pared desde el primer tick con control hasta el fin del turno.
        clave_t0, clave_t1 = "t0_" + qa_ce["modo"], "t1_" + qa_ce["modo"]
        if p.tick > 0 and clave_t0 not in qa_ce:
            qa_ce[clave_t0] = ahora - p.tick / float(CE.TICKS_S)
        if not p.jugando() and clave_t1 not in qa_ce:
            qa_ce[clave_t1] = ahora
            qa_ce["ticks_" + qa_ce["modo"]] = p.tick
        if p.jugando() and 2 * CE.TICKS_S < p.fin_tick - p.tick < 4 * CE.TICKS_S:
            qa_ce_foto("ce13_ultimos_5_%s" % qa_ce["modo"])
        if v.resultado_listo() and "res_visible_" + qa_ce["modo"] not in qa_ce and clave_t1 in qa_ce:
            qa_ce["res_visible_" + qa_ce["modo"]] = round(ahora - qa_ce[clave_t1], 2)
        if v.resultado_listo():
            if qa_ce.get("res_desde") is None:
                qa_ce["res_desde"] = ahora
            elif ahora - qa_ce["res_desde"] > 1.6:
                qa_ce_foto("ce11_resultado_%s" % qa_ce["modo"])
                qa_ce["res_desde"] = None
                qa_ce["fps_%s" % qa_ce["modo"]] = v.fps()
                return True
            return None
        if qa_ce["modo"] != "historia":
            if p.fase == 3 and p.tick % 300 < 3:
                qa_ce_foto("ce20_feria_crisis")
            return None
        # --- Fase 1 jugada con clics ---
        paso = qa_ce["paso"]
        if paso == 0 and p.emergencias and v.cuenta <= 0 and p.tick > 45:
            qa_ce_foto("ce01_tutorial_ambulancia")
            x, y, _g = v.pos_amb(p.ambulancias[0])
            qa_ce["eventos"].append(("clic_ambulancia", v.clic_mapa(x, y), v.sel))
            qa_ce["paso"], qa_ce["t_paso"] = 1, ahora
        elif paso == 1 and ahora - qa_ce["t_paso"] > 0.8:
            qa_ce_foto("ce02_tutorial_emergencia")
            e = p.emergencias[0]
            x, y, _b = CE.NODOS[e.nodo]
            qa_ce["eventos"].append(("clic_emergencia", v.clic_mapa(x, y), len(v.opciones)))
            qa_ce["paso"], qa_ce["t_paso"] = 2, ahora
        elif paso == 2 and ahora - qa_ce["t_paso"] > 1.0:
            qa_ce_foto("ce03_rutas_a_b")
            opcion = 1 if len(v.opciones) > 1 else 0
            qa_ce["eventos"].append(("ruta_elegida", "AB"[opcion], [o[0] for o in v.opciones]))
            v.confirmar(opcion)
            qa_ce["paso"], qa_ce["t_paso"] = 3, ahora
        elif paso == 3 and ahora - qa_ce["t_paso"] > 1.5:
            qa_ce_foto("ce04_en_ruta")
            v.piloto = CE.Despachador(__import__("random").Random(3), 1.0)
            qa_ce["paso"] = 4
        if any(p.g.bloqueada):
            qa_ce_foto("ce05_bloqueo")
        if any(a.estado == "detenida" or a.bloqueo_avisado for a in p.ambulancias):
            qa_ce_foto("ce06_ruta_cortada")
        if v.banner and v.banner[0] == "Fase 2" and v.st - v.banner[2] > 0.8:
            qa_ce_foto("ce07_fase2")
        if v.banner and v.banner[0] == "Fase 3" and v.st - v.banner[2] > 0.8:
            qa_ce_foto("ce08_fase3")
        if p.g.aislados():
            qa_ce_foto("ce09_zona_aislada")
        if any(a.estado == "esperando_hospital" for a in p.ambulancias) and p.fase >= 2:
            qa_ce_foto("ce10_elegir_hospital")
        if p.fase == 3 and sum(1 for e in p.emergencias if e.estado in ("espera", "asignada", "atendiendo", "traslado")) >= 3:
            qa_ce_foto("ce12_crisis_varias")
        return None

screen qa_central_auto():
    zorder 1001
    timer 0.05 repeat True action Function(qa_ce_tick)

label qa_gal_central:
    hide screen qa_pad_inyector
    show screen qa_central_auto
    $ qa_ce["modo"] = "historia"
    $ qa_central_auto = None
    call minijuego_central("historia", 7, False, True, True)
    $ qa_gal["eventos"].append(("central_historia", _return["exito"], _return["calificacion"], _return["a_tiempo"],
                                _return["total"], _return["desvios"], _return["recursos"], qa_ce.get("fps_historia")))
    $ qa_ce["modo"] = "feria"
    $ qa_central_auto = 0.6
    call minijuego_central("feria", 21, False, True, True)
    $ qa_central_auto = None
    $ qa_gal["eventos"].append(("central_feria", _return["exito"], _return["calificacion"], _return["a_tiempo"],
                                _return["total"], _return["desvios"], _return["recursos"], qa_ce.get("fps_feria")))
    python:
        for _m in ("historia", "feria"):
            qa_gal["eventos"].append(("duracion_" + _m, qa_ce.get("ticks_" + _m),
                                      round(qa_ce.get("t1_" + _m, 0) - qa_ce.get("t0_" + _m, 0), 2), qa_ce.get("res_visible_" + _m)))
    $ qa_gal["eventos"].extend(qa_ce["eventos"])
    $ qa_gal_volcar(etapa="central", ok=True)
    $ renpy.quit()
