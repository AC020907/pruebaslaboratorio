## Remaster 3: piezas comunes de interfaz (la "ficha" de Civitas: papel, contorno de tinta y sombra plana).
## Las usan el Expediente, las Misiones, el Mapa, CivitasNet y el Archivo de Destinos, para que todas las
## pantallas del juego hablen el mismo idioma que el inicio, los minijuegos y los finales. Solo presentacion.

define CIV_TINTA = "#2b2440"
define CIV_PAPEL = "#fbf6ee"
define CIV_NOCHE = "#120d1c"
define CIV_LILA = "#c9b8d8"
define CIV_VINO = "#8c2f4b"
define CIV_RUMOR = "#d1495b"
define CIV_TEAL = "#2f9e8f"
define CIV_AMBAR = "#e8b04b"
define CIV_GRIS = "#8b84a8"
define CIV_FUENTE_FINA = "fonts/Roboto-Light.ttf"

init -1 python:
    def ficha_fondo(w, h, papel="#fbf6ee", franja=None, sombra=8, borde=3, franja_w=10, tinta="#2b2440"):
        """Hoja de papel con contorno de tinta y sombra plana debajo (sin degradados)."""
        capas = []
        if sombra:
            capas.append(Solid(tinta, xysize=(w, h), pos=(0, sombra)))
        capas.append(Solid(tinta, xysize=(w, h)))
        capas.append(Solid(papel, xysize=(w - 2 * borde, h - 2 * borde), pos=(borde, borde)))
        if franja:
            capas.append(Solid(franja, xysize=(franja_w, h - 2 * borde), pos=(borde, borde)))
        return Fixed(*capas, xysize=(w, h + sombra))

style civ_ficha is default:
    background Frame("gui/boton_menu_idle.png", 20, 16, 20, 22)
    hover_background Frame("gui/boton_menu_hover.png", 22, 16, 20, 22)
    insensitive_background Frame("gui/boton_menu_idle.png", 20, 16, 20, 22)
    padding (30, 12, 30, 18)
    hover_sound "assets/audio/sfx/menu_hover.ogg"
    activate_sound "assets/audio/sfx/ui_click.wav"

style civ_ficha_text is default:
    size 20
    bold True
    color "#2b2440"
    hover_color "#8c2f4b"
    insensitive_color "#8b84a8"
    xalign 0.5
    text_align 0.5

style civ_ficha_oscura is civ_ficha:
    background Frame("gui/telefono_boton.png", 12, 12)
    hover_background Frame("gui/telefono_boton_hover.png", 12, 12)
    padding (26, 12)

style civ_ficha_oscura_text is civ_ficha_text:
    color "#fbf6ee"
    hover_color "#fbf6ee"

style civ_etiqueta is default:
    size 15
    bold True
    kerning 4
    color "#8c2f4b"

style civ_titulo is default:
    font "fonts/Roboto-Light.ttf"
    size 56
    color "#2b2440"

style civ_cuerpo is default:
    size 22
    color "#2b2440"

style civ_nota is default:
    size 18
    color "#5b4f72"

## Cabecera de una hoja: etiqueta pequena, titulo en Roboto Light y la raya roja de la marca.
screen civ_cabecera(etiqueta, titulo, subtitulo=None, oscuro=False):
    vbox:
        spacing 2
        text etiqueta style "civ_etiqueta" color ("#c9b8d8" if oscuro else "#8c2f4b")
        text titulo style "civ_titulo" color ("#fbf6ee" if oscuro else "#2b2440")
        add Solid("#d1495b", xysize=(120, 5)) ypos 6
        if subtitulo:
            null height 10
            text subtitulo size 20 italic True color ("#c9b8d8" if oscuro else "#5b4f72") substitute False

## Boton de cierre comun: ficha con la tecla al lado (Esc o B en mando).
screen civ_cerrar(accion, etiqueta="CERRAR", foco=False):
    button:
        style "civ_ficha"
        action accion
        default_focus foco
        hbox:
            spacing 16
            yalign 0.5
            text etiqueta style "civ_ficha_text" kerning 2 yalign 0.5
            frame:
                yalign 0.5
                background Solid("#2b2440")
                padding (8, 2)
                text "Esc" size 14 bold True color "#fbf6ee"

## Chip de estado: ficha pequena con el color del estado y texto en papel.
screen civ_chip(etiqueta, color, claro=False):
    frame:
        background Solid(color)
        padding (12, 4)
        yalign 0.5
        text etiqueta size 15 bold True color ("#2b2440" if claro else "#fbf6ee") kerning 1

## Sello girado (estado final de una ficha), con contorno doble como un sello de tinta.
transform civ_sello_giro(angulo=-8):
    rotate angulo
    alpha 0.92

screen civ_sello(texto, color, angulo=-8):
    frame at civ_sello_giro(angulo):
        background Solid(color)
        padding (4, 4)
        frame:
            background Solid("#fbf6ee")
            padding (16, 6)
            text texto size 24 bold True color color kerning 4
