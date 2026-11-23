# Central de Emergencias

**Qué es:** el minijuego de estrategia en tiempo real que sustituye a Caza-Rumores. La desinformación provoca bloqueos en Ciudad Nova y hay personas que necesitan un hospital. El jugador coordina ambulancias:
- a quién atender primero;
- por qué ruta;
- a qué hospital llevar a cada paciente;
- cuándo desviar;
- cuándo gastar un recurso.

Es la consecuencia temática de la cinemática de apertura (la ambulancia atrapada en el bloqueo): aquí el jugador sí puede intervenir.

**Rama:** `feature/minijuegos-feria`. **Punto de recuperación:** tag `checkpoint-pre-minijuegos-feria` (commit `5cd7235`). Sin push ni deploy.

## Cómo se juega (con el ratón)

1. Toca una **ambulancia**, en el mapa o en su tarjeta.
2. Toca una **emergencia**. El anillo que la rodea es el tiempo que le queda al paciente.
3. Elige la **ruta**:
   - **A** es la más rápida ahora (Dijkstra).
   - **B** es la alternativa. Si la ruta A pasa por una calle con **protesta anunciada** (megáfono con cuenta atrás), la B la esquiva.
4. La ambulancia circula por las calles. Si una protesta corta su ruta, se detiene antes de la barricada y hay que **DESVIARLA**.
5. Con el paciente a bordo, elige **hospital**. Cada uno muestra su tiempo estimado y sus **camas libres**. Si nadie elige, la tripulación va al más rápido con cama a los 6 s.

**Recursos limitados:**
- **Mediación:** toca una barricada y la calle abre en 3 s.
- **Ruta prioritaria:** durante 20 s, la ambulancia elegida no paga el tráfico.

Cada recurso usado resta 15 puntos.

**Si no se elige ambulancia:** al tocar una emergencia se propone la ambulancia libre más cercana. El jugador confirma igualmente la ruta.

**Otros controles:** Esc cancela o pausa. Con mando, la cruceta recorre el panel de despacho y A elige.

**Tutorial:** la fase 1 incluye un tutorial integrado. Unos anillos con «AQUÍ» señalan el siguiente paso y una caja «Cómo se juega» lo explica en una línea. Antes de empezar se muestra una presentación de cuatro pasos.

## Fases

| Fase | Qué cambia | Decisión nueva |
|---|---|---|
| 1 · Primera emergencia | 1 ambulancia, 1 paciente grave. Hay una protesta anunciada sobre la ruta más probable. | Aprender a despachar; leer el aviso y elegir B, o desviar si cortan la calle |
| 2 · Ciudad congestionada | Llega la Ambulancia 7. Un paciente crítico y otro moderado a la vez. La Av. Central se atasca. Una protesta corta un puente. | Priorizar: no se puede atender a los dos a la vez. La ruta corta deja de ser la rápida |
| 3 · Crisis | Llega la Ambulancia 21. Hay varias llamadas seguidas. Una protesta **aísla** al paciente crítico del Sur (todas sus calles cortadas, sin reapertura) y hay más cortes en el centro. | Detectar la zona aislada (BFS) y gastar la mediación donde hace falta; coordinar tres ambulancias; elegir hospital según camas |

La dificultad sube con las decisiones (más llamadas que ambulancias, tráfico, protestas, aislamiento, camas), no recortando tiempos.

| Modo | Duración máxima | Pacientes | Recursos |
|---|---|---|---|
| Historia | 150 s (suele acabar en 120-140 s) | 7 | 2 mediaciones, 2 rutas prioritarias |
| Feria | 110 s (suele acabar en 85-100 s) | 6 | 1 y 1 |
| Arena | 140 s | 7 | 2 y 2 |

## Algoritmos y estructuras de datos

La ciudad es un **grafo ponderado no dirigido** (`game/clases/CentralEmergencias.py`):

- **Grafo:** 35 vértices (intersecciones) y 46 aristas (calles), guardados en listas de adyacencia `ADY[v] = [(vecino, arista), ...]`, ordenadas para que los desempates sean deterministas.
- **Tipos de calle:**
  - avenidas, más rápidas;
  - calles;
  - tres puentes sobre el río, que son los únicos pasos entre el Sur y el resto.
- **Peso de cada arista:** el tiempo de recorrido en ticks, `BASE[i] · nivel_trafico% / 100`, con niveles de tráfico 100, 160 y 240 %. Cambia en vivo.

| Algoritmo / estructura | Complejidad | Papel en la partida |
|---|---|---|
| **Dijkstra** con cola de prioridad (`heapq`, tuplas `(distancia, vértice)`) | O((V + E) log V) | Calcula la ruta A de cada despacho, de cada elección de hospital y de cada desvío, los tiempos estimados que ve el jugador (tarjetas de hospital y botones de ruta) y la elección automática de hospital. Con prioridad, usa el peso sin tráfico |
| **Dijkstra con penalizaciones** | igual | Ruta B: se repite Dijkstra multiplicando ×4 las calles con protesta anunciada (o, si A no pasa por ninguna, las calles de A) y se ofrece B solo si sale distinta |
| **BFS** con cola FIFO (`deque`) | O(V + E) | Recorre las calles abiertas desde los tres hospitales. Los vértices que no alcanza son **zonas aisladas**: el mapa las marca con un círculo rojo, no se puede despachar a ellas y piden una mediación |
| **Grafo dinámico** | O(1) por evento | Los eventos del escenario bloquean, avisan y reabren calles y cambian su tráfico. Al bloquear una calle se revisan las rutas pendientes de cada ambulancia: si contienen esa calle, la ambulancia avisa y se detiene antes de la barricada hasta que el jugador desvía. Las rutas se vuelven a calcular al pedir el desvío |
| **Cola de eventos** del escenario (lista ordenada por tick) | O(1) amortizado por tick | Llamadas, protestas (aviso 8 s antes), aperturas, tráfico, refuerzos y fases |

**Verificación:** `tests/test_central.py` compara Dijkstra con **Bellman-Ford** en 150 grafos con tráfico y bloqueos aleatorios. Comprueba la distancia y que la ruta sea una cadena de calles abiertas y contiguas. También verifica el BFS y las zonas aisladas: cortar los tres puentes aísla el Sur Oeste, que no tiene hospital.

## Simulación determinista

- **Paso fijo:** 30 ticks/s, solo enteros y desempates por id. La vista acumula tiempo real, así que la partida no depende de los FPS.
- **Órdenes:** todo lo que hace el jugador es una orden `[tick, tipo, a, b, c]` (`despachar`, `hospital`, `desviar`, `despejar`, `prioridad`). Las órdenes imposibles (ambulancia ocupada, opción inexistente, recurso agotado) se ignoran y no se registran.
- **Reproducción:** `CentralEmergencias.rejugar(escenario, ordenes)` reproduce exactamente la partida y rechaza listas manipuladas: formato, tipos, ticks desordenados o fuera de rango, más de 400 órdenes.

## Puntuación (transparente)

```
por cada paciente que llega a tiempo:  base(gravedad) + base · margen / (4 · tiempo límite)
   base: crítico 300 · grave 220 · moderado 160    (el margen da hasta +25 %)
por cada paciente que llega tarde:     base / 5
sin atender:                           0
− 15 por cada recurso usado
normalizada 0-1000 = bruta · 1000 / máximo posible
```

- **Éxito:** al menos 3 de cada 5 pacientes a tiempo.
- **Nota:** S ≥ 820, A ≥ 680, B ≥ 540, C con éxito, D sin él.
- **Clics:** no puntúan. Una orden rechazada no cambia nada; `test_puntuacion_acotada_y_transparente` lo comprueba añadiendo órdenes basura.
- **Datos informativos:** desvíos, tiempo medio de respuesta y recorrido se muestran, pero no suman.
- **Tono:** el tratamiento es serio. Sin atención a tiempo se lee «No se llegó a tiempo», el marcador se vuelve gris y se desvanece, y suena un sonido neutro. No hay animación de muerte ni efectos.

**Equilibrio** (despachador automático, 8 escenarios por fila; resultados al terminar de ajustar):

| Habilidad | Feria | Arena / Historia |
|---|---|---|
| 1,0 | 5-6/6, S-A | 6-7/7, S-A |
| 0,4 | 4-6/6, S-B | 5-7/7, S-B |
| 0,15 | 2-5/6, A-D | 4-6/7, A-D |

Hay un gradiente real: priorizar, desviar a tiempo, elegir hospital y usar la mediación en la zona aislada cambian el resultado.

## Integración en la historia (Caza-Rumores → Central de Emergencias)

El hueco narrativo es el mismo: la clave del resultado sigue siendo **`contencion`** («contención de la crisis»). Gracias a eso no cambian:
- las consecuencias (`crisis_contenida` y `crisis_desbordada`);
- los indicadores de Ciudad Nova;
- la Puntuación Cívica;
- las misiones;
- los finales y los guardados.

El label `minijuego_contencion` conserva su firma; solo su cuerpo llama ahora a `minijuego_central`.

**Puntos de integración que se localizaron y su estado:**

| Lugar | Antes | Ahora |
|---|---|---|
| `game/story/acto2.rpy` (miércoles, Barrio Sur, con reintento) | Caza-Rumores | Central (Historia). **Adaptación mínima:** la frase del narrador «Si no lo frenas ahora, mañana estará en toda la ciudad.» describía la mecánica antigua; ahora es «Ya hay calles bloqueadas y llamadas de emergencia en el Barrio Sur. Alguien tiene que coordinar las ambulancias.» Las reacciones de Rodrigo siguen coherentes y no se tocaron |
| `game/story/modo_feria.rpy` («Primero el hospital. Vamos.») | Caza-Rumores, 40 s | Central (modo Feria). `FERIA_CONTENCION = {"modo": "feria"}` |
| `game/minijuegos/integracion.rpy` (compartir una publicación falsa) | «…Hay que contenerla.» | Central. **Adaptación mínima** del narrador: «…se expande sin control: ya hay calles bloqueadas y llamadas al 123.» |
| `game/arena/arena_torneo.rpy` (Arena local) | intercepciones | Juega Central con el escenario del servidor y envía sus **órdenes** |
| `game/clases/arena/torneo.py` | `puntuar_arcade` (sin rejuego) | `puntuar_central`: **rejuega** las órdenes. Bots con el despachador. `tension` del Consejo: con desinformación ≥ 50 hay una protesta en el centro desde el inicio |
| `game/clases/arena/sala.py` y `campana.py` (Arena Online) | caza_web | Escenario y mapa con `config_cliente`, entrega de órdenes (no pueden llegar antes de su tiempo real) y rejuego. Textos de la ronda del debate adaptados |
| `leaderboard/app/static/arena.html` | `iniciarCaza` | `iniciarCentral` (mapa en canvas, panel de despacho, el mismo tutorial) y `central_motor.js` |
| `finales.rpy`, `ayuda.rpy`, `mando.rpy`, comentarios | «Caza-Rumores» | «Central de Emergencias» |
| QA (`qa_galeria`, `qa_mando`, `qa_autoplay`) | arcade | Central con despachador automático; `qa_autoplay` sigue sustituyendo el label en los recorridos |

**Diálogos de personajes:** no se cambió ninguno. Tampoco las decisiones ni los acontecimientos de la trama.

**Lo que se conserva sin borrar** (fuera de la experiencia jugable):
- `game/clases/CazaRumores.py`, `game/minijuegos/arcade.rpy` (`jugar_arcade`);
- `game/clases/arena/caza_web.py`, `leaderboard/app/static/caza_motor.js` y `tests/test_caza_web.py`, que sigue pasando;
- `iniciarCaza` en `arena.html`.

Ninguno se llama ya desde la historia, la Feria ni la Arena. Se pueden retirar del todo en un cambio aparte.

## Arena

- **Desafío de despacho en paralelo:** todos reciben el mismo mapa, las mismas llamadas, los mismos bloqueos y los mismos recursos, y cada uno dirige **su propia** simulación. Nadie comparte ambulancias ni estorba a otro. Se comparan pacientes a tiempo, eficiencia y puntos.
- **Arena local (LAN):** el cliente Ren'Py juega y envía sus órdenes; el servidor las rejuega con Python.
- **Arena Online:** `leaderboard/app/static/central_motor.js` es una traducción 1:1 del motor. `tests/test_central_web.py` ejecuta 12 partidas (3 modos × 4 perfiles, con órdenes al azar válidas e inválidas) en Node y en Python. Exige el mismo estado cada 10 ticks, las mismas órdenes aceptadas y la misma puntuación, y que el servidor puntúe igual lo que produce el navegador. **No se ha desplegado en Render.**

## Archivos

| Archivo | Contenido |
|---|---|
| `game/clases/CentralEmergencias.py` | Mapa-grafo, Dijkstra, BFS, escenarios, simulación, puntuación, rejuego, despachador automático |
| `game/minijuegos/central.rpy` | Vista (mapa vivo, ambulancias orientadas, tráfico civil animado, barricadas, megáfonos con cuenta atrás, anillos de tiempo, camas, zonas aisladas, rutas animadas), panel de despacho, tutorial, pausa y resultados |
| `game/minijuegos/contencion.rpy` | `minijuego_contencion` → Central |
| `tools/arte/central_arte.py` | Mapa ilustrado dibujado **a partir del mismo grafo** (lo que se ve y lo que se calcula coinciden) y sprites; exporta WebP para la web |
| `leaderboard/app/static/central_motor.js`, `arena.html` | Versión web |
| `game/qa_central.rpy` | QA en el motor real |

## Pruebas

| Prueba | Resultado |
|---|---|
| `tests/test_central.py` (19) | Grafo, Dijkstra = Bellman-Ford, tráfico, BFS y aislamiento, alternativa que evita la protesta, despacho-recogida-entrega, órdenes inválidas, bloqueo → detención → desvío, mediación, prioridad, camas y hospital automático, paciente sin atender, refuerzos y fases, aislamiento en fase 3, determinismo y rejuego, gradiente de habilidad, puntuación acotada, listas manipuladas, rendimiento (10 turnos en < 10 s) |
| `tests/test_central_web.py` | Paridad Python/JS tick a tick |
| `tests/test_arena_torneo.py` | Rejuego de órdenes en el servidor TCP con bots reales |
| `leaderboard` (165) | Campaña online con 2, 3 y 4 jugadores, entregas manipuladas o adelantadas, bots |
| `qa_visual.py galeria --etapas central` | Motor real: fase 1 jugada con **clics sobre el mapa** (ambulancia → emergencia → rutas A/B → B), el resto con el despachador; Historia y Feria completos, ~173 FPS |

Capturas en `docs/remaster/minijuegos/`.

## Verificación final (2026-11-23)

| Comprobación | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores |
| `python -m unittest discover -s tests -p "test_*.py"` | **230 OK** |
| `cd leaderboard && python -m pytest -q` | **165 OK** |
| `python tests/qa_recorridos.py` (cinco finales × Historia y Feria) | **10/10** |
| `qa_visual.py galeria` (todas las etapas) | menús, personajes, escenas, minijuegos, Duelo ×3, finales, cinemática y Central: OK. La etapa `ruta` se cayó al arrancar por una carrera de 11 procesos sobre `game/saves/persistent.new` (fallo del entorno, no del juego); sola: **OK** |
| Central en el motor real | Historia **A, 6/7** a tiempo; Feria **S, 6/6** (despachador) |
| Ruta en el motor real | Historia **S, 8/8** evidencias, 0 detecciones, 33,3 s |
| `qa_visual.py arena` (Arena local: 2 Ren'Py y 2 bots, 4 participantes) | OK: 5 pruebas (Central: 881-890 puntos los cuatro), elección final |
| `tests/e2e_arena_online.py --jugadores 2,3,4` (Chrome contra el servidor local) | OK: salas de 2, 3 y 4 jugadores juegan los 5 retos, incluidos Central y Ruta en PC y en móvil |
| Inventario de arte de personajes (155) | **Idéntico** |
| Inventario narrativo | Solo cambian las dos frases del narrador adaptadas y la llamada al nuevo minijuego (más la cinemática de la entrega anterior) |
| Vídeos del juego real (`tests/grabar_minijuego.py`, sin audio) | `Documents/civitas-dist/minijuegos/civitas_central_de_emergencias.mp4` (100 s) y `civitas_ruta_de_la_verdad.mp4` (39 s) |

## Limitaciones

- La jugabilidad se verificó con clics automáticos y un despachador automático, **no con personas**. Falta ver si un jugador nuevo entiende el tutorial sin ayuda y si la fase 3 resulta abrumadora.
- El mapa es plano e ilustrado con la paleta del juego, no con el estilo de los fondos oficiales.
- La versión web de la Arena Online necesita el Manual Deploy en Render para estar disponible.
