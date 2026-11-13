# Apertura «Ciudad Nova en crisis» (Feria Gamer)

## Por qué se cambió

La profesora pidió un inicio más dinámico, capaz de atrapar a un jurado desde los primeros segundos. Había gustado el multijugador y los minijuegos, pero el comienzo era lento.

| Inicio anterior (Modo Feria, contado en el guion) | Ahora |
|---|---|
| 7 líneas de diálogo (447 caracteres) y la pantalla de CivitasNet antes de la primera decisión | 0 líneas: la decisión llega justo después del montaje |
| El primer minijuego llegaba tras 26 líneas (≥ 1.745 caracteres), el teléfono, CivitasNet y varios menús, ya en el Lunes | Microprueba jugable a los ~31 s |
| La consecuencia de la decisión solo se veía como números flotantes | La consecuencia se ve en el grafo real de Civitas, con indicadores y la reacción de un ciudadano |

## El flujo (`game/story/prologo.rpy` + `game/story/apertura.rpy`)

| Fase | Qué ve y hace el jugador | Implementación |
|---|---|---|
| **A. La ciudad despierta** (≈ 9 s) | Vibración, notificaciones contradictorias de Civitas, el titular «¿EL AGUA ESTÁ ENVENENADA?», la tendencia, 3 llamadas perdidas de Claudia y «el alcalde eres tú». Clic, Enter o «Saltar» la terminan; si nadie toca nada, termina sola a los 11 s. | `screen apertura_montaje` |
| **B. Decisión inmediata** | La publicación de @verdad.oculta con su alcance. Tres respuestas: desmentir ahora, pedir los análisis o no intervenir todavía. Opcional: «Ver de dónde salió» (revela la captura recortada y da la pista `captura_veneno`). No se marca ninguna opción como correcta. | `menu (screen="apertura_decision")`: es un menú real, así el guardado, el rollback y los recorridos de QA lo respetan |
| **C. La ciudad reacciona** | El rumor se propaga nivel por nivel por el grafo de Civitas: cuentas alcanzadas, saltos, cuentas que tu respuesta frenó (en azul), la reacción de un ciudadano y el cambio en los indicadores. Clic: muestra todo; «Continuar» sigue. | `apertura_propagacion()` + `screen apertura_reaccion` |
| **D. Entra Claudia** | Reacciona a lo que ya elegiste (no se repite la decisión), se presenta en una línea y trae la pista nueva: la cuenta no existía ayer. La sospecha de una campaña coordinada queda abierta; NOVA no se revela. | `prologo.rpy` |
| **E. Microprueba** | Moderación Express con 4 comentarios (2 bots y 2 personas reales, una de ellas crítica con el alcalde). Claudia comenta el resultado. | `label apertura_microprueba`: mismo motor (`ColaModeracion`) y misma pantalla (`moderador_ui`) |
| **F. Título** | CIVITAS · ALCALDE DIGITAL · «Cada publicación cambia la ciudad». | `screen apertura_titulo` |
| Estilo del alcalde | Se conserva la elección (Cercano, Analítico, Mediático, Político). | `prologo.rpy` |

## Estructuras de datos que intervienen

- **Grafo dirigido y ponderado** (`red_civitas`, `clases/RedCivitas.py` + `GrafoSocial`): la fase C hace un **BFS real** (`bfs_propagacion`, cola FIFO y conjunto de visitados) desde `@verdad.oculta`, con semilla fija («apertura»), así que la animación es reproducible. La respuesta del jugador cambia los parámetros del recorrido:
  - **Desmentir:** las cuentas que siguen al alcalde quedan **bloqueadas**, porque leyeron el desmentido.
  - **Pedir análisis:** se bloquean los medios (`@salud.nova`, `@investigador.nova`, `@noticias.nova`), que esperan los datos; el rumor sigue por los demás.
  - **No intervenir:** no hay bloqueos y la fuerza de propagación sube ×1,35.

  Alcance resultante, sobre 27 cuentas: desmentir 16, pedir análisis 17 e ignorar 24.
- **Cola FIFO** (`ColaModeracion`, `deque`): la microprueba atiende los comentarios en orden de llegada.
- **Diccionarios de estado:** `apertura_decision`, `apertura_micro` y `apertura_tiempos`, además de las estructuras de la historia (hechos, pistas, afinidad, indicadores).

## Consecuencias conservadas, aplicadas una sola vez

| Respuesta | Indicadores (los mismos de antes) | Marcas |
|---|---|---|
| Desmentir | confianza +2, información verificada −2 | `desmintio_sin_datos`, calidad 0,4 |
| Pedir análisis | información verificada +3, desinformación +2 | `pidio_analisis`, calidad 1,0, Claudia +1 |
| No intervenir | desinformación +4, confianza −2 | `ignoro_rumor_agua`, calidad 0,0, Claudia −1 |

- `apertura_decidir()` se niega a aplicarse dos veces, y después de la decisión se bloquea el rollback.
- La microprueba aplica un efecto pequeño una sola vez:
  - todo limpio: confianza +1;
  - borró a una persona real: convivencia −1;
  - dejó pasar bots: desinformación +1.

  No escribe en `registro_minijuegos`, así que no altera la puntuación del Moderación Express completo del Lunes.
- **No se repiten comentarios:** los cuatro de la microprueba no están en el banco del reto completo (lo comprueba una prueba).
- **Lo que sigue igual:** la pista `hip_nova_creo`, las escenas posteriores que leen las marcas (CivitasNet del miércoles, Rodrigo, Martina) y los cinco finales.

## Decisiones de diseño

- **Interactuar antes de explicar.** La primera acción del jugador es la decisión de alcalde, no un diálogo.
- **Ver la consecuencia.** El grafo muestra quién recibió el rumor y por qué, en lugar de anunciarlo con texto.
- **Jugar pronto.** La microprueba enseña la regla clave de Moderación Express («a la gente real no se la calla») en 4 tarjetas y anticipa el reto completo.
- **Sin respuesta correcta anunciada.** El foco de teclado usa un color neutro para no sugerir una opción.
- **Accesibilidad:**
  - con «reducir movimiento», nada se desliza ni vibra y la propagación aparece completa;
  - el montaje dura lo mismo para que se pueda leer;
  - los sonidos tienen aviso visual (`sfx`);
  - no hay flashes;
  - todo se controla con ratón, teclado (Enter) o mando (`civ_accion`).
- **Voces:** las 13 líneas nuevas o cambiadas de Claudia se doblaron con las mismas voces de ElevenLabs. La línea del jugador no se dobla, por diseño.
- **Modos:** Historia y Modo Feria comparten la apertura. En Feria se omiten 3 líneas (la presentación larga de Claudia y el intercambio «¿Alguien la creó solo para esto?»).

## Demostración ante profesores y jurados (≈ 1 minuto)

1. **Menú principal → «Modo Feria (12 min)».** La crisis empieza sola; se puede pulsar «Saltar».
2. **La crisis:** señalar el titular y las llamadas perdidas.
3. **Decisión:** pulsar «Ver de dónde salió» y elegir una opción. Para comparar, repetir con otra respuesta y ver cómo cambia el alcance (16, 17 o 24 cuentas).
4. **Grafo:** explicar que es el BFS real de la red de Civitas. Las cuentas en azul son las que frenó tu respuesta, y los indicadores cambian.
5. **Claudia y la microprueba:** moderar 4 comentarios.
6. **Título → estilo → Lunes:** la historia sigue con normalidad. Para mostrar un minijuego completo, continuar hasta Moderación Express en el estudio de Martina.

## Pruebas realizadas (2026-11-12)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores |
| `python -m pytest -q tests` | 182 + 8 nuevas (`tests/test_apertura.py`) |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en Historia y en Feria, pasando por la nueva decisión (desmentir, analizar o no intervenir según el perfil) |
| `qa_visual.py galeria --etapas apertura` (con `ALCALDE_QA_APERTURA` = desmentir, analisis, ignorar) | OK en las 3 respuestas, en Feria y en Historia. Indicadores, pistas, afinidad y marcas correctos; consecuencias aplicadas una vez |
| Partida real con clics en la ventana | Montaje → decisión → grafo → Claudia → microprueba (4/4) → título → estilo, sin errores |

**Medición simulada** (lector automático de ~15 caracteres/s que pulsa a los 8,5 s del montaje; **no son datos de personas**):

| Hito | Feria | Historia |
|---|---|---|
| Primer acontecimiento | < 1 s (verificado en ventana real: < 2 s) | igual |
| Crisis comprendida y primera interacción | 8,8 s | 8,8 s |
| Decisión y consecuencia visible | 14 s | 14 s |
| Microprueba | 31 s | 33 s |
| Título | 49 s | 51 s |
| Fin del prólogo (incluido el estilo) | 64 s | 67 s |
| Líneas de diálogo en todo el prólogo | 10 | 12 |
| Interacciones obligatorias | 19 | 21 |

Capturas reales del motor en `docs/auditoria/apertura/` (`ap01`–`ap09`; la propagación, la consecuencia y Claudia, para cada respuesta).

**Sin verificar:** mando físico (las acciones `civ_accion` existen, pero no se probó con un mando conectado) y pruebas con personas (protocolo abajo).

## Protocolo de prueba con personas (pendiente: no se ha realizado)

Al menos **5 personas ajenas al equipo**. Una sesión por persona, sin explicar nada antes: solo «es un juego sobre una ciudad en elecciones».

1. Abre el juego en el menú y pídele que elija «Modo Feria». Cronometra desde ese clic.
2. No ayudes. Anota los tiempos y lo que diga en voz alta.
3. Detén la sesión en el título «CIVITAS» o al empezar el Lunes.

| Dato | Cómo registrarlo |
|---|---|
| Tiempo hasta comprender la crisis | Cuando diga, con sus palabras, que hay un rumor sobre el agua |
| Tiempo hasta la primera interacción | Primer clic o tecla con intención |
| ¿Comprendió su responsabilidad? | Pregunta al final: «¿Quién eras tú y qué tenías que hacer?» |
| ¿Entendió las consecuencias? | «¿Qué pasó en la ciudad por lo que elegiste?» |
| ¿Quiso seguir jugando? | «¿Quieres seguir?» (sí, no o tal vez) |
| Momento que más llamó su atención | Pregunta abierta |
| Escena que le pareció lenta | Pregunta abierta |
| Problemas de controles o lectura | Observación directa |

Plantilla de registro (una fila por persona; no anotes nombres ni datos personales):

| # | Comprende la crisis (s) | 1.ª interacción (s) | Responsabilidad (s/n) | Consecuencias (s/n) | Quiere seguir | Lo mejor | Lo lento | Problemas |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

**Criterio orientativo:** al menos 4 de 5 comprenden la crisis antes de los 15 s, entienden que su respuesta cambió la propagación y quieren seguir.
