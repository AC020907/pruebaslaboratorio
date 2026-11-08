# Arquitectura multijugador: Arena Civitas (rúbrica §13, PDF pp. 9–10)

## Resumen

Es un multijugador **local cliente-servidor por sockets TCP** para **2 a 4 jugadores reales**, cada uno en su propio equipo y con un rol distinto. El **servidor es autoritativo**:
- mantiene la partida;
- controla el reloj;
- valida cada decisión;
- calcula la propagación, los indicadores, las puntuaciones y la elección.

Los clientes solo envían lo que el jugador eligió. No hace falta internet: funciona en la red del salón, sin Render ni Neon. La clasificación online del modo historia es un añadido aparte y **no** es este multijugador.

```
                           SERVIDOR  (clases/arena/servidor.py)
                 Partida (reglas.py): árbol + grafo + indicadores + elección
                                     |  TCP 50777, JSON por línea
          ┌──────────────────┬───────┴──────────┬──────────────────┐
      CLIENTE 1          CLIENTE 2          CLIENTE 3          CLIENTE 4
      Ciudadano          Periodista         Influencer         Candidato
   (Ren'Py, equipo A) (Ren'Py, equipo B) (Ren'Py, equipo C) (Ren'Py o bot)
```

El equipo que pulsa «Crear sala» ejecuta el servidor dentro del juego, en un hilo, y además su propio cliente. También existe un servidor dedicado sin interfaz: `python servidor_arena.py`.

## Capas

| Capa | Archivo | Depende de |
|---|---|---|
| Reglas (Python puro, sin red ni pantallas) | `game/clases/arena/reglas.py` | `Tree.py`, `GrafoSocial.py` |
| Protocolo (formato y validación) | `game/clases/arena/protocolo.py` | — |
| Transporte del servidor (sockets, hilos, reloj) | `game/clases/arena/servidor.py` | reglas, protocolo |
| Cliente (socket + cola) | `game/clases/arena/cliente.py` | protocolo |
| Interfaz | `game/arena/arena.rpy` | cliente (y servidor al crear sala) |
| Jugador automático | `game/clases/arena/bot.py`, `tests/arena_bot.py` | cliente |

Gracias a esta separación, las reglas se prueban sin Ren'Py (`tests/test_arena_motor.py`) y la red con clientes reales (`tests/test_arena_red.py`).

## Qué mantiene y sincroniza el servidor (lista del PDF)

| PDF | Dónde | Cómo llega a los clientes |
|---|---|---|
| Estado de la partida | `Partida.fase`, `ronda`, `indicadores` | mensaje `estado`, tras cada cambio |
| Jugadores | `Partida.jugadores` (rol, puntos, reputación, logros, conexión) | `estado.jugadores` |
| Publicaciones | `Partida.publicacion` (la verdad se oculta hasta el resultado) | `ronda.publicacion` y luego `resultado.publicacion` |
| Relaciones | `Partida.grafo` (grafo social con las cuentas de los jugadores) | `bienvenida.grafo` y `grafo` al empezar |
| Eventos | evento aleatorio de la ronda (con semilla) | `ronda.evento` |
| Puntuaciones | `Jugador.puntos` y `reputacion` (solo los calcula el servidor) | `estado`, `resultado.acciones`, `final.ranking` |
| Turnos | rondas simultáneas con límite de tiempo, pausa y continuar | `ronda.segundos`, `estado.restante`, `estado.decidieron` |
| Información compartida | resultado de propagación (alcanzados, protegidos, padres, saltos) | `resultado` |

## Protocolo (versión 1)

Un objeto JSON por línea (`\n`), UTF-8 y como máximo 16 KB. Todo mensaje lleva `v` (versión) y `tipo`.

**Cliente → servidor.** Todos llevan `id`, único por mensaje:

| tipo | campos | regla |
|---|---|---|
| `hola` | `nombre`, `rol`, `token?`, `clave?` | Une a la sala. Con `token` reconecta al mismo puesto. Con `clave` (la conoce solo quien creó la sala) queda como anfitrión. |
| `listo` | `listo` (bool) | — |
| `empezar` | — | Solo el anfitrión. Exige de 2 a 4 jugadores y que los demás estén listos. |
| `accion` | `ronda` (int), `ruta` (lista de int) | Ruta en el árbol del jugador. Debe ser de la ronda actual, terminar en una hoja y ser la primera de la ronda. |
| `pausa` | `pausar` (bool) | Solo el anfitrión. Congela el reloj del servidor. |
| `continuar` | — | Solo el anfitrión. Pasa a la siguiente ronda. |
| `salir`, `ping` | — | — |

**Servidor → cliente:**
- `bienvenida` lleva `jugador_id`, `token`, `anfitrion` y `grafo`.
- `estado` y `grafo` llevan lo que indica su nombre.
- `ronda` lleva `arbol` (el de ese jugador), `publicacion`, `evento` y `segundos`.
- `resultado` y `final` llevan lo que indica su nombre.
- `ack` y `error` llevan `codigo`, `mensaje` y `ref`.
- `cierre` avisa del fin de la sesión.
- Todo lo difundido lleva **`seq`** creciente: el cliente descarta lo que llegue repetido o fuera de orden.

## Robustez

- **Idempotencia:** el servidor recuerda los `id` de cada jugador. Un reenvío tras un corte recibe `ack` con `repetido: true` y no se aplica dos veces.
- **Carreras:** un único `RLock` protege la partida. Las acciones simultáneas se aplican en orden de llegada, pero se **resuelven** juntas y en orden fijo de jugador, así que el resultado es determinista.
- **Validación estricta:**
  - se descartan los campos desconocidos, como `puntos` o `indicadores` enviados por un cliente tramposo;
  - se rechazan los tipos incorrectos, incluido `true` como número;
  - tras 5 mensajes malformados se cierra esa sesión, y el servidor sigue atendiendo.
- **Tiempo:** el servidor fija el límite de cada ronda. Si se agota, quien no decidió cuenta como «sin respuesta», que resta participación.
- **Desconexión:**
  - en el lobby se libera el puesto y el rol;
  - en juego, el puesto se conserva (`conectado: false`) y la ronda no se bloquea esperándolo;
  - con su `token` vuelve al mismo puesto y recibe la ronda en curso.
- **Cierre ordenado:** `detener()` envía `cierre` a todos antes de cerrar los sockets.
- **Seguridad:** el cliente nunca calcula puntos. La verdad de la publicación no viaja hasta el resultado, y la fuente real solo va en el árbol del periodista.

## Por qué TCP y no otra cosa

- **TCP:** el PDF pide sockets. TCP garantiza el orden y la entrega, que es lo que importa en un juego por turnos de pocos jugadores.
- **JSON por línea:** se puede leer en la sustentación y depurar con `telnet`.
- **Navegadores:** no abren sockets TCP. Por eso la versión web **no** incluye la Arena y muestra un aviso para usar la de escritorio. Llevarla al navegador exigiría un adaptador WebSocket, que **no** está hecho.

## Cómo probarlo

```bash
python -m pytest -q tests/test_arena_red.py
python tests/qa_visual.py arena --salida <carpeta>
```

**`pytest`** cubre 12 pruebas:
- 2, 3 y 4 clientes en hilos y en **procesos independientes**;
- acciones simultáneas, tiempo agotado, pausa, ids repetidos y puntos falsos;
- mensajes malformados, reconexión con token, anfitrión por clave, roles duplicados y sala llena.

**`qa_visual.py arena`** lanza 4 procesos (2 Ren'Py con interfaz y 2 bots), juega la partida entera y guarda capturas de cada fase. Los 4 llegan al mismo resultado.

**En una LAN real** (no se ha podido probar aquí con varios PCs):
1. Ejecuta el juego de escritorio en el equipo anfitrión y elige «Arena (2-4 jugadores)» → «Crear sala». Permite el acceso cuando lo pregunte el firewall de Windows.
2. En los demás equipos, elige «Unirse» y escribe la IP que muestra la sala.
