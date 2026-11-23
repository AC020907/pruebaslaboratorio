"""Banda sonora de la cinematica de apertura, generada con codigo y alineada con game/clases/cinematica_tiempos.py.

    python tools/musica/cinematica_sonido.py

Escribe dos pistas de la misma duracion que el juego arranca juntas (synchro_start):
  game/assets/audio/cine/apertura_fx.ogg     ciudad, sirenas, radio, musica, monitor, tono continuo, titulo
  game/assets/audio/cine/apertura_voces.ogg  noticiero y radio de la ambulancia (canal de voz: respeta su volumen)
Los pitidos salen de LATIDOS (el mismo instante que dibuja el pico R) y el tono continuo de TONO.
Necesita las voces en tools/voces/cinematica/ (tools/voces/cinematica_voces.py).
"""
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "game"))
import dsp  # noqa: E402
from dsp import SR, bp, hp, lp  # noqa: E402
from clases import cinematica_tiempos as CT  # noqa: E402

SALIDA = RAIZ / "game" / "assets" / "audio" / "cine"
VOCES = AQUI.parent / "voces" / "cinematica"
N = int((CT.DURACION + 0.2) * SR)
rng = np.random.default_rng(1729)


def t_(n):
    return np.arange(n) / SR


def ruido(n):
    return rng.standard_normal(n)


def i_(seg):
    return int(round(seg * SR))


def estereo(m, pan=0.0):
    """pan -1 (izquierda) .. 1 (derecha), ley de potencia constante; pan puede ser un array."""
    a = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([m * np.cos(a), m * np.sin(a)])


def poner(buf, x, t0):
    a = i_(t0)
    if x.ndim == 1:
        x = estereo(x)
    b = min(buf.shape[1], a + x.shape[1])
    if b > a:
        buf[:, a:b] += x[:, : b - a]


def env_lineal(puntos, n):
    """Curva por tramos [(t, valor), ...] muestreada en n puntos (t en segundos desde 0)."""
    ts, vs = zip(*puntos)
    return np.interp(t_(n), ts, vs)


def media_movil(x, k):
    """Media movil centrada de k muestras (suma acumulada: O(n), no O(n*k))."""
    x = np.asarray(x, dtype=float)
    if k <= 1:
        return x
    c = np.cumsum(np.concatenate([np.zeros(k // 2 + 1), x, np.zeros(k)]))
    return (c[k:k + len(x)] - c[:len(x)]) / k


def suave(x, seg=0.02):
    return media_movil(x, max(1, i_(seg)))


# ---------------- Piezas ----------------
def sirena(dur):
    """Sirena de ambulancia (wail): sube y baja entre 650 y 1400 Hz cada 4,4 s; armonicos y algo de saturacion."""
    n = i_(dur)
    t = t_(n)
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * t / 4.4)
    f = 650 + 750 * lfo ** 0.8
    fase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(fase) + 0.35 * np.sin(2 * fase) + 0.18 * np.sin(3 * fase)
    return np.tanh(1.6 * x) * 0.5


def bocina(dur=0.45, f=410):
    n = i_(dur)
    t = t_(n)
    x = signal.sawtooth(2 * np.pi * f * t) + 0.7 * signal.sawtooth(2 * np.pi * f * 1.26 * t)
    x = lp(x, 2400) * dsp.fade(np.ones(n), 0.01, 0.06)
    return x * 0.25


def trafico(n):
    """Rumor de motores parados: ruido marron filtrado con un leve pulso de ralenti."""
    b = np.cumsum(ruido(n))
    b = hp(b - media_movil(b, 4410), 30)
    b = lp(b, 260)
    b /= np.max(np.abs(b)) + 1e-9
    ralenti = 1 + 0.15 * np.sin(2 * np.pi * 13 * t_(n))
    return b * ralenti * 0.6


def multitud(n, consigna=True):
    """Murmullo de gente; con consigna, golpes de voz a ritmo de grito de protesta (dos silabas por compas)."""
    x = bp(ruido(n), 280, 2600, order=3)
    am = 0.55 + 0.45 * suave(rng.random(n) > 0.5, 0.18)
    y = x * am
    if consigna:
        t = t_(n)
        ciclo = (t % 1.1)
        golpes = np.exp(-((ciclo - 0.05) / 0.09) ** 2) + 0.8 * np.exp(-((ciclo - 0.42) / 0.12) ** 2)
        voz = bp(ruido(n), 450, 1700, order=3) * golpes * 1.6
        y = y + voz
    return y / (np.max(np.abs(y)) + 1e-9) * 0.5


def radio_chasquido():
    n = i_(0.14)
    x = bp(ruido(n), 900, 5200) * np.exp(-t_(n) / 0.05)
    x[: i_(0.004)] += 0.9
    return x * 0.45


def estatica(n):
    return bp(ruido(n), 1200, 6000) * 0.05 * (1 + 0.5 * suave(rng.random(n), 0.05))


def pitido(freq, dur=0.09, amp=1.0):
    n = i_(dur)
    t = t_(n)
    x = np.sin(2 * np.pi * freq * t) + 0.12 * np.sin(4 * np.pi * freq * t)
    return dsp.fade(x, 0.004, 0.025) * 0.32 * amp


def tono_continuo(dur, freq=960.0):
    n = i_(dur)
    t = t_(n)
    x = np.sin(2 * np.pi * freq * t) + 0.1 * np.sin(4 * np.pi * freq * t)
    return dsp.fade(x, 0.004, 0.003) * 0.3


def golpe(dur=3.0, f0=52):
    """Impacto grave del titulo: seno con caida de tono y cola."""
    n = i_(dur)
    t = t_(n)
    f = f0 * (1 + 1.6 * np.exp(-t / 0.05))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    x += 0.4 * lp(ruido(n), 180) * np.exp(-t / 0.15)
    return x * 0.9


def acorde_sintetizado(notas_hz, dur, ataque=0.005, caida=0.35, brillo=2600):
    n = i_(dur)
    t = t_(n)
    x = sum(signal.sawtooth(2 * np.pi * f * t * (1 + 0.002 * k)) for k, f in enumerate(notas_hz))
    env = np.minimum(1, t / ataque) * np.exp(-t / caida)
    return lp(x * env, brillo) * 0.12


def cortinilla():
    """Sintonia de noticias: dos golpes de acorde con timbal y un barrido."""
    y = np.zeros(i_(1.6))
    re_m = [73.4, 146.8, 174.6, 220.0, 293.7]
    for t0, notas in ((0.0, re_m), (0.38, [f * 1.0595 for f in re_m])):
        a = acorde_sintetizado(notas, 1.1, caida=0.4)
        y[i_(t0): i_(t0) + len(a)] += a[: len(y) - i_(t0)]
        tim = golpe(0.8, 70) * 0.35
        y[i_(t0): i_(t0) + len(tim)] += tim[: len(y) - i_(t0)]
    w = bp(ruido(i_(0.4)), 800, 6000) * np.linspace(0, 1, i_(0.4)) ** 2 * 0.15
    y[: len(w)] += w
    return y


def cama_noticias(dur):
    """Ostinato de noticiero a 120 bpm (re menor), discreto: va por debajo de la voz."""
    n = i_(dur)
    y = np.zeros(n)
    patron = [146.8, 146.8, 174.6, 220.0, 146.8, 196.0, 174.6, 220.0]
    paso = 0.25
    k = 0
    while k * paso < dur:
        f = patron[k % len(patron)]
        nota = acorde_sintetizado([f, f * 2], 0.24, ataque=0.003, caida=0.08, brillo=1800)
        a = i_(k * paso)
        b = min(n, a + len(nota))
        y[a:b] += nota[: b - a] * (1.0 if k % 4 == 0 else 0.7)
        k += 1
    bajo = np.sin(2 * np.pi * 73.4 * t_(n)) * 0.08
    return y + bajo


def tension(dur):
    """Colchon de tension: pedal grave y un racimo que crece; se corta en seco con el ultimo latido."""
    n = i_(dur)
    t = t_(n)
    pedal = lp(signal.sawtooth(2 * np.pi * 36.7 * t) + signal.sawtooth(2 * np.pi * 36.9 * t), 160) * 0.18
    racimo = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate((220.0, 233.1, 261.6, 277.2)))
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 7.5 * t)
    crece = np.clip(t / dur, 0, 1) ** 1.5
    return pedal + racimo * trem * crece * 0.045


# ---------------- Voces ----------------
def cargar_voz(nombre, max_pausa=0.32):
    a, sr = sf.read(str(VOCES / (nombre + ".wav")))
    if a.ndim > 1:
        a = a.mean(axis=1)
    a = signal.resample_poly(a, SR, sr)
    env = suave(np.abs(a), 0.02)
    voz = env > 0.008
    idx = np.where(voz)[0]
    a = a[max(0, idx[0] - i_(0.03)): idx[-1] + i_(0.08)]
    voz = voz[max(0, idx[0] - i_(0.03)): idx[-1] + i_(0.08)]
    # Acorta las pausas largas (ritmo de noticiero) sin tocar las palabras.
    cambios = np.flatnonzero(np.diff(voz.astype(np.int8))) + 1
    limites = np.concatenate([[0], cambios, [len(voz)]])
    keep = np.ones(len(a), dtype=bool)
    mitad = i_(max_pausa) // 2
    for x0, x1 in zip(limites[:-1], limites[1:]):
        if not voz[x0] and x1 - x0 > i_(max_pausa) and x0 > 0 and x1 < len(voz):
            keep[x0 + mitad: x1 - mitad] = False
    return a[keep]


def emision(x):
    x = hp(x, 95)
    x = x + 0.35 * bp(x, 2200, 5200)
    return np.tanh(1.4 * x / (np.max(np.abs(x)) + 1e-9)) * 0.62


def radio(x):
    x = bp(x, 380, 2900, order=3)
    x = np.tanh(4.0 * x / (np.max(np.abs(x)) + 1e-9))
    x = dsp.bitcrush(x, bits=7, hold=2)
    return bp(x, 380, 3100) * 0.55 + estatica(len(x)) * 0.6


def pausas(x, umbral=0.012, minimo=0.2):
    """Inicios de frase (s) tras pausas de al menos `minimo` segundos: para ajustar subtitulos."""
    env = suave(np.abs(x), 0.03) > umbral
    cambios = np.flatnonzero(np.diff(env.astype(np.int8))) + 1
    limites = np.concatenate([[0], cambios, [len(env)]])
    return [round(x1 / SR, 2) for x0, x1 in zip(limites[:-1], limites[1:])
            if not env[x0] and x0 > 0 and x1 < len(env) and x1 - x0 > i_(minimo)]


# ---------------- Mezcla ----------------
def mezclar():
    fx = np.zeros((2, N))
    voces = np.zeros((2, N))
    inicio = {n: a for n, a, _b in CT.PLANOS}
    fin = {n: b for n, _a, b in CT.PLANOS}

    # Voces y su envolvente (para bajar el ambiente cuando hablan).
    procesadas = {}
    for nombre, t0 in CT.VOCES:
        limpia = cargar_voz(nombre)
        v = radio(limpia) if nombre == "paramedico" else emision(limpia)
        procesadas[nombre] = (t0, v)
        poner(voces, estereo(v, 0.0) * 0.95, t0)
        print("%-14s %5.2f s -> %5.2f a %5.2f  frases en %s" % (nombre, len(v) / SR, t0, t0 + len(v) / SR,
                                                               [round(t0 + p, 2) for p in pausas(limpia)]))
    habla = suave(np.abs(voces[0]) > 0.02, 0.25)
    ducking = 1.0 - 0.45 * np.clip(habla * 3, 0, 1)

    # 0 - 6.6: noticias (sintonia, cama, y el sonido de campo de cada inserto, lejano).
    poner(fx, cortinilla() * 0.9, 0.0)
    cama = cama_noticias(fin["noticias"] - 0.9)
    cama *= dsp.fade(np.ones(len(cama)), 0.4, 0.05)
    poner(fx, estereo(cama * 0.55, 0.0), 0.9)
    campo = np.zeros(i_(fin["noticias"] - 1.1))
    m = {n: (a, b) for n, a, b in CT.MONTAJE}
    tr = trafico(len(campo))
    campo += tr * 0.25
    a, b = m["barricada"]
    gente = multitud(i_(b - a))
    campo[i_(a - 1.1): i_(a - 1.1) + len(gente)] += gente * 0.55
    a, b = m["atasco"]
    sir = lp(sirena(b - a), 2500) * 0.35
    campo[i_(a - 1.1): i_(a - 1.1) + len(sir)] += sir
    campo[i_(a - 1.1 + 0.3): i_(a - 1.1 + 0.3) + i_(0.45)] += bocina(0.45, 380)
    poner(fx, estereo(lp(campo, 6000) * 0.7, 0.0), 1.1)

    # 6.6 - 12.6: la ambulancia atrapada. Sirena fuerte que se desplaza a la izquierda con la camara.
    a0, a1 = inicio["ambulancia"], fin["ambulancia"]
    dur = a1 - a0
    sir = sirena(dur + 10.0)
    pan = np.interp(t_(len(sir)), [0, dur, dur + 10], [0.1, -0.65, -0.65])
    vol = np.interp(t_(len(sir)), [0, 0.15, dur, dur + 0.01, dur + 4.2, CT.ULTIMO_LATIDO - a0, CT.ULTIMO_LATIDO - a0 + 0.8],
                    [0.0, 0.95, 0.85, 0.30, 0.22, 0.08, 0.0])
    sir_mezcla = sir * vol
    # Dentro de la ambulancia la sirena se oye amortiguada.
    corte = i_(dur)
    sir_mezcla[corte:] = lp(sir_mezcla[corte:], 1100, order=3)
    poner(fx, estereo(sir_mezcla, pan[: len(sir_mezcla)]), a0)
    trf = trafico(i_(dur)) * 0.9
    poner(fx, estereo(trf, 0.0), a0)
    gente = multitud(i_(dur)) * np.interp(t_(i_(dur)), [0, 2.5, dur], [0.05, 0.15, 0.75])
    poner(fx, estereo(gente, 0.45), a0)
    for t0, f, p in ((0.7, 395, -0.3), (1.6, 455, 0.4), (3.3, 370, 0.6), (4.6, 430, -0.2), (5.4, 470, 0.5)):
        poner(fx, estereo(bocina(0.5 if t0 != 3.3 else 0.9, f), p), a0 + t0)
    # Radio: chasquido al abrir y cerrar el canal, estatica de fondo mientras habla el paramedico.
    t_radio, v_radio = procesadas["paramedico"]
    poner(fx, radio_chasquido(), t_radio - 0.12)
    poner(fx, estatica(len(v_radio)) * 0.8, t_radio)
    poner(fx, radio_chasquido(), t_radio + len(v_radio) / SR + 0.02)

    # 6.6 - 21: musica de tension que se corta con el ultimo latido.
    dur_t = CT.MUSICA_FIN - a0
    ten = tension(dur_t)
    ten *= dsp.fade(np.ones(len(ten)), 0.6, 0.004)
    poner(fx, estereo(ten, 0.0), a0)

    # 12.6 - 21: interior (oxigeno, motor al ralenti, todo apagado por la carroceria).
    p0 = inicio["paciente"]
    dur_i = CT.PLANA - p0
    oxi = hp(ruido(i_(dur_i)), 4000) * 0.012
    motor = lp(trafico(i_(dur_i)), 140) * 0.5
    caida = np.interp(t_(i_(dur_i)), [0, dur_i - 1.5, dur_i], [1.0, 0.6, 0.0])
    poner(fx, estereo((oxi + motor) * caida, 0.0), p0)

    # Pitidos del monitor en el instante de cada pico R (mas fuertes en el primer plano del monitor).
    for r, amp in CT.LATIDOS:
        if r < CT.PITIDOS_DESDE:
            continue
        cerca = 1.0 if r >= inicio["monitor"] else 0.72
        poner(fx, estereo(pitido(CT.tono_pitido(amp), amp=(0.45 + 0.55 * amp) * cerca), 0.0), r)
    # Tono continuo; despues, silencio total.
    t0, t1 = CT.TONO
    poner(fx, estereo(tono_continuo(t1 - t0), 0.0), t0)

    # 24.8 - 34.4: noticia del fallecimiento, sin musica. Un tono de sala casi inaudible y un golpe sordo con el titular.
    n0 = inicio["noticia_muerte"]
    sala = lp(ruido(i_(fin["noticia_muerte"] - n0)), 400) * 0.006
    poner(fx, estereo(sala, 0.0), n0)
    poner(fx, estereo(golpe(1.4, 44) * 0.35, 0.0), CT.TITULAR)

    # 34.4 - fin: titulo.
    ti = inicio["titulo"]
    poner(fx, estereo(golpe(3.6, 49) * 0.9, 0.0), ti + 0.15)
    campana = sum(np.sin(2 * np.pi * f * t_(i_(3.6))) * w for f, w in ((293.7, 1.0), (587.3, 0.3), (880.0, 0.12)))
    campana *= np.exp(-t_(i_(3.6)) / 1.2) * 0.09
    poner(fx, estereo(campana, 0.0), ti + 0.9)

    fx *= np.stack([ducking, ducking])
    # Silencio absoluto entre el fin del tono y la voz del noticiero (el monitor queda inmovil).
    fx[:, i_(CT.TONO[1]): i_(inicio["noticia_muerte"])] = 0.0
    return fx, voces


def normalizar(x, pico=0.89):
    return x / max(np.max(np.abs(x)), 1e-9) * pico


def escribir_ogg(ruta, x):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with sf.SoundFile(str(ruta), "w", samplerate=SR, channels=2, format="OGG", subtype="VORBIS",
                      compression_level=0.5) as f:
        data = x.T.astype(np.float32)
        for k in range(0, len(data), 8192):
            f.write(data[k:k + 8192])


def main():
    fx, voces = mezclar()
    escala = 0.89 / max(np.max(np.abs(fx)), np.max(np.abs(voces)), 1e-9)
    fx *= escala
    voces *= escala * 1.05
    np.clip(voces, -0.95, 0.95, out=voces)
    escribir_ogg(SALIDA / "apertura_fx.ogg", fx)
    escribir_ogg(SALIDA / "apertura_voces.ogg", voces)
    print("ok:", SALIDA, "duracion %.2f s" % (N / SR))


if __name__ == "__main__":
    main()
