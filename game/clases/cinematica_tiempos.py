# -*- coding: utf-8 -*-
"""Linea de tiempo determinista de la cinematica de apertura (dramatizacion de ficcion).

Un solo lugar para los tiempos: el juego (game/story/cinematica.rpy) dibuja con ellos, el mezclador
(tools/musica/cinematica_sonido.py) coloca los pitidos y las voces con ellos, y las pruebas los comprueban.
Todo en segundos desde el primer cuadro. Sin dependencias de Ren'Py.
"""

DURACION = 38.9

# Planos: (nombre, inicio, fin). Entre planos hay cortes; FUNDIDO marca los que se funden.
PLANOS = (
    ("noticias", 0.0, 6.6),
    ("ambulancia", 6.6, 12.6),
    ("paciente", 12.6, 16.8),
    ("monitor", 16.8, 24.8),
    ("noticia_muerte", 24.8, 34.9),
    ("titulo", 34.9, DURACION),
)
FUNDIDO = {"paciente": 0.35, "monitor": 0.5, "titulo": 0.6}

# Sub-planos del montaje de noticias: (nombre, inicio, fin).
MONTAJE = (
    ("cortinilla", 0.0, 1.1),
    ("mapa", 1.1, 2.6),
    ("barricada", 2.6, 3.9),
    ("feed", 3.9, 5.1),
    ("atasco", 5.1, 6.6),
)

# Latidos: (tiempo del pico R, amplitud 0..1). El ritmo se vuelve lento e irregular y la senal se debilita.
# Los anteriores a PITIDOS_DESDE solo llenan la pantalla del monitor al entrar en la ambulancia (no suenan).
LATIDOS = (
    (10.80, 1.00), (11.35, 1.00), (11.90, 1.00), (12.45, 1.00),
    (13.00, 1.00), (13.55, 1.00), (14.10, 0.98), (14.65, 0.98), (15.20, 0.96), (15.75, 0.95),
    (16.32, 0.93), (16.92, 0.90), (17.56, 0.86), (18.26, 0.80), (19.04, 0.72), (19.94, 0.60),
    (21.02, 0.42),
)
ULTIMO_LATIDO = LATIDOS[-1][0]
PITIDOS_DESDE = 12.6                  # primer cuadro dentro de la ambulancia
VENTANA = 2.2                         # segundos de senal visibles en el monitor
PLANA = ULTIMO_LATIDO + 0.35          # desde aqui la senal no vuelve a subir
TONO = (22.0, 24.0)                   # tono continuo del monitor
CONGELADO = (24.0, 24.8)              # monitor inmovil y en silencio antes del corte
MUSICA_FIN = ULTIMO_LATIDO            # la musica se apaga con el ultimo latido

# Signos vitales que muestra el monitor: (tiempo, FC, SpO2, PA sistolica, PA diastolica); se interpola.
VITALES = (
    (12.6, 112, 88, 84, 52),
    (16.8, 98, 84, 78, 46),
    (19.0, 76, 79, 66, 38),
    (20.5, 54, 72, 56, 31),
    (21.3, 41, 68, 50, 28),
)

# Voces: archivo en tools/voces/cinematica/ y tiempo de inicio.
VOCES = (
    ("presentador_1", 0.55),
    ("paramedico", 7.95),
    ("presentador_2", 25.0),
)

# Subtitulos: (inicio, fin, quien, texto). Los textos son los del guion de la cinematica.
SUBTITULOS = (
    (0.55, 1.45, "NOTICIAS NOVA", "Última hora."),
    (1.48, 4.10, "NOTICIAS NOVA", "Los bloqueos continúan extendiéndose por Ciudad Nova"),
    (4.10, 7.85, "NOTICIAS NOVA", "tras la difusión de información no verificada sobre el suministro de agua."),
    (7.95, 10.25, "AMBULANCIA 12", "¡Central, tenemos un paciente crítico!"),
    (10.36, 12.60, "AMBULANCIA 12", "La avenida está completamente bloqueada."),
    (12.71, 14.60, "AMBULANCIA 12", "Necesitamos una ruta alternativa."),
    (25.00, 30.62, "NOTICIAS NOVA", "Un paciente con una infección intestinal grave falleció tras sufrir retrasos en su traslado de emergencia."),
    (30.71, 32.92, "NOTICIAS NOVA", "Los bloqueos que paralizan Ciudad Nova"),
    (32.98, 34.75, "NOTICIAS NOVA", "habrían dificultado su atención."),
)

TITULAR = 30.7                        # «LA DESINFORMACION COBRO OTRA VICTIMA»
DIAGNOSTICO = "Colitis infecciosa grave — complicaciones sistémicas"


def plano(t):
    """Nombre del plano en el instante t (el ultimo se mantiene al final)."""
    for nombre, a, b in PLANOS:
        if a <= t < b:
            return nombre
    return PLANOS[-1][0] if t >= DURACION else PLANOS[0][0]


def inicio(nombre):
    for n, a, _b in PLANOS:
        if n == nombre:
            return a
    raise KeyError(nombre)


def vitales(t):
    """(FC, SpO2, PAs, PAd) interpolados; antes del primero, el primero; despues del ultimo, el ultimo."""
    if t <= VITALES[0][0]:
        return VITALES[0][1:]
    for a, b in zip(VITALES, VITALES[1:]):
        if t <= b[0]:
            k = (t - a[0]) / (b[0] - a[0])
            return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(1, 5))
    return VITALES[-1][1:]


def _gauss(x, mu, sigma):
    import math
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def ecg(t):
    """Senal del ECG (unidades arbitrarias, 0 = linea base) en el instante t.

    Cada latido es un complejo P-QRS-T centrado en su pico R; los ultimos se ensanchan y se aplanan.
    Despues de PLANA la senal es exactamente 0: ningun latido aparece tras el ultimo.
    """
    if t >= PLANA:
        return 0.0
    v = 0.0
    for r, amp in LATIDOS:
        d = t - r
        if d < -0.35 or d > 0.45:
            continue
        ancho = 1.0 + (1.0 - amp) * 1.6
        v += amp * (0.12 * _gauss(d, -0.17, 0.028 * ancho)
                    - 0.14 * _gauss(d, -0.035, 0.010 * ancho)
                    + 1.00 * _gauss(d, 0.0, 0.012 * ancho)
                    - 0.26 * _gauss(d, 0.028, 0.012 * ancho)
                    + 0.22 * _gauss(d, 0.22, 0.055 * ancho))
    return v


def pletismografia(t):
    """Onda de pulso (SpO2): sigue a cada latido con 0,22 s de retraso y se apaga con el."""
    if t >= PLANA + 0.3:
        return 0.0
    v = 0.0
    for r, amp in LATIDOS:
        d = t - r - 0.22
        if -0.1 < d < 0.7:
            v += amp * amp * (_gauss(d, 0.08, 0.07) + 0.35 * _gauss(d, 0.30, 0.08))
    return v


def tono_pitido(amp):
    """Frecuencia del pitido de pulso: baja con la saturacion, como en los monitores reales."""
    return 760.0 + 200.0 * amp
