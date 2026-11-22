## Archivo de Destinos: los finales como coleccionables. Los no descubiertos guardan el misterio.

transform destino_entrada(retraso):
    alpha 0.0 yoffset 24
    pause retraso
    easein 0.35 alpha 1.0 yoffset 0

transform destino_destacado:
    block:
        easein 0.8 zoom 1.03
        easeout 0.8 zoom 1.0
        repeat

## Remaster 3: cada destino es una ficha del archivo con la franja de color del final (la misma
## identidad que su cartela cinematografica). Los ocultos son fichas veladas con su pista.
screen tarjeta_destino(final, retraso=0.0, destacar=None):
    $ d = destinos.DESTINOS[final]
    $ visto = final in persistent.finales_vistos
    $ color = d["color"] if visto else "#c9b8d8"
    fixed at (destino_destacado if (final == destacar and not persistent.reducir_movimiento) else destino_entrada(retraso)):
        xysize (300, 500)
        add ficha_fondo(300, 490, papel=("#fbf6ee" if visto else "#ebe3ef"), sombra=10, borde=4)
        add Solid(color, xysize=(292, 74), pos=(4, 4))
        add Solid("#2b2440", xysize=(292, 4), pos=(4, 78))
        text ("Nº %d" % (destinos.FINALES.index(final) + 1)) size 15 bold True kerning 3 color ("#fbf6ee" if visto else "#5b4f72") pos (24, 28)
        fixed:
            xysize (128, 128)
            pos (86, 30)
            add circulo("#2b2440", "#2b2440", 64) align (0.5, 0.5)
            add circulo(color if visto else "#ddd3e6", "#fbf6ee", 58) align (0.5, 0.5)
            text (d["insignia"][0] if visto else "?") font CIV_FUENTE_FINA size 72 color ("#fbf6ee" if visto else "#8b84a8") align (0.5, 0.52)
        vbox:
            pos (24, 180)
            xsize 252
            spacing 12
            if visto:
                text d["titulo"] font CIV_FUENTE_FINA size 32 color "#2b2440" xalign 0.5 text_align 0.5
                text d["insignia"].upper() size 15 bold True color d["color"] xalign 0.5 kerning 4
                add Solid("#c9b8d8", xysize=(120, 2)) xalign 0.5
                text d["descripcion"] size 19 color "#5b4f72" text_align 0.5 xalign 0.5
            else:
                text "Destino oculto" font CIV_FUENTE_FINA size 32 color "#8b84a8" xalign 0.5
                text "PISTA" size 15 bold True color "#8b84a8" xalign 0.5 kerning 4
                add Solid("#c9b8d8", xysize=(120, 2)) xalign 0.5
                text d["misterio"] size 19 italic True color "#8b84a8" text_align 0.5 xalign 0.5

screen archivo_destinos(destacar=None):
    modal True
    zorder 130
    key "game_menu" action Hide("archivo_destinos")
    add Solid("#120d1cf0")
    $ n_vistos = len(finales_descubiertos())
    vbox:
        align (0.5, 0.5)
        spacing 34
        hbox:
            xsize 1640
            fixed:
                xysize (900, 150)
                use civ_cabecera("CIUDAD NOVA", "Archivo de Destinos", oscuro=True)
            vbox:
                xalign 1.0
                yalign 0.6
                text "%d / %d" % (n_vistos, len(destinos.FINALES)) font CIV_FUENTE_FINA size 60 color "#fbf6ee" xalign 1.0
                hbox:
                    xalign 1.0
                    spacing 8
                    for f in destinos.FINALES:
                        add Solid(destinos.DESTINOS[f]["color"] if f in persistent.finales_vistos else "#3a3350", xysize=(34, 8))
        text ("Has descubierto %d de %d destinos de Ciudad Nova" % (n_vistos, len(destinos.FINALES))) size 22 color "#c9b8d8"
        hbox:
            spacing 35
            xalign 0.5
            for i, final in enumerate(destinos.FINALES):
                use tarjeta_destino(final, 0.08 * i, destacar)
        hbox:
            xalign 0.5
            use civ_cerrar(Hide("archivo_destinos"), foco=True)
