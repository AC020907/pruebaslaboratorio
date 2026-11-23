# Cinemática de apertura: «Un año antes»

**Qué es:** dramatización de ficción de 38,9 s. Se reproduce antes del prólogo interactivo al pulsar **Nueva partida** o **Modo Feria**. Una noticia falsa sobre el agua provoca bloqueos, una ambulancia queda atrapada, el monitor del paciente llega a la línea plana y el noticiero informa del fallecimiento. Termina con el título.

**Rama:** `feature/cinematica-apertura`. Sin push ni deploy.

## Continuidad con la historia

El prólogo empieza el **lunes a las 6:02**, cuando nace el rumor del agua (al final resulta ser una tubería rota). Ningún diálogo menciona bloqueos ni muertes. Si la cinemática ocurriera esa misma semana, contradiría la cronología, y presentarla como un futuro posible introduciría una consecuencia que el juego no tiene.

Por eso la cortinilla del noticiero la sitúa con un rótulo: **«CIUDAD NOVA · UN AÑO ANTES DE LAS ELECCIONES»**. Tras el título empieza el prólogo con su propio rótulo («lunes · 6:09 a. m. · seis días antes de las elecciones»): el mismo tipo de rumor vuelve a la ciudad.

No se modificó ningún diálogo, decisión, pista, minijuego, ruta ni final. Tampoco aparece ni se insinúa NOVA. Las cuentas del noticiero son genéricas; `@verdad.oculta` no aparece, porque en la historia se crea el domingo.

## Guion de planos (tiempos reales de `game/clases/cinematica_tiempos.py`)

| Tiempo | Plano | Imagen | Sonido |
|---|---|---|---|
| 0,0–1,1 | Cortinilla | «NOTICIAS NOVA · ÚLTIMA HORA», bandas que entran, rótulo «un año antes» | Sintonía |
| 1,1–2,6 | Mapa | Mapa oficial de Ciudad Nova; 14 puntos bloqueados aparecen uno a uno, con contador; ambulancia con pulso | Voz del presentador, sirena lejana |
| 2,6–3,9 | Calle | Barricada con llantas y vallas; manifestantes con carteles que se mueven | Multitud con consigna |
| 3,9–5,1 | CivitasNet | Publicaciones que suben y se multiplican; alerta «#AguaEnvenenada es tendencia» | — |
| 5,1–6,6 | Atasco | Fila de coches con luces de freno, la ambulancia al fondo | Bocina, sirena |
| 6,6–12,6 | Ambulancia | Primer plano de la ambulancia con luces rojas y azules. Cámara en mano; la cámara recorre la fila hasta la barricada (parallax de 5 capas) | Sirena fuerte que se desplaza con la cámara, bocinas, radio: «¡Central, tenemos un paciente crítico!…» |
| 12,6–16,8 | Paciente | Interior: paciente bajo la manta (sin rostro), suero que se balancea, paramédica y monitor en la pared. Diagnóstico de ficción en el monitor; la cámara sube al monitor y entra en él | Pitidos sincronizados, sirena apagada por la carrocería, oxígeno |
| 16,8–24,8 | Monitor | Primer plano: los latidos se espacian y se debilitan. Aparece «FC BAJA», luego el **último latido (21,02 s)** y la **línea plana (21,37 s)**. Desde 23,5 s la pantalla está entera en línea plana; aviso «ALARMA» y luz roja | La música se corta con el último latido. **Tono continuo de 22,0 a 24,0 s**; después, **silencio total**, con el monitor inmóvil (24,0–24,8 s) |
| 24,8–34,9 | Noticia | La calle bloqueada, apagada. Rótulo «FALLECE PACIENTE TRAS DEMORA EN SU TRASLADO»; a los 30,7 s, titular **«LA DESINFORMACIÓN COBRÓ OTRA VÍCTIMA»** con «Se investiga si los bloqueos retrasaron la atención del paciente» | Voz del presentador sin música; golpe sordo con el titular |
| 34,9–38,9 | Título | **CIVITAS**, **ALCALDE DIGITAL** y «Una mentira puede recorrer una ciudad. Sus consecuencias también.» (mismo logotipo de red del prólogo) | Golpe grave y una nota |

Las frases habladas son las del guion, palabra por palabra; una prueba lo comprueba. El noticiero dice «habrían dificultado» y el titular va acompañado de «se investiga», así que el retraso se presenta como un factor investigado y no como causa probada. En los planos médicos se lee «DRAMATIZACIÓN», y el monitor no muestra la palabra «muerte».

**Duración:** 38,9 s, no 30. Las tres frases pedidas suman 23,5 s de voz, incluso a ritmo de noticiero (velocidad 1,14–1,2). Además, la secuencia del monitor necesita unos 8 s para que se vea el deterioro, el último latido, la línea plana, el tono y el silencio. Para acercarse a los 30 s, las voces se solapan con los cortes de plano.

## Implementación

| Pieza | Archivo |
|---|---|
| Línea de tiempo (planos, latidos, voces, subtítulos, signos vitales, forma del ECG) | `game/clases/cinematica_tiempos.py` |
| Pantalla, cámara, planos y monitor | `game/story/cinematica.rpy` |
| Arte nuevo (calle en 5 capas, 6 vehículos, ambulancia, luces, barricada, 8 manifestantes, interior, camilla, paramédica, suero, carcasa del monitor, iconos) | `tools/arte/cinematica_arte.py` → `game/images/cinematica/` |
| Voces del presentador y del paramédico (ElevenLabs; voces distintas de las de los personajes) | `tools/voces/cinematica_voces.py` → `tools/voces/cinematica/` |
| Sonido (sirena, tráfico, multitud, radio, música, pitidos, tono continuo, silencio, título) | `tools/musica/cinematica_sonido.py` → `game/assets/audio/cine/apertura_fx.ogg` y `apertura_voces.ogg` |
| Integración | `call cinematica_apertura` justo antes de `call prologo` en `script.rpy` y `story/modo_feria.rpy` |

**Monitor.** No es una imagen en bucle. `MonitorVital` dibuja en cada cuadro:
- la cuadrícula;
- el ECG y la onda de pulso, que se desplazan de derecha a izquierda (2,2 s visibles);
- el punto de escritura;
- los valores de FC, SpO2 y PA, y los avisos.

La señal sale de `CT.ecg(t)`: un complejo P-QRS-T por latido, que se ensancha y aplana al debilitarse. A partir de `PLANA` vale exactamente 0, así que no puede aparecer ningún latido después del último. Durante `CONGELADO` la imagen se detiene.

**Sincronía.** Hay dos pistas, efectos y música (canal `cine`, volumen de efectos) y voces (canal `cine_voz`, volumen de voz). Arrancan juntas con `synchro_start`. El reloj de la imagen es la posición real del canal `cine` (`renpy.music.get_pos`): cada pico R se dibuja en el mismo instante en que suena su pitido. En las pruebas, imagen y audio difieren entre 1 y 40 ms.

**Omitir.** El botón «Omitir ›» (arriba a la derecha), la tecla Esc o el clic derecho omiten la cinemática. Un clic normal no la corta, para que nadie se la salte sin querer en la feria. Al salir por cualquier vía (fin, omitir u ocultar la pantalla), el audio se detiene.

Con salto rápido activo (`config.skipping`) la cinemática se omite sola; es lo que usan los recorridos automáticos.

**Accesibilidad:** subtítulos de todas las líneas habladas. Con «Reducir movimiento» se desactivan la cámara en mano, el balanceo y los empujes de cámara.

**Estado de la partida:** la cinemática no usa `default`, no escribe en `store.` ni llama a funciones que den pistas, consecuencias o afinidad. La QA compara todas las variables del store y de `persistent` antes y después, tanto viéndola entera como omitiéndola: ningún cambio.

## Regenerar

```
python tools/arte/cinematica_arte.py
python tools/voces/cinematica_voces.py          # necesita ELEVENLABS_API_KEY; solo sintetiza lo que falta
python tools/musica/cinematica_sonido.py
```

Si se cambian tiempos en `cinematica_tiempos.py`, hay que volver a ejecutar `cinematica_sonido.py` (los pitidos y las voces se colocan con esos tiempos) y `tests/test_cinematica.py`.

## Pruebas (2026-11-22)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores |
| `python -m unittest discover -s tests -p "test_*.py"` | **205 OK**: las 190 anteriores y 15 nuevas en `tests/test_cinematica.py` (guion exacto, orden de planos, latidos que se espacian y debilitan, señal 0 tras el último latido, cada pitido sobre su latido, ningún pitido después, tono continuo, silencio, voces solo donde corresponde, imágenes, integración antes del prólogo, sin escrituras de estado) |
| `qa_visual.py galeria --etapas cinematica` (Nueva partida) | **OK**: completa en 38,91 s; un clic a los 5 s no la corta; ~159 fps; omitida con Esc a los 9,08 s; audio detenido en ambos casos; store y `persistent` sin cambios; llega al prólogo |
| Igual con `ALCALDE_QA_CINE_FLUJO=modo_feria` | **OK**; llega al prólogo del Modo Feria |
| `python tests/qa_recorridos.py` | **10/10**: los cinco finales en Historia y en Feria |
| Inventario de arte de personajes (155 archivos) | **Idéntico** |
| Inventario narrativo (652 elementos) | Sin cambios en el guion; solo la llamada nueva antes del prólogo |

**Capturas del juego real** (en `docs/remaster/cinematica/`; la hoja de contactos es `hoja_cinematica.jpg`):

| Momento | Captura |
|---|---|
| 1. Noticiero | `c01_noticiero.jpg` |
| 2. Calles bloqueadas | `c02_calles_bloqueadas.jpg` |
| 3. Ambulancia atrapada | `c03_ambulancia.jpg` |
| 4. Paciente crítico | `c04_paciente_critico.jpg` |
| 5. Monitor con latidos | `c05_monitor_latidos.jpg` |
| 6. Último latido | `c06_ultimo_latido.jpg` |
| 7. Línea plana | `c07a_linea_plana_tono.jpg` (último latido saliendo de la pantalla), `c07b_linea_plana_completa.jpg` (pantalla entera plana con el tono), `c07c_monitor_inmovil.jpg` (silencio) |
| 8. Titular del fallecimiento | `c08a_noticia.jpg`, `c08b_titular.jpg` |
| 9. Título | `c09_titulo.jpg` |
| 10. Transición al prólogo | `c10a_fin_cinematica.jpg`, `c10_prologo.jpg` (Nueva partida), `c10_prologo_modo_feria.jpg` |
| Omitir | `c11_antes_de_omitir.jpg`, `c12_despues_de_omitir.jpg` |

Las tiradas de QA guardaron, en cada captura, el tiempo de la cinemática, la posición del audio, el plano y el valor del ECG: `qa_nueva_partida.json`, `qa_modo_feria.json`.

**Vídeo:** `tests/grabar_cinematica.py` lanza el juego, captura la ventana real (1280×720, ~42 capturas/s) y escribe un AVI con vídeo MJPEG a 30 fps y audio PCM. El audio son las dos pistas que reproduce el juego, colocadas desde el t = 0 que marca el propio juego; no se graba el altavoz. Los datos de la grabación están en `grabacion_video.json`.

## Limitaciones

- La versión web (GitHub Pages) no se ha reconstruido: allí todavía no aparece la cinemática, y no se ha medido su rendimiento en el navegador.
- Las voces son de ElevenLabs y el sonido se generó con código. Se verificaron por números (tiempos, bandas de frecuencia, silencio, picos), pero **nadie las ha escuchado todavía**.
- El arte nuevo usa el estilo plano con contorno de la interfaz y del plataformero, no el estilo ilustrado de los fondos oficiales. Los únicos fondos oficiales que aparecen son el mapa de la ciudad y la pantalla del título.
- No se ha probado con personas ni en el equipo de la feria.
