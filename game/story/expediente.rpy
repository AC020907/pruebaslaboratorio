## Expediente: fichas de investigacion. Solo muestra lo que el jugador encontro;
## las relaciones apuntan unicamente a fichas ya obtenidas.

screen exp_chip(estado):
    $ etiqueta, color = inv.ESTADOS_PISTA[estado]
    use civ_chip(etiqueta, color)

## Remaster 3: el expediente como carpeta de investigacion. Indice a la izquierda (cada ficha con la
## franja de su estado), la ficha abierta a la derecha como hoja con contorno de tinta y, si el estado es
## final, el sello. Misma informacion y mismas acciones que antes.
transform exp_hoja_entra:
    alpha 0.0 yoffset (0 if persistent.reducir_movimiento else 14)
    easein 0.22 alpha 1.0 yoffset 0

screen expediente():
    modal True
    zorder 102
    default nuevas = list(mem()["pistas_nuevas"])
    default seleccion = (list(mem()["pistas_nuevas"]) or list(mem()["pistas"]) or [None])[-1]
    on "show" action [Function(marcar_expediente_visto), Hide("notify")]
    key "game_menu" action Hide("expediente")

    $ propias = mem()["pistas"]
    $ abiertas = sum(1 for p in propias if propias[p] in ("observado", "hipotesis") and inv.PISTAS[p]["preguntas"])

    add Solid("#120d1ce6")
    fixed:
        xysize (1640, 1020)
        xalign 0.5
        ypos 24
        add ficha_fondo(1640, 1010, sombra=10, borde=4)
        add Solid("#8c2f4b", xysize=(1632, 10), pos=(4, 4))

        fixed:
            pos (56, 40)
            xysize (1100, 170)
            use civ_cabecera("CIUDAD NOVA", "Expediente", inv.resumen_investigacion(memoria))
        hbox:
            xpos 1584
            xanchor 1.0
            ypos 52
            spacing 30
            vbox:
                yalign 0.5
                text "%d" % abiertas font CIV_FUENTE_FINA size 54 color "#2b2440" xalign 1.0
                text "HILOS ABIERTOS" size 14 bold True kerning 3 color "#8b84a8" xalign 1.0
            use civ_cerrar(Hide("expediente"))
        add Solid("#2b2440", xysize=(1528, 3), pos=(56, 220))

        ## Indice
        viewport:
            pos (56, 240)
            xysize (480, 730)
            mousewheel True
            scrollbars "vertical"
            vscrollbar_unscrollable "hide"
            vbox:
                spacing 4
                xsize 456
                if not propias:
                    text "Todavía no hay fichas. Revisa CivitasNet y escucha a la gente: las pistas aparecen al inspeccionar." style "civ_nota" size 20
                for categoria in inv.CATEGORIAS_PISTA:
                    $ fichas = [p for p in propias if inv.PISTAS[p]["categoria"] == categoria]
                    if fichas:
                        null height 12
                        hbox:
                            spacing 10
                            text inv.NOMBRE_CATEGORIA[categoria].upper() style "civ_etiqueta"
                            text "%d" % len(fichas) size 15 bold True color "#8b84a8"
                        null height 4
                        for pid in fichas:
                            $ elegida = seleccion == pid
                            button:
                                xfill True
                                background (Solid("#2b2440") if elegida else Solid("#fbf6ee00"))
                                hover_background (Solid("#2b2440") if elegida else Solid("#efe6f3"))
                                padding (0, 10, 12, 10)
                                hover_sound "assets/audio/sfx/menu_hover.ogg"
                                action SetScreenVariable("seleccion", pid)
                                hbox:
                                    spacing 14
                                    add Solid(inv.ESTADOS_PISTA[propias[pid]][1], xysize=(8, 34)) yalign 0.5
                                    text inv.PISTAS[pid]["titulo"] size 20 color ("#fbf6ee" if elegida else "#2b2440") yalign 0.5 xmaximum 330
                                    if pid in nuevas:
                                        frame:
                                            yalign 0.5
                                            background Solid("#d1495b")
                                            padding (6, 1)
                                            text "NUEVA" size 12 bold True color "#fbf6ee" kerning 1

        ## Ficha abierta
        fixed:
            pos (580, 240)
            xysize (1004, 740)
            if seleccion and seleccion in propias:
                $ ficha = inv.PISTAS[seleccion]
                $ estado_f = propias[seleccion]
                $ etiqueta_f, color_f = inv.ESTADOS_PISTA[estado_f]
                fixed at exp_hoja_entra:
                    xysize (1004, 740)
                    add ficha_fondo(1000, 722, papel="#fffaf3", franja=color_f, franja_w=12, sombra=8)
                    ## Clip de papel
                    add Solid("#2b2440", xysize=(18, 60), pos=(912, -24))
                    add Solid("#c9b8d8", xysize=(8, 50), pos=(917, -19))
                    viewport:
                        pos (52, 32)
                        xysize (910, 660)
                        mousewheel True
                        scrollbars "vertical"
                        vscrollbar_unscrollable "hide"
                        vbox:
                            spacing 14
                            xsize 880
                            text "%s  ·  %s  ·  %s" % (inv.NOMBRE_CATEGORIA[ficha["categoria"]].upper(), ficha["procedencia"], inv.NOMBRE_MOMENTO[ficha["momento"]]) size 15 bold True kerning 2 color "#8b84a8"
                            text ficha["titulo"] font CIV_FUENTE_FINA size 46 color "#2b2440"
                            use exp_chip(estado_f)
                            add Solid("#c9b8d8", xysize=(880, 2))
                            text inv.contenido_pista(seleccion, memoria) size 24 color "#2b2440" substitute False line_spacing 4
                            if ficha["preguntas"] and estado_f in ("observado", "hipotesis"):
                                null height 6
                                hbox:
                                    spacing 16
                                    add Solid("#e8b04b", xysize=(6, 26 + 36 * len(ficha["preguntas"])))
                                    vbox:
                                        spacing 8
                                        text "PREGUNTAS ABIERTAS" style "civ_etiqueta" color "#b07a1c"
                                        for pregunta in ficha["preguntas"]:
                                            text "–  " + pregunta size 20 color "#5b4f72"
                            $ relacionadas = inv.relaciones_conocidas(seleccion, memoria)
                            if relacionadas:
                                null height 6
                                text "SE CONECTA CON" style "civ_etiqueta"
                                hbox:
                                    spacing 12
                                    box_wrap True
                                    box_wrap_spacing 10
                                    for rid in relacionadas:
                                        textbutton inv.PISTAS[rid]["titulo"]:
                                            style "civ_ficha"
                                            text_style "civ_ficha_text"
                                            padding (20, 8, 20, 14)
                                            text_size 17
                                            action SetScreenVariable("seleccion", rid)
                    if estado_f in ("comprobado", "refutado"):
                        frame at civ_sello_giro(-6):
                            xpos 950
                            xanchor 1.0
                            ypos 770
                            yanchor 1.0
                            background Solid(color_f)
                            padding (4, 4)
                            frame:
                                background Solid("#fffaf3")
                                padding (18, 6)
                                text etiqueta_f.upper() size 24 bold True color color_f kerning 4
            else:
                add ficha_fondo(1000, 722, papel="#fffaf3", sombra=8)
                text "Elige una ficha." style "civ_nota" size 24 align (0.5, 0.45)
