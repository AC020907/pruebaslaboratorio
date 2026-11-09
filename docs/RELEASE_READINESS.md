# Release readiness: corrección de pendientes, Arena Online y validación final

- **Rama:** `fix/rubrica-online`, que sale de `main` `d3c0a5b` (versión publicada el 2026-11-08). El punto de recuperación es el tag `checkpoint-pre-online`.
- **Fecha:** 2026-11-08. **SDK:** Ren'Py 8.5.3.
- **Estado:** commits locales en la rama. **Sin push, sin merge a `main`, sin despliegue:** requieren autorización.
- **Veredicto:**
  - **Entrega académica: GO condicionado**, a ejecutar `docs/PRUEBAS_FISICAS.md` §A (LAN real).
  - **Arena Online: lista para desplegar**, pendiente de autorización y de la prueba §B con teléfonos.

## 1. Problemas encontrados y corregidos

| Gravedad | Problema | Corrección | Prueba |
|---|---|---|---|
| Alta (educativo) | En la historia, reportar como falsa una noticia **verdadera** daba puntos y bajaba la desinformación (5 de 5 publicaciones verdaderas). Avalar un rumor **falso** («Sí, es verdad») también daba puntos (5 de 5 falsas). | Ramas equivocadas con coste en puntos, reputación e indicadores. Compartir algo falso sin verificar ahora resta puntos. | `tests/test_coherencia_educativa.py` (12) |
| Alta (educativo) | «Verificar» en el teléfono de la historia no mostraba ninguna evidencia: se decidía a ciegas | Cada publicación muestra una pista al verificar (`publicaciones_historia.py`) | Mismo archivo |
| Media | La historia no tenía cuatro candidatos ni recuento de votos (§3, §12) | Línea del tarjetón el domingo y pantalla de **escrutinio** coherente con cada final (`clases/Eleccion.py`) | `tests/test_eleccion_historia.py` (4); [R] 10/10 |
| Media | Choque de nombres: «Lucía» (hija de Rodrigo) y la candidata «Lucía Prado» | La candidata pasa a llamarse **Inés Prado** | — |
| Media | El AVL no tenía ninguna prueba | `tests/test_avl.py`: balanceo, borrado, búsqueda y orden de entrega | 4 pruebas |
| Baja | Al cerrarse el servidor LAN, el cliente decía «se perdió la conexión» en vez de «el servidor se cerró» | El cliente conserva el motivo que envía el servidor | `test_cierre_ordenado_del_servidor` |
| Baja | Documentación con rutas y repositorio antiguos (`alcalde_digital`) en los pasos de despliegue | Se distinguen el repositorio de desarrollo y despliegue (`pruebaslaboratorio`) y el académico (`alcalde_digital`) | — |

## 2. Funcionalidad nueva

**Arena Online (2–4 jugadores por navegador):**
- **Código:** `game/clases/arena/sala.py` (sala sobre el mismo `reglas.py`), `leaderboard/app/arena_online.py` (API HTTPS) y `leaderboard/app/static/arena.html` (página para móvil en `/arena`).
- **Acceso desde el juego:** en la web, el botón Arena abre la versión online; en escritorio hay un enlace en la Arena local.
- **AYUDA:** incluye una sección sobre la Arena Online.

## 3. Pruebas ejecutadas (2026-11-08)

| Comando | Resultado |
|---|---|
| `python -m pytest -q tests` | **131 OK** |
| `cd leaderboard && python -m pytest -q` | **153 OK** (142 del leaderboard + 11 de la Arena Online) |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en historia y en feria, también con las consecuencias corregidas |
| `python tests/qa_visual.py arena --tam 1920x1080` y `--tam 1366x768` | OK en ambas: 4 procesos (2 Ren'Py + 2 bots), los 4 con la misma elección |
| `python tests/qa_visual.py galeria --etapas finales,menus` a 1920, 1366 y 1600×720 táctil | OK en las 3: menús, historial, 5 escrutinios y 5 pantallas de resultados |
| Arena Online en el navegador (local, 2 clientes, viewport 375×812) | Partida completa, misma elección en ambos, recarga con reconexión, sala inexistente con mensaje claro, sin errores de consola |

**Evidencias:** `docs/auditoria/historia_escrutinio_*.jpg`, `arena_1366_resultado.jpg` y `online_0*_*.jpg`.

## 4. Estado

| Área | Estado |
|---|---|
| Rúbrica (ver `docs/RUBRICA_CUMPLIMIENTO.md`) | Todos los requisitos implementados y probados. LAN con varios PCs y audio: requieren prueba física |
| Multijugador local (TCP) | Probado con procesos independientes en un PC (2, 3 y 4). **Sin probar en LAN física** |
| Multijugador online | Probado en local. **No desplegado** en Render; no probado con teléfonos reales |
| Historia | 5 finales alcanzables y escrutinio nuevo |
| Backend y leaderboard | 142 pruebas sin cambios de comportamiento; sin cambios de esquema |

## 5. Pendiente

**Antes de la entrega (16–20 nov):**
1. `docs/PRUEBAS_FISICAS.md` §A: LAN con 2, 3 y 4 PCs.
2. Commits de cada integrante en el repositorio académico.

**Antes de la feria (26 nov):**
1. Autorizar el merge y el **Manual Deploy** en Render (`DESPLIEGUE.md` §6).
2. §B (teléfonos) y §C (mando, audio y sesiones con personas).
3. Regenerar la web y el zip de Windows desde `main` para incluir estos cambios.

## 6. Rollback

- **Código:** `main` no se ha tocado: basta con no fusionar la rama. Si ya se fusionó, `git revert -m 1 <merge>`.
- **Backend:** la Arena Online solo añade rutas. Revertir el commit y redesplegar deja el leaderboard como estaba.
