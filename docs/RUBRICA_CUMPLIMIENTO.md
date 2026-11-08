# Matriz de cumplimiento: rúbrica «LABORATORIO — ALCALDE DIGITAL» (PDF de 15 páginas)

- **Fuente:** `LABORATORIO 1 202630 (1).pdf`, Universidad del Norte, Estructura de Datos II. Se leyó completo, página por página.
- **Estado del código:** rama `feature/arena-rubrica`, actualizada el 2026-11-07.

**Estados:**
- **CUMPLE VERIFICADO:** se probó ejecutándolo (prueba automática, partida real o captura).
- **PARCIAL:** cumple en parte; se dice qué falta.
- **NO CUMPLE.**
- **NO VERIFICABLE:** requiere hardware, personas o accesos que no hay en este entorno.

**Comandos de evidencia:**
- **[T1]** `python -m pytest -q tests`: 110 pruebas. Incluye `test_arena_motor.py`, `test_arena_red.py`, `test_civitas_logica.py`, `test_destinos_puntuacion.py` y `test_ritmo.py`.
- **[T2]** `cd leaderboard && python -m pytest -q`: 142 pruebas del backend.
- **[T3]** `python tests/qa_recorridos.py`: los 5 perfiles llegan a sus 5 finales, en historia y en feria.
- **[T4]** `python tests/qa_visual.py arena --salida <dir>`: 4 procesos (2 Ren'Py + 2 bots), partida completa y capturas.
- **[T5]** `python tests/qa_visual.py galeria --salida <dir>`: capturas de menús, escenas, minijuegos, duelo y finales.
- **[L]** `renpy.exe . lint`: sin errores.

| § / pág. | Requisito (fiel al PDF) | Estado | Dónde (archivo · función) | Evidencia | Riesgo / nota |
|---|---|---|---|---|---|
| 1 / p.1 | Videojuego educativo sobre uso responsable de redes | CUMPLE VERIFICADO | Todo `game/` | T3, T4, T5 | — |
| 1 / p.1 | Desarrollado exclusivamente en Java o Python | CUMPLE VERIFICADO | Lógica del juego en Python: Ren'Py 8.5 (Python 3.12), `game/clases/*.py`; backend opcional en Python (FastAPI) | Repositorio | Ren'Py es un motor escrito en Python. La versión web es el mismo juego Python compilado a WebAssembly por Ren'Py: no hay lógica propia en JavaScript. |
| 1 / p.1 | Ciudad Nova, elecciones, red Civitas (publicar, compartir, verificar, reportar) | CUMPLE VERIFICADO | Historia (`story/`), CivitasNet (`story/civitasnet.rpy`), Arena (`clases/arena/reglas.py`) | T3, T4 | — |
| 1–2 / pp.1–2 | Indicadores a subir (verificada, convivencia, confianza, bienestar, participación) y a bajar (desinformación, conflictos, rumores, uso irresponsable) | CUMPLE VERIFICADO | Arena: `reglas.INDICADORES` (los 8); historia: `Ciudad.py` y HUD | T1 `test_responsables_ganan_puntos_y_la_ciudad_mejora`, capturas de T4 | El «uso irresponsable» se mide por acciones: puntos y reputación negativos. |
| 2 / p.2 | Sin preguntas explícitas de conocimiento; aprender por decisiones y consecuencias | CUMPLE VERIFICADO | No hay cuestionarios. Verificar muestra la fuente o pista y el jugador decide; el resultado explica qué pasó | Capturas de T4 (`*_verificar`, `*_resultado`) | La pregunta «¿Es verdadera?» es la del árbol del PDF (p.4), no una pregunta de examen. |
| 3 / p.2 | Cuatro candidatos compiten y usan Civitas | CUMPLE VERIFICADO (Arena) · PARCIAL (historia) | `reglas.CANDIDATOS` (Vega, Ortega, Prado, Ruiz), con cuentas en el grafo | Captura final de T4 | La historia individual se centra en el alcalde y su rival Tomás Vega, y no nombra a cuatro candidatos. |
| 3 / p.2 | Publicaciones verdaderas, opiniones y falsas (incluye los ejemplos del PDF) | CUMPLE VERIFICADO | `reglas.PUBLICACIONES`: «El candidato Juan quiere cerrar el colegio», «El alcalde actual está robando dinero», «Mañana cerrarán todos los parques»… | T1, T4 | — |
| 3 / p.2 | Decidir: compartir, verificar, ignorar o reportar, con consecuencias | CUMPLE VERIFICADO | Árbol `arbol_base()`, `Partida.resolver_ronda()`; historia: teléfono (`Publicacion.py`) | T1, T4 | — |
| 4 / p.3 | De 2 a 4 jugadores | CUMPLE VERIFICADO | `reglas.MIN/MAX_JUGADORES`, servidor | T1 `test_roles_unicos_y_limites`; T1 red `test_2_3_y_4…` y `test_procesos_independientes_2_3_4` | — |
| 4 / p.3 | Roles Ciudadano, Periodista, Influencer y Candidato a alcalde, con habilidades distintas | CUMPLE VERIFICADO | `ROLES`, `DESCRIPCION_ROL`, `arbol_para`, `resolver_ronda`, `_valorar`, `Partida._conectar_jugador` | T1 `test_candidato_no_reporta…`, `test_periodista_ve_la_fuente…`, `test_influencer_pesa_el_doble`, `test_jugadores_entran_al_grafo` | Cada rol cambia su árbol, su alcance en el grafo, sus bloqueos y su peso en la puntuación. Un rol solo puede tomarlo una persona. |
| 5 / pp.3–4 | Árboles funcionales que resuelven un problema real | CUMPLE VERIFICADO | `Tree.py` (n-ario: insertar, eliminar, buscar, recorridos, ruta, hojas, altura); `ArbolAVL.py` (banco por riesgo) | T1 `TestArbol`; `docs/ESTRUCTURAS_DATOS.md` §1 | — |
| 5 / p.4 | Justificar: problema, por qué, variante, inserción/eliminación, recorrido | CUMPLE VERIFICADO | `docs/ESTRUCTURAS_DATOS.md` §1, `docs/GUIA_SUSTENTACION.md` | — | — |
| 6 / p.5 | Grafo de la ciudad (zonas) | CUMPLE VERIFICADO | `construir_grafo_ciudad`, `distancias_zona` (BFS); pantalla `arena_mapa` | T1 `test_grafo_ciudad_y_distancias`; capturas T4 (zona resaltada) | — |
| 6 / p.5 | Grafo social (amistad, confianza, seguimiento) con función en el juego | CUMPLE VERIFICADO | `GrafoSocial.py` (dirigido y ponderado), `construir_grafo_social` | T1 `TestGrafos` | — |
| 6 / p.5 | Implementar y demostrar operaciones de grafos | CUMPLE VERIFICADO | agregar/eliminar vértice y arista, vecinos, predecesores, BFS, BFS multifuente, DFS | T1 `test_operaciones_basicas`, `test_bfs_multifuente_bloqueos_y_aislados` | — |
| 6, 18 / pp.5, 12 | Integración con árboles y visualización del grafo | CUMPLE VERIFICADO | La hoja del árbol decide fuentes y bloqueos del BFS (`resolver_ronda`); se dibuja con `grafo_red` | Capturas T4 `*_resultado` | — |
| 7 / p.6 | Propagación: quiénes, cuántos, qué tan rápido, si era verdadera y qué consecuencias | CUMPLE VERIFICADO | `resultado`: `alcanzados`, `n_alcanzados`, `saltos`, `velocidad`, `publicacion.tipo`, `delta_indicadores` | T1 `test_reportes_frenan…`; captura del resultado | — |
| 8 / pp.6–7 | Eventos aleatorios (los 7 del PDF) que varían entre partidas | CUMPLE VERIFICADO | `reglas.EVENTOS`; azar con semilla (`random.Random`) | T1 `test_misma_semilla_misma_partida_y_semillas_distintas_varian` | — |
| 8 / p.7 | Componentes que dependen de la habilidad, no solo del azar | CUMPLE VERIFICADO | Decisiones del árbol, minijuegos de la historia (Moderación, Caza-Rumores, Rastreador, Duelo, Viralización) | T1, T5 | — |
| 9 / p.7 | Tiempo limitado para actuar en momentos concretos | CUMPLE VERIFICADO | Ronda con límite de 25 s (×0,6 si se vuelve viral), controlado por el servidor; pausa del anfitrión | T1 red `test_tiempo_agotado…`, `test_pausa_congela…`; captura «Tiempo restante» | — |
| 10 / pp.7–8 | Indicadores que cambian durante la partida y deciden el resultado | CUMPLE VERIFICADO | `Partida.indicadores`; cabecera con variación por ronda | Capturas T4; T1 | — |
| 11 / pp.8–9 | Puntuación individual y resultado general de la ciudad | CUMPLE VERIFICADO | `Jugador.puntos/reputacion/logros`; `resultado_ciudad()` | Captura final de T4; T1 | — |
| 11 / p.8 | Reputación, confianza, puntos, logros, recompensas y sus pérdidas | CUMPLE VERIFICADO | `_valorar`, `_logros` (Verificador/a, Cortafuegos, Voz de confianza, Debate limpio, Siempre presente) | Capturas T4 (logros desbloqueados) | — |
| 11 / p.9 | Retroalimentación sobre las consecuencias | CUMPLE VERIFICADO | Pantalla de resultado: nota personal, acciones de cada jugador, propagación | Capturas T4 | — |
| 12 / p.9 | Elección final ligada al comportamiento (confianza, reputación, participación, conflictos, verificación) | CUMPLE VERIFICADO (Arena) · PARCIAL (historia) | `elegir_alcalde()`: confianza de cada ciudadano, reputación del jugador Candidato, participación que fija la abstención y causas registradas | T1 `test_eleccion_depende…`, `test_rumores_cambian_el_ganador`, `test_participacion…`; captura «¿Por qué ganó?» | En la historia, los cinco finales narran el resultado electoral sin un recuento de votos. |
| 13 / pp.9–10 | Multijugador local con arquitectura cliente-servidor, preferiblemente sockets | CUMPLE VERIFICADO (en un PC) · NO VERIFICABLE (varios PCs) | `clases/arena/servidor.py`, `cliente.py`, `protocolo.py`; `servidor_arena.py` | T1 red (12 pruebas, procesos independientes); T4 | Probado con procesos independientes por TCP en 127.0.0.1. Falta una prueba física con varios PCs en una LAN y el firewall de Windows: **PENDIENTE DE PRUEBA FÍSICA**. |
| 13 / p.10 | El servidor mantiene y sincroniza estado, jugadores, publicaciones, relaciones, eventos, puntuaciones, turnos e información compartida | CUMPLE VERIFICADO | Ver la tabla de `docs/ARQUITECTURA_MULTIJUGADOR.md` | T1 `test_2_3_y_4…` (estado final idéntico en todos), `test_acciones_simultaneas…` | — |
| 14 / p.10 | Interfaz gráfica: ciudad, personaje, publicaciones, opciones, estado, puntuación, indicadores y resultados; no solo consola | CUMPLE VERIFICADO | `arena/arena.rpy`, `screens.rpy`, historia | Capturas T4 y T5 | Comprobado a 1739×978, 1366×768 y 1600×720 en modo táctil (auditoría anterior). En la Arena solo a 1739×978. |
| 15 / pp.10–11 | Al menos un componente inclusivo y explicar qué dificultad atiende | CUMPLE VERIFICADO | **Avisos visuales de sonido** (`sfx()` en `story/rutas.rpy`, pantalla `aviso_sonido`, opción en Accesibilidad); subtítulos permanentes; reducir movimiento; formas además de colores | Captura de T4 (cliente: «SONIDO ¡Logro!»); AYUDA → Accesibilidad | Atienden: pérdida auditiva o jugar sin audio en la feria, mareo por movimiento y daltonismo. Los avisos solo salen para los sonidos que pasan por `sfx()`. |
| 16 / p.11 | AYUDA con objetivo, reglas, botones, personajes, cómo ganar e indicadores | CUMPLE VERIFICADO | `game/ayuda.rpy` (7 pestañas), accesible desde el menú principal, el menú del juego y la Arena | Capturas T4 `*_95_ayuda_arena`, `*_96_ayuda_indicadores` | — |
| 16 / p.11 | Mensajes durante la partida que orienten | CUMPLE VERIFICADO | Arena: rol y habilidad, reloj y nota por ronda; historia: tutoriales de cada minijuego y avisos | Capturas T4 y T5 | — |
| 17 / pp.11–12 | Elementos motivadores funcionales (sonidos, animaciones, recompensas, logros, efectos al ganar o perder) | CUMPLE VERIFICADO | Logros y puntos de la Arena, sonidos por resultado y alarma de 5 s, animaciones del grafo, resultados de los minijuegos | Capturas T4 y T5 | Nadie ha escuchado el audio todavía: pendiente de escucha humana. |
| 18 / pp.12–13 | Entrega final integrada y estable | PARCIAL | Todo lo anterior | T1–T5 | Faltan las pruebas físicas (LAN, mando, teléfono) y con personas. |
| 19 / p.13 | Repositorio Git con commits de cada integrante | NO VERIFICABLE | `AC020907/pruebaslaboratorio` (pruebas) y `AC020907/alcalde_digital` (equipo) | `git log` | Aquí solo hay commits de la cuenta del usuario. **No se falsifica autoría**: cada integrante debe subir su parte desde su cuenta al repositorio del equipo. |
| 20 / pp.13–14 | Todos explican diseño, código, árboles, grafos, interfaz, cliente-servidor, decisiones y mecánicas | PREPARADO | `docs/GUIA_SUSTENTACION.md` | — | Depende de que el equipo lo estudie. |
| 21 / pp.14–15 | Feria: creatividad, interfaz, interacción, funcionamiento, simulación, aprendizaje y presentación | PREPARADO | `docs/PLAN_DE_PRUEBAS_FERIA.md`, guion de demostración | — | Pruebas con personas pendientes. |

## Defectos encontrados y corregidos en esta fase

| Defecto | Corrección |
|---|---|
| No existía el multijugador cliente-servidor, ni los 4 roles, ni los 4 candidatos, ni la elección | Arena Civitas completa (motor, servidor, cliente, interfaz y pruebas). |
| `ArbolDecisiones` no podía eliminar, buscar ni medir; `GrafoSocial` no podía quitar vértices ni aristas | Operaciones añadidas y probadas. |
| No había una sección AYUDA completa (solo la de controles de Ren'Py) | `ayuda.rpy`, con 7 pestañas. |
| El anfitrión era quien llegaba primero, y otra persona podía quedarse con la sala | Clave de anfitrión del equipo que crea la sala, con prueba. |
| Los clientes no recibían las cuentas de jugadores que se unían después | El grafo se difunde al empezar, con prueba. |
| El botón «Verificar» mostraba la pista antes de elegirlo | Ahora muestra la etiqueta; la pista aparece al entrar. |
| Las aristas se cortaban en x=1260 en la pantalla ancha | La capa de aristas acepta un ancho propio. |
| Glifos ●, ✓ y ♪ que la fuente no tiene | Se sustituyeron por formas o texto. |
