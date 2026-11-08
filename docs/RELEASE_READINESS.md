# Release readiness: cumplimiento de la rúbrica y Arena Civitas

- **Rama:** `feature/arena-rubrica`, que sale de `main` `8608dc2` (versión publicada el 2026-11-05).
- **Fecha:** 2026-11-07.
- **SDK:** Ren'Py 8.5.3.
- **Estado:** commit local en la rama. **Sin push, sin merge a `main` y sin publicación web:** requieren autorización.
- **Veredicto:** **GO condicionado** para la entrega final (16–20 nov). No queda ningún defecto bloqueante conocido. Faltan las pruebas físicas y con personas de §5.

## 1. Qué se añadió

| Área | Cambio | Archivos |
|---|---|---|
| Multijugador (§13) | Arena Civitas: servidor TCP autoritativo, cliente, protocolo versionado, sala, rondas, pausa, reconexión, bots y servidor dedicado | `game/clases/arena/*`, `game/arena/arena.rpy`, `servidor_arena.py` |
| Roles (§4) | Ciudadano, Periodista, Influencer y Candidato, con árbol, alcance, bloqueos y puntos propios | `reglas.py`: `arbol_para`, `_conectar_jugador`, `resolver_ronda`, `_valorar` |
| Árbol (§5) | `buscar`, `eliminar`, `recorrer_ruta`, `hojas`, `altura` y `tamanio`; enlace `padre` | `Tree.py`, `Node.py` |
| Grafos (§6–7) | `eliminar_usuario`, `eliminar_conexion`, `bfs_multifuente`; grafo de la ciudad; propagación integrada con el árbol | `GrafoSocial.py`, `reglas.py` |
| Elección (§12) | 4 candidatos; voto por la confianza de cada ciudadano, la reputación del Candidato y la participación; explicación causal | `reglas.elegir_alcalde` |
| Ayuda (§16) | Pantalla AYUDA con 7 pestañas en el menú principal, el menú del juego y la Arena | `game/ayuda.rpy`, `screens.rpy` |
| Inclusión (§15) | Avisos visuales de sonido (opción en Accesibilidad) | `story/rutas.rpy` (`sfx`, `aviso_sonido`) |
| Documentación | Matriz de rúbrica, estructuras, arquitectura, guía de sustentación y plan de feria | `docs/` |

## 2. Pruebas ejecutadas (2026-11-07)

| Comando | Resultado |
|---|---|
| `python -m pytest -q tests` | **110 OK**: 21 del motor de la Arena, 12 de red, 77 de historia, finales y duelo |
| `cd leaderboard && python -m pytest -q` | **142 OK** |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en historia y en feria |
| `python tests/qa_visual.py galeria …` | Menús, escenas, minijuegos, duelo (S 97 % con pausa) y finales: OK |
| `python tests/qa_visual.py arena …` | 4 procesos (2 Ren'Py + 2 bots): **OK en las 4 ejecuciones posteriores a corregir el anfitrión** (la primera falló por ese defecto), mismo resultado final en los 4 |
| `test_arena_red.py` repetido 3 veces | 3/3 estable |

**Capturas:** las de la Arena están en `docs/auditoria/arena_*.jpg`, junto con `menu_principal_arena_ayuda.jpg` y las comparativas antes/después de la auditoría anterior.

## 3. Defectos encontrados y corregidos en esta fase

Están detallados en `docs/RUBRICA_CUMPLIMIENTO.md` (sección final):
- anfitrión equivocado;
- grafo incompleto en los clientes;
- pista visible antes de verificar;
- aristas cortadas;
- glifos sin fuente;
- botones desbordados en la Arena y en el menú;
- la reconexión no tenía botón en la interfaz.

## 4. Abiertos (no bloqueantes)

| P | Tema | Nota |
|---|---|---|
| P2 | La historia individual no muestra 4 candidatos ni un recuento de votos | La Arena cubre §3 y §12. La historia es un modo complementario. |
| P3 | La Arena solo se capturó a 1739×978 | La interfaz usa coordenadas virtuales de 1920×1080 y Ren'Py escala; no se ha visto a 1366×768. |
| P3 | La Arena no está en la web | Limitación de los navegadores (sin TCP), documentada. |
| P3 | Los avisos visuales cubren los sonidos de `sfx()`, no la música | Las voces ya tienen subtítulos. |

## 5. Pendiente de prueba física o humana

1. **Arena en una LAN real** con 2, 3 y 4 PCs, incluyendo el firewall de Windows y un corte de cable con «Reconectar».
2. **Mando físico** en la historia y en la Arena.
3. **Teléfono real** con la web y el QR.
4. **Escucha humana** de voces, música y duelo.
5. **Sesiones con personas:** `PROTOCOLO_PRUEBAS_JUGADORES.md` para la historia y el plan de feria para la Arena.
6. **Commits por integrante** en el repositorio del equipo: cada persona desde su cuenta. Aquí no se falsifica autoría.

## 6. Publicación (cuando se autorice)

1. Merge de `feature/arena-rubrica` a `main` y push.
2. Build de escritorio (Windows) para la Arena, con el lanzador de Ren'Py: *Build Distributions → PC*.
3. Build web (`DESPLIEGUE.md` §3–4) y copia a `gh-pages`. La web recibe la AYUDA y el menú nuevos; la Arena muestra en ella el aviso de «solo escritorio».

**Rollback:** `git revert -m 1 <merge>` en `main`, y revertir el último commit de `gh-pages`. No hay cambios de backend ni de base de datos.
