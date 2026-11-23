# Ruta de la Verdad 2: remasterización jugable y visual

**Qué es:** la remasterización del plataformero que ya teníamos, no un juego distinto. Conserva:
- la plataforma 2D y la infiltración en el sistema de NOVA;
- las evidencias, los saltos, los obstáculos y los puntos de control;
- la victoria y la derrota;
- el mismo contrato de resultado (`"viralizacion"`), así que finales, expediente y puntuación no cambian.

El motor sigue siendo determinista, con enteros y a 60 ticks/s, con paridad exacta en el navegador y rejuego en el servidor.

**Rama:** `feature/minijuegos-feria`. **Punto de recuperación:** tag `checkpoint-pre-minijuegos-feria`.

## Qué estaba mal (comprobado) y qué se hizo

| Problema comprobado | Prueba | Cambio |
|---|---|---|
| Niveles planos: los cuatro eran tramos de 8 filas encadenados al mismo nivel de suelo, y los dos tercios superiores de la pantalla quedaban vacíos | Captura `docs/remaster/comparativas/plataformero_juego_r3.jpg` | Niveles verticales de 13 filas diseñados a mano por zonas (ver «Diseño de niveles») |
| Poca variedad: solo correr, saltar, pinchos y bloques intermitentes | Inventario de piezas de los mapas | Tres piezas nuevas, sencillas y deterministas (abajo) |
| La cámara se suavizaba un 18 % **por cuadro**: a 160 FPS reaccionaba casi 3 veces más rápido que a 60 | Código de `render` (multiplicaba por 0,18 en cada cuadro) | Suavizado exponencial **por tiempo** (`1 − e^(−8,5·dt)`), igual en Ren'Py y en la web |
| Al cambiar de sentido, la anticipación de 260 px saltaba de golpe al otro lado (giro de 520 px) | Mismo código | La anticipación gira suavemente (`1 − e^(−2,6·dt)`) |
| El HUD decía «1 / 5» y no se sabía en qué parte del sistema se estaba | Captura del remaster 3 | Casillas de evidencia que se llenan, barra de tiempo, zona actual y cartel de zona |

**Física: sin cambios.** Las medidas actuales funcionan y las pruebas lo confirman:
- el salto sube ~2,5 tiles y es variable;
- coyote time de 100 ms y jump buffering de 117 ms;
- velocidad máxima de 285 px/s;
- corrección de esquina de 7 px;
- reaparición en 0,6 s con parpadeo.

Ningún dato pedía tocarlas, así que no se cambió ninguna constante. Lo único nuevo en el motor son las tres piezas.

## Piezas nuevas (motor y web)

| Pieza | Tile | Regla | Para qué |
|---|---|---|---|
| **Pasarela de datos** | `=` | Solo frena cayendo, si los pies estaban por encima de su borde antes de ese tick. Se atraviesa saltando desde abajo y no es pared | Niveles por capas: subir por debajo, rutas altas y bajas |
| **Impulsor** | `J` | Bloque sólido; al apoyarse lanza a `V_IMPULSO = −268` (~4,6 tiles). Ese salto **no** se recorta al soltar el botón | Llegar a repisas a 4 tiles y a rutas altas sobre fosos |
| **Escáner de NOVA** | `L` | Haz vertical con ciclo de 150 ticks: 66 barriendo (letal) y aviso 30 ticks antes. Cada columna va desfasada 37 ticks, así que varios escáneres seguidos forman una ola. Detecta solo encendido, con la caja de daño más estrecha que el tile | Tramos de ritmo: esperar el hueco |

Las tres están en `game/clases/Plataformas.py` y `leaderboard/app/static/plat_motor.js`; `config_cliente` envía sus constantes al navegador.

## Diseño de niveles

Tramos verticales de 13 filas, diseñados a mano y medidos con la física real:
- cada repisa está a 2 tiles (salto) o a 4 (impulsor) de la anterior;
- ningún hueco pasa de 3 tiles.

Los niveles se organizan en **zonas**: se cambia de zona en cada punto de control, con un arco en el fondo y un cartel al entrar.

| Zona | Enseña | Tramos |
|---|---|---|
| 1 · Puerta de enlace | Pasarelas, huecos y el primer impulsor | `entrada`, `escalones` (bloques escalonados y una pasarela con evidencia), `foso` (pasarelas como piedras sobre pinchos), `impulso` (repisa alta a 4 tiles) |
| 2 · Granja de bots | El tiempo | `inestable` (puente que se apaga sobre pinchos), `escaneres` (dos escáneres desfasados con una evidencia entre ellos), `dos_alturas` (pasarelas a dos alturas sobre un foso) |
| 3-4 · Núcleo de NOVA / Archivo | Combinaciones | `cadena` (impulsor → pasarela larga sobre pinchos), `barrido` (puente intermitente + escáneres), `torre` (escalada de tres alturas con la evidencia arriba) |

| Nivel | Uso | Tamaño | Evidencias | Tiempo | Ruta verificada |
|---|---|---|---|---|---|
| `tutorial` | — | 91 × 13 | 4 | 60 s | 15,9 s |
| `feria` | Modo Feria, torneo Feria y Arena Online | 125 × 13 | 5 | **75 s** (antes 55) | 23,1 s |
| `arena` | Torneo LAN completo | 153 × 13 | 6 | 80 s | 27,0 s |
| `historia` | Historia (domingo) | 185 × 13 | 8 | 120 s (± ayuda de aliados) | 33,3 s |

Ningún nivel ni contenido se eliminó. Los mismos cuatro niveles conservan su número de evidencias, y los tramos antiguos se conservan en el código como `TRAMOS_V1`.

**Tiempo de Feria:** pasó de 55 a 75 s porque el nivel creció de 77 a 125 columnas. Con 75 s, la ruta perfecta ocupa el 31 % del tiempo, igual que en Arena (34 %).

**Alcanzabilidad demostrada.** `tools/plataformas_rutas.py` busca con A* ponderado sobre el motor real, con macro-acciones de 4 ticks. Va de evidencia en evidencia hasta la meta, sin morir nunca, e incluye en el estado la fase de intermitentes y escáneres cuando están cerca. Las rutas se guardan en `game/clases/plataformas_rutas.json` y la prueba `test_todos_los_niveles_se_pueden_completar_con_todas_las_evidencias` las rejuega. Las mismas rutas mueven:
- la QA visual (`PilotoRuta`);
- los bots de la Arena: con menos habilidad abandonan antes y solo valen las evidencias que ya recogieron.

## Presentación

- **Piezas con forma propia, no solo color:**
  - pasarela con bordes y luz lila debajo;
  - impulsor con flechas que se comprime al usarse;
  - escáner con emisor y tres estados (guía punteada, aviso parpadeante y haz).
- **Decoración del fondo** colocada según el nivel:
  - arcos de zona en el inicio y en cada control;
  - carteles de aviso antes de cada peligro y una flecha antes de cada impulsor;
  - racks y pantallas de NOVA con frases del rumor;
  - tono de color por zona.
- **Meta:** columna de luz ámbar sobre el archivo, que se intensifica al llegar.
- **Efectos (en la paleta, moderados):**
  - polvo al correr;
  - salto y aterrizaje (squash);
  - ráfaga turquesa del impulsor;
  - «+1 FRAGMENTO» flotante y la casilla del HUD que late;
  - destello de detección;
  - onda en el control y cartel de zona;
  - destello «ARCHIVO RECUPERADO».

  Con «Reducir movimiento» se quitan el polvo, el temblor y los giros.
- **HUD:**
  - título y zona actual;
  - casillas de evidencia;
  - tiempo con barra, que se pone roja en los últimos segundos;
  - detecciones;
  - línea de ruta con los puntos de control y el archivo.
- **Presentación inicial:** las siete piezas con su explicación en una línea.
- **Arena Online:** el mismo arte y las mismas piezas en `arena.html` (WebP), con la cámara corregida igual.

## Pruebas

| Prueba | Resultado |
|---|---|
| `tests/test_plataformas.py` (27) | Rutas verificadas en los 4 niveles (todas las evidencias, 0 detecciones, < 55 % del tiempo); piezas nuevas presentes; zonas; bots ordenados por habilidad; pasarela atravesable desde abajo y que sostiene al caer; impulsor de 4-5 tiles sin recorte; escáner letal solo encendido y desfasado; física anterior intacta (gravedad, paredes, salto único, variable, coyote, buffer, caída, control, esquina, intermitentes); puntuación; rejuego; trazas manipuladas; independencia de los FPS |
| `tests/test_plataformas_web.py` | Paridad JS/Python tick a tick en 4 niveles × 6 perfiles (incluye la ruta verificada con ruido: impulsores, pasarelas, escáneres) y el servidor acepta la traza del navegador |
| `qa_visual.py galeria --etapas ruta` | Motor real, nivel Historia: **S, 8/8 evidencias, 0 detecciones, 33,3 s**, ~119 FPS con la captura activa. Fotos de la presentación, de cada zona, del impulso, del escáner, de la victoria y del resultado |
| `qa_visual.py galeria --etapas minijuegos` | La Ruta en el flujo de minijuegos (nivel Feria) |

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

- La curva de dificultad se verificó con una ruta óptima y bots, no con personas. El margen de tiempo para jugadores reales es una estimación (ruta perfecta ≈ 30 % del tiempo).
- No hay plataformas móviles ni enemigos que persigan. Se eligieron piezas que no rompen la paridad tick a tick con el navegador.
- La Arena Online con los niveles nuevos necesita el Manual Deploy en Render.
