# Remasterización visual de Civitas

**Ramas:** `feature/remaster-visual` (remaster 1), `feature/remaster-2` y `feature/remaster-3`. **Puntos de recuperación:** tags `checkpoint-pre-remaster`, `checkpoint-pre-remaster-2` y `checkpoint-pre-remaster-3`.

La remasterización cambia **cómo se presenta** el juego, nunca **qué ocurre**. La historia, los diálogos, las decisiones, los finales y el arte oficial de los personajes están intactos, y se puede verificar (ver «Integridad»).

## 1. Integridad verificable

| Comprobación | Herramienta | Resultado |
|---|---|---|
| **Arte oficial** (`game/images/personajes/**`: sprites, laterales, bases; 155 archivos) | `python tools/remaster/inventario.py comparar docs/remaster/inventario_antes.json` (SHA-256) | **Idénticos**. Ningún PNG de personaje se sobrescribió; la presentación usa transforms |
| **Narrativa** (labels, diálogos, opciones con su condición, `call`/`jump` entre labels; 652 elementos en 41 archivos) | El mismo comando. El «antes» se generó desde el tag `checkpoint-pre-remaster` | **Idénticos** |
| **Diálogo oficial de Ren'Py** (identificador, personaje y texto de cada línea; enlaza las voces) | `renpy.exe . dialogue` comparado con `docs/remaster/dialogo_antes.tab` | **Sin diferencias** |
| **Los cinco finales y el secreto** | `python tests/qa_recorridos.py` | **10/10** en Historia y en Feria |

Mostrar una pantalla (`call screen`) se considera presentación y no entra en el inventario narrativo. Las nuevas cartelas de desenlace y el cierre son pantallas; no añaden texto a la historia.

## 2. Dirección artística unificada

La referencia son los sprites oficiales: dibujo plano, contorno definido, expresiones claras. Todo lo nuevo se dibuja con el mismo lenguaje.

| Elemento | Regla |
|---|---|
| **Trazo** | Contorno de tinta `#2b2440` y color plano encima. Nada de degradados, brillos, partículas decorativas ni neón. |
| **Paleta** | Tinta `#2b2440`, papel `#fbf6ee`, noche `#120d1c`, lila `#c9b8d8`, vino `#8c2f4b`. Rojo de emergencia `#d1495b` (rumor y peligro), teal `#2f9e8f` (red ciudadana y lo verificado), ámbar `#e8b04b` (evidencia). |
| **Componentes** | **Tarjeta de papel** con contorno de tinta y franja roja (CivitasNet). Se usa en notificaciones, el rótulo de lugar, el HUD del plataformero y los resultados de los minijuegos. **Remaster 3:** es un kit común en `game/minijuegos/civitas_kit.rpy`: hoja con sombra plana (`ficha_fondo`), botón ficha (`civ_ficha`), cabecera con título en Roboto Light y raya roja (`civ_cabecera`), cierre con la tecla (`civ_cerrar`), chip y sello. Los botones de Ren'Py (`boton_menu_*`, `frame.png`, deslizadores y barras) se regeneraron con el mismo lenguaje (`tools/arte/gui_civitas.py`). |
| **Paleta única** | Remaster 3: se sustituyeron 90 colores heredados de la interfaz anterior (índigo `#5b5bd6`, lavanda `#a7a5f2`, amarillo `#facc15`, menta `#5eead4`, rosa `#e86a7e`) por sus equivalentes de la paleta en todos los `.rpy`, y 31 en la Arena web. Solo cambian colores. |
| **Tipografía** | Roboto Light espaciada para la marca y los títulos (logo, cartelas, título del menú del juego). Roboto en negrita para lo que se lee rápido. |
| **Marca** | **La línea de red con nodos** del logo CIVITAS se repite: en las cartelas de acto (la semana de lunes a domingo, con el acto marcado), en la ruta del plataformero y en las cartelas de los desenlaces. |
| **Movimiento** | La cámara avanza, sigue o se acerca con intención. Las entradas duran 0,35–0,45 s. Con «reducir movimiento» no hay desplazamientos, sacudidas ni zooms. |

## 3. Auditoría y estado por pantalla

Clasificación: **P0** impide comprender o jugar · **P1** presentación grave · **P2** falta de pulido · **P3** opcional.

| Pantalla | Problema encontrado | Prioridad | Mejora aplicada | Evidencia | Estado |
|---|---|---|---|---|---|
| **Ruta de la Verdad: juego** | Bloques rectangulares genéricos, protagonista diminuto (~50 px), fondo de rascacielos neón genérico, HUD en barra negra | P1 | Tileset nuevo con **autotiling** (16 variantes × 2, contorno solo en los lados expuestos, sin costuras). **Parallax en 3 planos**: Ciudad Nova, del panorama oficial entintado; torres de NOVA con pantallas del rumor; cables en primer plano. **Avatar propio del minijuego** redibujado (~108 px, 14 cuadros). Barreras de interferencia animadas con franjas de aviso (forma, no solo color). Plataformas inestables que se agrietan y tiemblan antes de apagarse. **Documentos** como coleccionables. **Antenas** como punto de control, con onda. **Puerta del Archivo** como meta. Polvo y papeles con contorno. Squash al aterrizar, pose al recoger, sacudida y estática al ser detectado, pose de victoria. HUD en fichas de papel y **ruta como línea de red**. | `comparativas/plataformero_juego.jpg`, `capturas/j11_plataformas_juego_b.jpg` | Hecho |
| **Ruta de la Verdad: resultados** | Panel azul marino genérico | P1 | Tarjeta de papel: calificación en círculo, objetivo cumplido o pendiente, cuatro fichas de cifras y **cada documento recuperado con su nombre** | `comparativas/plataformero_resultado.jpg` | Hecho |
| **Ruta de la Verdad: tutorial** | Iconos antiguos | P2 | Iconos y fondo nuevos | `comparativas/plataformero_tutorial.jpg` | Hecho |
| **Moderación Express** | **El título salía cortado** («ÓN EXPRESS»): la cabecera centrada se desbordaba | **P0** | Cabecera reorganizada: título a la izquierda y marcadores a la derecha | `comparativas/moderacion_cabecera.jpg` | Hecho |
| **Resultados de Moderación, Caza-Rumores y Rastreador** | Tres estilos distintos (papel, azul marino, botones azules ajenos a la paleta) | P1 | Componente común `resultado_tarjeta` (`minijuegos/resultado_comun.rpy`), con los mismos textos y cifras de cada motor | `comparativas/moderacion_resultado.jpg`, `rastreador_resultado.jpg` | Hecho |
| **Escrutinio** | Panel estático con las cifras ya puestas | P1 | **Cuenta las cifras exactas del motor** (`Eleccion.escrutinio_historia`): mesas escrutadas 0 → 100 %, barras y votos que suben, «Contando votos…», el ganador revelado al cerrar el conteo y los «¿por qué?» uno a uno. Avatares: Tomás con su **lateral oficial sin modificar**; el resto, con iniciales. Fondo del mapa de la ciudad. | `comparativas/escrutinio.jpg`, `capturas/f01_escrutinio_conteo_informada.jpg` | Hecho |
| **Los cinco finales** | Misma presentación para todos | P1 | Cartela de desenlace (nombre, insignia y lema del Archivo de Destinos) e identidad por final (ver tabla 4) | `capturas/f0*_escena_*.jpg`, `f01_cartela_informada.jpg` | Hecho |
| **Cierre** | Del resultado se volvía al menú sin transición | P2 | Pantalla de cierre con el logo, tu destino, los destinos descubiertos y «Gracias por jugar» (6 s, se puede saltar). Se conserva el Archivo de Destinos. | `capturas/f01_cierre_informada.jpg` | Hecho |
| **Cartelas de acto** | Texto plano sobre negro | P2 | Identidad del logo: el mapa de la ciudad al fondo y la **línea de la semana** con el acto marcado | `comparativas/cartela_acto.jpg` | Hecho |
| **Rótulo de lugar** | Recuadro genérico pequeño | P2 | Tarjeta de CivitasNet con franja roja y el lugar en Roboto Light | `comparativas/rotulo_lugar.jpg` | Hecho |
| **Menú del juego** (Opciones, Guardar, Cargar, Historial, Ayuda, Créditos) | **El título salía cortado por arriba**; la veladura blanquecina parecía sin terminar; las ranuras vacías eran bloques grises | **P0** / P1 | Título visible en Roboto Light con acento rojo. Panel de papel sólido con la columna de navegación en lila y separador de tinta. Ranuras de guardado como tarjetas de papel con contorno. | `comparativas/menu_opciones.jpg`, `menu_guardar.jpg` | Hecho |
| **Prólogo** | — | — | Ya remasterizado (`docs/APERTURA_FERIA_GAMER.md`) | `docs/auditoria/apertura/` | Hecho (rama anterior) |
| **Duelo de Frecuencias** | Notas cayendo en el vacío sin pista; juicio pequeño en amarillo; combo suelto; resultados con otro estilo | P1 | **Pista de carriles** con contorno de tinta, separadores, **línea de golpe** y **pulsos del compás** que bajan al tempo del chart (120 BPM). Brillo del carril al pulsar. **Anillo en el receptor según el juicio**: doble (perfecto), simple (bien/justo), cruz (fallo), así que no depende solo del color. Juicios más grandes con un pequeño golpe de escala, en la paleta: ámbar, teal, lila, gris. Combo en Roboto Light junto a la pista, que late al subir. Título en la tipografía de la marca. Resultados en la tarjeta común. **No cambian** el reloj, el chart, las ventanas de precisión, la música ni las reglas: solo `render()` y las pantallas. | `comparativas/duelo_juego.jpg`, `duelo_resultado.jpg` | Hecho (remaster 2) |
| **Moderación Express (tarjetas)** | Tarjeta genérica; la decisión no se sentía | P2 | El comentario es una **publicación de CivitasNet** (papel, contorno, franja, «comentario reportado»). Al decidir, **la tarjeta sale despedida** hacia su lado con el sello BORRADO o APROBADO y una ligera rotación (con movimiento reducido, solo se desvanece). Cronómetro y botones en fichas con franja roja y teal. La lógica (`ColaModeracion`) no cambia. | `comparativas/moderacion_tarjeta.jpg` | Hecho (remaster 2) |
| **Caza-Rumores, propagación y Gran Viralización (juego)** | Fondo tecnológico neón genérico; barra superior azul marino | P2 | Fondo nuevo: **el mapa ilustrado de Ciudad Nova entintado** (`tools/arte/fondos_minijuegos.py`), así que el grafo se juega sobre la ciudad real. Barra superior en el color noche de la paleta. Los originales quedan en `tools/arte/respaldo_v1/`. | `capturas/j05_contencion_2_juego.jpg` | Hecho |
| **Rastreador (tablero)** | Explicación del error en rojo sobre la foto (poco legible); conclusión elegida con degradado | P1 | La explicación va en una tira de papel con franja roja (la etiqueta de la mesa se oculta mientras se muestra). Los botones de conclusión son planos: vino si está elegida y noche con contorno lila si está disponible. | `capturas/j14_rastreador_error.jpg` | Hecho |
| **HUD de la ciudad** (Ciudad, CivitasNet, Expediente, Misiones, Mapa) | Píldoras azul marino con degradado | P2 | Fichas de papel con contorno de tinta y franja roja al pasar el ratón; los avisos pendientes en un círculo rojo con contorno; el panel de la ciudad, enmarcado | `capturas/e03_barrio_conversacion.jpg` | Hecho |
| **Expediente** | Panel genérico con acentos índigo; la ficha abierta era un rectángulo plano | P2 | Carpeta de investigación: hoja de papel con franja vino, cabecera «Expediente» en Roboto Light, contador de hilos abiertos. Índice con la franja del estado de cada ficha y la elegida en tinta. La ficha abierta es una hoja con clip, franja del estado, título en Light, preguntas abiertas con barra ámbar, conexiones como fichas y **sello** cuando la conclusión está comprobada o refutada. Mismas fichas, textos y acciones. | `comparativas/expediente.jpg` | Hecho (remaster 3) |
| **Misiones** | Lista oscura de bajo contraste; las pendientes casi no se leían | P2 | Diario en papel: cada misión es una ficha con la franja de su estado (en curso ámbar, cumplida teal, pendiente atenuada), etiqueta de estado, título en Light, chips de lugar y minijuego, y contador «cumplidas». | `comparativas/misiones.jpg` | Hecho (remaster 3) |
| **Mapa de Ciudad Nova** | Paneles azul marino genéricos sobre la ilustración | P2 | Barra superior con raya roja y «Ciudad Nova» en Light; misión, controles y lugar cercano como fichas de papel con la franja que corresponde (ámbar si es el destino, rojo si no está disponible). La conducción no cambia. | `comparativas/mapa.jpg` | Hecho (remaster 3) |
| **CivitasNet** | Degradados de otra aplicación (morado-rosa); consejo flotando y botón de píldora | P2 | Fondos de publicación en la paleta según el estado, con trama de semitono, como un afiche (`tools/arte/civitasnet_arte.py`); aro de historias rojo y ámbar; marco lila; botón «Añadir al expediente» en vino. El consejo es una nota de papel junto al teléfono y el cierre una ficha. Los textos y la lógica del feed no cambian. | `comparativas/civitasnet.jpg` | Hecho (remaster 3) |
| **Archivo de Destinos** | Tarjetas correctas, botón lavanda | P3 | Cada destino es una ficha del archivo con la banda de color de su final (la misma de su cartela), insignia sobre la banda, número y barra de progreso de destinos descubiertos. Los ocultos conservan su pista. | `comparativas/archivo_destinos.jpg` | Hecho (remaster 3) |
| **Ruta de la Verdad (segunda pasada)** | Seguía viéndose plano: el fondo y las plataformas tenían el mismo tono morado y la escena no tenía profundidad | P1 | **Cielo** nocturno en bandas con la **señal de NOVA** (disco con ondas) y estrellas, fijo. **Skyline propio** de Ciudad Nova en dos planos, con la torre del cerro, ventanas y bruma en el horizonte. **Torres de NOVA** oscuras con canto iluminado y pantallas del rumor que brillan. **Plataformas con volumen**: pasarela clara, cuerpo que se oscurece hacia dentro, racks con LED, canto con luz y sombra. **Halo ámbar** en los documentos (se ven antes). **Viñeta** que centra la mirada. Tutorial y pausa con la cabecera de la marca; botón de pausa en ficha. El motor, los niveles y la puntuación no cambian. | `comparativas/plataformero_juego_r3.jpg`, `plataformero_tutorial_r3.jpg` | Hecho (remaster 3) |
| **Menú principal y opciones** | Botón activo en lavanda; deslizadores índigo | P2 | Botones como fichas de papel con contorno y sombra plana (el activo, con franja roja); Modo Feria en rojo; deslizadores con relleno vino y perilla de papel. | `comparativas/menu_principal_r3.jpg`, `opciones_r3.jpg` | Hecho (remaster 3) |
| **Duelo de Frecuencias en la Arena Online** | El navegador usaba la versión anterior: sin pista, juicio único en el centro, colores neón | P1 | `dibujarDuelo` (`static/arena.html`) dibuja ahora lo mismo que el Duelo de escritorio: pista con contorno, separadores, **pulsos del compás**, **línea de golpe**, brillo del carril, **anillo por juicio** (doble, simple o cruz) con el texto sobre el carril, combo en trazo fino que late y paleta de Civitas. No cambian el reloj de audio, el chart, las ventanas, la calibración ni el envío del resultado (`ritmo_motor.js` intacto). | `comparativas/arena_web_duelo_r3.jpg` | Hecho (requiere deploy en Render) |
| **Ruta de la Verdad en la Arena Online** | — | — | Recibe el mismo arte nuevo (cielo, viñeta y halo añadidos a `dibujarPlat`; 61 WebP, 158 KB). | `comparativas/arena_web_plataformero_r3.jpg` | Hecho (requiere deploy en Render) |
| **Escenas de la novela** (personajes) | — | — | Ya existían entrada con subida y fundido, respiración, foco que atenúa a quien no habla y reacciones (`funcion_foco`). Se añaden rótulos, cartelas, cámara en la apertura y en los finales. | — | Hecho |
| **Arena Local (LAN)** | — | — | Usa las mismas pantallas de Ren'Py que Historia y Feria, así que recibe el plataformero, los fondos y los resultados nuevos. La red y el protocolo no cambian. | — | Hecho |
| **Arena Online (navegador)** | Plataformero con el arte antiguo; fondos neón | P1 | **Mismo arte que Ren'Py** en WebP: 58 archivos, 128 KB (`tools/arte/exportar_plataformas_web.py`). Se reescribió solo `dibujarPlat` en `static/arena.html`: autotiling, 3 planos, avatar con poses, squash, documentos que flotan, antenas con onda, archivo, partículas con contorno, sacudida y estática al ser detectado, HUD en fichas, `prefers-reduced-motion`. Fondos de los retos de grafo reexportados. **`plat_motor.js` (física) no cambia**: las pruebas de paridad Python/JS pasan. | E2E con Chrome: 2 navegadores, 5 retos, exit 0 | Hecho (requiere deploy en Render) |

## 4. Identidad de cada desenlace

Todo es presentación añadida a las escenas existentes (`story/finales_cine.rpy`); los diálogos no cambian.

| Final | Color | Cámara | Capa | Sensación |
|---|---|---|---|---|
| Ciudad Informada | Tinte cálido, +brillo | Se abre y sube hacia el cielo (9 s) | — | Esperanza, recuperación |
| Ciudad Dividida | Desaturado (0,55) | Fija | **Grieta** que parte la imagen y mitades teñidas de teal y vino | Fragmentación |
| Caos Informativo | Rojo apagado | **Cámara en mano** (desvíos irregulares) | **Publicaciones contradictorias** que se cruzan («GANÓ VEGA», «FRAUDE en la mesa 14»…) | Saturación |
| Mandato Prestado | Frío, muy desaturado | **Se cierra** sobre el poder (14 s) | **Bandas de cine** que estrechan el encuadre | Ambigüedad, encierro |
| Fuente Abierta | Papel cálido | Se abre | **El expediente** se arma: RSN-Scheduler, Resonancia, el informe del Acueducto, @verdad.oculta, unidos con hilo rojo | Revelación |

## 5. Recursos nuevos

- `game/gui/plataformas/v2/` (58 PNG), generados con `tools/arte/plataformas_arte.py`. Es el archivo editable: los parámetros de forma y color están en el código y se regeneran con un comando.
  - Si se quiere mantener el tamaño en disco de la distribución, los PNG antiguos de `gui/plataformas/` se pueden excluir del build; no se borraron.
- `gui/button/slot_*_background.png` y `gui/overlay/game_menu.png`, rehechos.
- No se usó material de terceros. El fondo lejano del plataformero era el panorama oficial del juego, entintado; en el remaster 3 se sustituye por un skyline dibujado con el mismo generador.
- Remaster 3: `tools/arte/gui_civitas.py` (botones, marco y deslizadores de Ren'Py) y `tools/arte/civitasnet_arte.py` (fondos de publicación, aro, marco y botón de CivitasNet). Los originales se guardaron en `tools/arte/respaldo_v1/gui/` y `tools/arte/respaldo_v1/civitasnet/`.

## 6. Rendimiento

| Medida | Antes | Después |
|---|---|---|
| Plataformero (QA de minijuegos, RTX 4070, 1920×1080) | 178 FPS | 140–142 FPS (remaster 1); 131–143 FPS con el cielo, el halo y la viñeta del remaster 3 |

Sigue muy por encima de 60.
- **Capas:** los fondos son dos texturas de 3840 px enlazables más una de cables.
- **Dibujo:** las partículas y la ruta se dibujan con un solo canvas por cuadro.
- **Visibilidad:** los tiles fuera de cámara no se dibujan.
- **Escrutinio y finales:** usan `AnimatedValue` y `DynamicDisplayable` con refresco limitado, y dejan de redibujarse al terminar.

## 7. Pruebas ejecutadas (2026-11-12)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores (3 ejecuciones). Una ejecución intermedia reportó un error transitorio de lectura de `nova_seria.png`; el archivo estaba intacto (hash, git y PIL) y no se reprodujo |
| `python -m pytest -q tests` | **190 OK**: incluye la paridad del motor del plataformero Python/JS (motor sin cambios) |
| `cd leaderboard && python -m pytest -q` | **165 OK** (el backend no se tocó) |
| `python tests/qa_recorridos.py` | **10/10** finales |
| `qa_visual.py galeria --etapas minijuegos` | OK: los 5 minijuegos, con el plataformero completado (S, 5/5) |
| `qa_visual.py galeria --etapas finales` | OK: por cada final, cartela, escena con su identidad, escrutinio contando y revelado, resultados y cierre |
| `qa_visual.py galeria --etapas menus,escenas` | OK |
| `qa_visual.py galeria --etapas apertura` | OK |
| Inventario de arte y narrativa | **Idénticos** |

**Arena Online:** `python tests/e2e_arena_online.py --jugadores 2` contra el servidor local termina con exit 0 (5 retos, campeón y elección).

**Sin verificar:**
- partida completa con mando físico;
- versión web de esta rama (no se publicó);
- pruebas con personas.

## 8. Pruebas del remaster 3 (2026-11-22)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores |
| `python -m unittest discover -s tests` | **190 OK** (incluye la paridad Python/JS de los motores del plataformero y del Duelo) |
| `cd leaderboard && python -m pytest -q` | **165 OK** |
| `python tests/qa_recorridos.py` | **10/10**: los cinco finales en Historia y en Feria |
| `qa_visual.py galeria` (menús, personajes, escenas, minijuegos, Duelo ganado, Duelo sin pulsar, Duelo abandonado, finales, apertura, diálogo, Arena con bots) | **11/11 OK** |
| `qa_visual.py arena` (Arena LAN de escritorio: 2 instancias de Ren'Py y 2 bots, 4 participantes) | OK: 5 rondas, 5 pruebas, campeón y elección |
| `tests/e2e_arena_online.py --jugadores 2,3,4` (Arena Online en Chrome contra el servidor local) | OK con 2, 3 y 4 jugadores: 5 retos, campeón, alcalde y ciudad |
| Inventario de arte (155) y narrativa (652) | **Idénticos** |
| Diálogo exportado por Ren'Py | Identificador, personaje y texto **idénticos**; solo cambian números de línea de `qa_galeria.rpy` (archivo de pruebas) |
| Distribución de Windows (`DigitalMayor-2.0-pc.zip`, 93,4 MB) | CRC correcto; **870 de 870** archivos del juego idénticos byte a byte al código fuente; sin archivos de QA, respaldos ni documentación. SHA-256 `9d5892320e1492e68b8f0e9bcc5de275e9a549b8ee30d681cfb8ad9e0c20e772` |
| Arranque del paquete | Se descomprimió en una carpeta limpia y `DigitalMayor.exe` abrió el menú principal remasterizado, sin `traceback.txt` (`capturas/exe_arranque_r3.jpg`) |
| Versión web (`web_build` + `postbuild`) | 479 archivos revisados: los del juego son idénticos; solo difieren `index.html`, el manifiesto, el service worker y el presplash, que modifica el postbuild. En el servidor local carga el menú y el Archivo de Destinos remasterizados, sin errores en consola |

Moderación Express aparece unas veces como victoria y otras como derrota en la galería: el piloto automático alterna borrar y aprobar sobre comentarios con semilla aleatoria. Ya ocurría antes de estos cambios.
