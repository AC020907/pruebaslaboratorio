## MISIONES PRINCIPALES: que debe hacer el jugador y a que lugar del mapa ir.
## El catalogo y el estado viven en clases/Misiones.py. La historia marca cada mision
## con completar_mision("id"); la activa es siempre la siguiente sin completar.
## El mapa (story/mapa.rpy) marca su destino con un aro amarillo.

default misiones_hechas = []

init python:
    from clases import Misiones as misiones

    def completar_mision(mision_id):
        if mision_id in misiones.POR_ID and mision_id not in store.misiones_hechas:
            store.misiones_hechas.append(mision_id)

    def misiones_pendientes_hud():
        """Insignia del HUD: 1 mientras haya una mision por cumplir."""
        return 1 if misiones.mision_activa(store.misiones_hechas, store.modo_feria_activo) else 0


style mision_texto is default:
    color "#2b2440"

## Remaster 3: el diario como hoja de papel. Cada mision es una ficha con la franja de su estado:
## en curso (ambar, con boton al mapa), cumplida (teal, sello) y pendiente (atenuada).
transform mision_entra(retraso):
    alpha 0.0 xoffset (0 if persistent.reducir_movimiento else -18)
    pause retraso
    easein 0.25 alpha 1.0 xoffset 0

screen mision_tarjeta(mision, estado, retraso=0.0):
    $ hecha = estado == "hecha"
    $ activa = estado == "activa"
    $ color = "#e8b04b" if activa else ("#2f9e8f" if hecha else "#c9b8d8")
    $ lugar = UBICACIONES[mision["ubicacion"]][0]
    $ minijuego = mision["minijuego"] or ""
    $ tinta = "#2b2440" if estado != "bloqueada" else "#8b84a8"
    frame at mision_entra(retraso):
        xfill True
        padding (0, 0, 0, 8)
        background Frame(ficha_fondo(200, 100, papel=("#fffaf3" if activa else ("#fbf6ee" if hecha else "#f3edf4")), franja=color, franja_w=14, sombra=(8 if activa else 4), borde=(4 if activa else 2)), 30, 20, 30, 24)
        hbox:
            spacing 24
            null width 14
            fixed:
                xysize (56, 56)
                yalign 0.5
                add Solid("#2b2440")
                add Solid(color, xysize=(48, 48), pos=(4, 4))
                text ("✓" if hecha else ("!" if activa else "·")) size 32 bold True color ("#fbf6ee" if hecha else "#2b2440") align (0.5, 0.5)
            vbox:
                spacing 6
                xsize 1080
                yalign 0.5
                null height 16
                text ("EN CURSO" if activa else ("CUMPLIDA" if hecha else "PENDIENTE")) size 13 bold True kerning 3 color ("#b07a1c" if activa else ("#2f9e8f" if hecha else "#8b84a8"))
                text mision["titulo"] font CIV_FUENTE_FINA size (36 if activa else 30) color tinta
                text mision["descripcion"] size 18 color ("#5b4f72" if estado != "bloqueada" else "#a39cb8")
                hbox:
                    spacing 12
                    frame:
                        background Solid("#2b2440" if estado != "bloqueada" else "#c9b8d8")
                        padding (10, 3)
                        text "Lugar: [lugar]" size 15 bold True color "#fbf6ee"
                    if minijuego:
                        frame:
                            background Solid("#d1495b" if estado != "bloqueada" else "#c9b8d8")
                            padding (10, 3)
                            text "Minijuego: [minijuego]" size 15 bold True color "#fbf6ee"
                null height 14
            if activa:
                textbutton "Ver en el mapa":
                    style "civ_ficha"
                    text_style "civ_ficha_text"
                    yalign 0.5
                    action [Hide("misiones_ciudad"), Function(abrir_mapa_libre)]

screen misiones_ciudad():
    zorder 102
    modal True
    key "game_menu" action Hide("misiones_ciudad")
    add Solid("#120d1ce6")
    $ lista = misiones.estado_misiones(misiones_hechas, modo_feria_activo)
    $ hechas = sum(1 for _m, e in lista if e == "hecha")
    fixed:
        xysize (1640, 1020)
        xalign 0.5
        ypos 24
        add ficha_fondo(1640, 1010, sombra=10, borde=4)
        add Solid("#8c2f4b", xysize=(1632, 10), pos=(4, 4))
        fixed:
            pos (56, 40)
            xysize (1100, 150)
            use civ_cabecera("DIARIO", "Misiones principales")
        hbox:
            xpos 1584
            xanchor 1.0
            ypos 52
            spacing 30
            vbox:
                yalign 0.5
                text "%d / %d" % (hechas, len(lista)) font CIV_FUENTE_FINA size 54 color "#2b2440" xalign 1.0
                text "CUMPLIDAS" size 14 bold True kerning 3 color "#8b84a8" xalign 1.0
            use civ_cerrar(Hide("misiones_ciudad"))
        add Solid("#2b2440", xysize=(1528, 3), pos=(56, 190))
        viewport:
            pos (56, 214)
            xysize (1540, 770)
            mousewheel True
            scrollbars "vertical"
            vscrollbar_unscrollable "hide"
            vbox:
                spacing 10
                xsize 1500
                for i, (mision, estado) in enumerate(lista):
                    use mision_tarjeta(mision, estado, 0.04 * min(i, 8))
