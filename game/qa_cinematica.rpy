## QA de la cinematica de apertura (ALCALDE_QA=galeria, ALCALDE_QA_ETAPA=cinematica). Juego real, sin atajos:
## 1) la reproduce entera y fotografia los momentos pedidos en el tiempo de su propio reloj (el del audio);
##    un clic a los 5 s no debe cortarla; compara TODO el store y persistent antes y despues;
## 2) la vuelve a llamar y la omite con Esc (game_menu) a los 9 s: debe volver "omitida" y el audio parar;
## 3) arranca una partida desde `start` (o `modo_feria` con ALCALDE_QA_CINE_FLUJO=modo_feria) y fotografia el
##    final de la cinematica y el primer plano del prologo.
## ALCALDE_QA_CINE_SERIE=1 guarda ademas un cuadro cada 0,5 s (hoja de contactos).
## ALCALDE_QA_CINE_MARCA=<archivo> escribe la hora de pared del t = 0 (tests/grabar_cinematica.py).

init python:
    import types as _qa_types
    import time as _qa_time

    QA_CINE_FOTOS = ((1.9, "c01_noticiero"), (3.3, "c02_calles_bloqueadas"), (8.6, "c03_ambulancia"),
                     (14.6, "c04_paciente_critico"), (18.3, "c05_monitor_latidos"), (21.12, "c06_ultimo_latido"),
                     (22.2, "c07a_linea_plana_tono"), (23.7, "c07b_linea_plana_completa"),
                     (24.45, "c07c_monitor_inmovil"), (27.0, "c08a_noticia"), (32.2, "c08b_titular"),
                     (37.6, "c09_titulo"))
    qa_cine = {"modo": None, "hechas": [], "omitir_en": None, "clic_en": None, "eventos": [], "prologo_desde": None}

    def qa_cine_valor(v):
        if isinstance(v, (_qa_types.ModuleType, _qa_types.FunctionType, type)) or callable(v):
            return None
        try:
            if hasattr(v, "__dict__") and not isinstance(v, (dict, list, set, tuple)):
                return repr(sorted((k, repr(x)) for k, x in vars(v).items()))
            return repr(v)
        except Exception:
            return None

    def qa_cine_estado():
        """Todo lo que la cinematica no debe tocar: variables del store y persistent."""
        res = {}
        for k, v in list(vars(renpy.store).items()):
            if k.startswith("_") or k.startswith("qa") or k in ("quick_menu", "etapa_gal", "store", "persistent"):
                continue
            r = qa_cine_valor(v)
            if r is not None:
                res[k] = r
        for k, v in list(vars(persistent).items()):
            if not k.startswith("_"):
                res["persistent." + k] = repr(v)
        return res

    def qa_cine_diff(a, b):
        return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

    def qa_cine_tick():
        s = renpy.get_screen("cinematica_apertura")
        modo = qa_cine["modo"]
        if s is None:
            if modo == "flujo" and renpy.get_screen("apertura_montaje"):
                if qa_cine["prologo_desde"] is None:
                    qa_cine["prologo_desde"] = renpy.get_screen("apertura_montaje") and _qa_time.time()
                elif _qa_time.time() - qa_cine["prologo_desde"] > 1.6:
                    qa_gal_foto("c10_prologo")
                    qa_cine["eventos"].append(("flujo", _qa_os.environ.get("ALCALDE_QA_CINE_FLUJO", "start"), "prologo"))
                    qa_gal["eventos"].extend(qa_cine["eventos"])
                    qa_gal_volcar(etapa="cinematica", ok=qa_cine_ok())
                    renpy.quit()
            return
        cine = s.scope["cine"]
        t = cine.t
        if modo == "completa":
            qa_cine["fps"] = round(cine.cuadros / max(0.5, t), 1)
        marca = _qa_os.environ.get("ALCALDE_QA_CINE_MARCA")
        if marca and modo == "completa" and t > 0.2 and not qa_cine.get("marcado"):
            # Para el grabador de video: hora de pared que corresponde a t = 0 de la cinematica.
            qa_cine["marcado"] = True
            with open(marca, "w") as f:
                f.write("%.4f" % (_qa_time.time() - t))
        if modo == "completa":
            for tf, nombre in QA_CINE_FOTOS:
                if t >= tf and nombre not in qa_cine["hechas"]:
                    qa_cine["hechas"].append(nombre)
                    pos = renpy.music.get_pos(channel="cine")
                    qa_cine["eventos"].append(("foto", nombre, round(t, 3), None if pos is None else round(pos, 3),
                                               CT.plano(t), round(CT.ecg(t), 3), t >= CT.PLANA))
                    qa_gal_foto(nombre)
                    return
            if _qa_os.environ.get("ALCALDE_QA_CINE_SERIE"):
                n = int(t * 2)
                clave = "s%03d" % n
                if clave not in qa_cine["hechas"]:
                    qa_cine["hechas"].append(clave)
                    qa_gal_foto("serie_%03d" % n)
            if qa_cine["clic_en"] is not None and t >= qa_cine["clic_en"]:
                qa_cine["clic_en"] = None
                renpy.queue_event("dismiss")
        elif modo == "omitir" and qa_cine["omitir_en"] is not None and t >= qa_cine["omitir_en"]:
            qa_cine["omitir_en"] = None
            qa_gal_foto("c11_antes_de_omitir")
            renpy.queue_event("game_menu")
        elif modo == "flujo":
            if t >= 38.55 and "c10a_fin" not in qa_cine["hechas"]:
                qa_cine["hechas"].append("c10a_fin")
                qa_gal_foto("c10a_fin_cinematica")

    def qa_cine_ok():
        ev = dict((e[0], e[1:]) for e in qa_cine["eventos"] if e[0] in ("completa", "omitida", "cambios_completa", "cambios_omitida"))
        return (ev.get("completa", (None,))[0] == "completa" and ev.get("omitida", (None,))[0] == "omitida"
                and not ev.get("cambios_completa", (["?"],))[0] and not ev.get("cambios_omitida", (["?"],))[0])

screen qa_cine_auto():
    zorder 1001
    timer 0.02 repeat True action Function(qa_cine_tick)

label qa_gal_cinematica:
    hide screen qa_pad_inyector
    $ qa_cine_e0 = qa_cine_estado()
    show screen qa_cine_auto
    # 1) Completa (con un clic a mitad del noticiero, que no debe cortarla).
    $ qa_cine["modo"] = "completa"
    $ qa_cine["clic_en"] = 5.0
    $ qa_cine_t0 = _qa_time.time()
    call cinematica_apertura
    $ qa_cine["eventos"].append(("completa", _return, round(_qa_time.time() - qa_cine_t0, 2)))
    $ qa_cine["eventos"].append(("fps_cinematica", qa_cine.get("fps")))
    $ renpy.pause(0.6, hard=True)
    $ qa_cine["eventos"].append(("audio_tras_completa", renpy.music.get_playing("cine"), renpy.music.get_playing("cine_voz")))
    $ qa_cine["eventos"].append(("cambios_completa", qa_cine_diff(qa_cine_e0, qa_cine_estado())))
    # 2) Omitida con Esc a los 9 s.
    $ qa_cine["modo"] = "omitir"
    $ qa_cine["omitir_en"] = 9.0
    $ qa_cine_t0 = _qa_time.time()
    call cinematica_apertura
    $ qa_cine["eventos"].append(("omitida", _return, round(_qa_time.time() - qa_cine_t0, 2)))
    $ renpy.pause(0.6, hard=True)
    $ qa_gal_foto("c12_despues_de_omitir")
    $ qa_cine["eventos"].append(("audio_tras_omitir", renpy.music.get_playing("cine"), renpy.music.get_playing("cine_voz")))
    $ qa_cine["eventos"].append(("cambios_omitida", qa_cine_diff(qa_cine_e0, qa_cine_estado())))
    $ qa_gal["eventos"].extend(qa_cine["eventos"])
    $ qa_gal_volcar(etapa="cinematica", ok=False)
    $ qa_gal["eventos"] = []
    # 3) Flujo real: Nueva partida (o Modo Feria) -> cinematica -> prologo.
    $ qa_cine["modo"] = "flujo"
    $ qa_cine["hechas"] = []
    if _qa_os.environ.get("ALCALDE_QA_CINE_FLUJO", "start") == "modo_feria":
        jump modo_feria
    jump start
