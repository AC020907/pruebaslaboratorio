## QA de la Ruta de la Verdad 2 (ALCALDE_QA=galeria, ALCALDE_QA_ETAPA=ruta). Motor real de Ren'Py:
## juega el nivel Historia entero con la ruta verificada (PilotoRuta: las mismas teclas, tick a tick, que una
## persona perfecta) y fotografia la presentacion, una serie cada 2 s, el primer impulso, un escaner encendido
## cerca, el cartel de cada zona, la victoria y el resultado. Mide los FPS del render.

init python:
    qa_rt = {"hechas": [], "desde": None, "serie": -1, "eventos": []}

    def qa_rt_foto(nombre):
        if nombre not in qa_rt["hechas"]:
            qa_rt["hechas"].append(nombre)
            qa_gal_foto(nombre)

    def qa_rt_tick():
        import time as _t
        ahora = _t.time()
        if renpy.get_screen("plataformas_tutorial"):
            if qa_rt["desde"] is None:
                qa_rt["desde"] = ahora
            elif ahora - qa_rt["desde"] > 1.4:
                qa_rt_foto("r00_presentacion")
                qa_rt["desde"] = None
                return True
            return None
        s = renpy.get_screen("plataformas_ui")
        if s is None:
            return None
        v = s.scope["vista"]
        p = v.p
        if v.resultado_listo():
            if qa_rt["desde"] is None:
                qa_rt["desde"] = ahora
            elif ahora - qa_rt["desde"] > 1.6:
                qa_rt_foto("r90_resultado")
                qa_rt["fps"] = v.fps()
                qa_rt["desde"] = None
                return True
            return None
        if v.cuenta > 0:
            return None
        n = int(p.tick / (2 * PL.TICKS_S))
        if n != qa_rt["serie"]:
            qa_rt["serie"] = n
            qa_rt_foto("r%02d_serie" % (n + 1))
        tipos = [e[1] for e in p.eventos]
        if "impulso" in tipos and any(t == "impulso" and p.tick - k < 12 for k, t, _d in p.eventos):
            qa_rt_foto("r50_impulso")
        fx = p.x // PL.T
        if any(p.nivel.tile(c, f) == PL.ESCANER and PL.escaner_activo(p.tick, c) for c in range(fx, fx + 6) for f in range(5, 10)):
            qa_rt_foto("r51_escaner_encendido")
        if v.st - v.zona_st < 1.0 and v.st - v.zona_st > 0.5:
            qa_rt_foto("r6%d_zona" % v.zona)
        if p.completado() and v.fin_st is not None and v.st - v.fin_st > 0.5:
            qa_rt_foto("r80_victoria")
        return None

screen qa_ruta_auto():
    zorder 1001
    timer 0.05 repeat True action Function(qa_rt_tick)

label qa_gal_ruta:
    hide screen qa_pad_inyector
    show screen qa_ruta_auto
    $ qa_plataformas_auto = 1.0
    $ nivel_rt = _qa_os.environ.get("ALCALDE_QA_RUTA_NIVEL", "historia")
    call minijuego_plataformas(nivel_rt, False, None, True, True)
    $ qa_plataformas_auto = None
    $ qa_gal["eventos"].append(("ruta", nivel_rt, _return["exito"], _return["calificacion"], _return["evidencias"],
                                _return["evidencias_total"], _return["muertes"], _return["segundos"], qa_rt.get("fps")))
    $ qa_gal_volcar(etapa="ruta", ok=True)
    $ renpy.quit()
