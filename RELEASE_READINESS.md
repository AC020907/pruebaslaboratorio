# Release candidate: Civitas con Duelo de Frecuencias

- **Rama:** `feature/duelo-frecuencias`, fusionada en `main` (merge `5279ad1`).
- **Punto de retorno:** tag `rc-estable-pre-ritmo` (versión anterior).
- **Fecha:** 2026-11-05.
- **Estado: publicada.**
  - **Web:** GitHub Pages (`gh-pages` `a958de0`) sirve esta versión en `https://ac020907.github.io/pruebaslaboratorio/`. Arranca y llega al menú.
  - **Servidor:** Render responde `{"ok":true,"db":"ok"}`. Falta un *Manual Deploy* de `main` en Render para servir `/static/qr.png` (hoy 404). El juego no depende de ese archivo: el QR va dentro de la build web.

## 1. Qué cambió

### Duelo de Frecuencias (quinto reto, original)
- **Motor puro:** `game/clases/Ritmo.py`. Incluye validación de charts, juez con ventanas configurables (Perfecto ±45 ms, Bien ±90 ms, Justo ±135 ms), combo, precisión, nota y la máquina de estados `countdown → playing ⇄ paused → results/aborted`.
- **Reloj de canción:**
  - usa la **posición real del audio** (`renpy.music.get_pos`);
  - extrapola entre los bloques del motor de audio;
  - usa el reloj de pared si el audio no informa nunca, por ejemplo en algunos navegadores;
  - no retrocede ni salta al reanudar.
- **Pantalla:** `game/minijuegos/ritmo.rpy`.
  - **Interfaz:** 4 carriles con forma propia (círculo, rombo, triángulo, cuadrado), de modo que no dependen del color.
  - **Personajes:** NOVA y el aliado del domingo reaccionan a combos y fallos.
  - **Indicador:** muestra señal frente a interferencia, con texto y porcentaje.
  - **Flujo:** cuenta atrás, pausa real que congela el audio, abandono seguro y resultados.
- **Dificultades:**
  - **Normal.**
  - **Fácil:** solo pulsos enteros y sin acordes; es la opción por defecto en pantallas táctiles.
  - **Asistido:** ventanas más amplias y meta del 45 %.
- **Calibración:** de ±200 ms, y velocidad visual de 0,75, 1 o 1,25, guardadas en el equipo.
- **Música original:** `tools/musica/duelo.py` genera `duelo_historia.ogg` (72 s) y `duelo_feria.ogg` (36 s) a 120 BPM, con llamada (NOVA) y respuesta (la señal de Ciudad Nova). Los **charts se derivan de los mismos eventos que suenan**: `game/ritmo/*.json`, 98 y 69 notas en historia, 43 y 29 en feria.
- **Nada de Friday Night Funkin':** no se copió música, sprites, charts, iconos ni código. Solo se tomó como referencia la mecánica observable: carriles, juicio por tiempo y llamada y respuesta.

### Narrativa e integración
- **Escena nueva:** `duelo_transmision` (en `story/elecciones.rpy`). El domingo, NOVA secuestra la transmisión oficial antes de la Gran Viralización. Se juega en historia y en feria.
- **Si ganas:** hecho `duelo_ganado`, consecuencias en la ciudad y **+1500 de umbral** en la Gran Viralización (`BONO_DUELO` en `story/rutas.rpy`). Se anuncia en pantalla.
- **Si pierdes:** hecho `duelo_perdido` y un impacto leve. No bloquea ningún final.
- **Los cinco finales no cambian de requisitos:** el duelo es un factor más.

### Puntuación y leaderboard
- **Escala intacta:** la Puntuación Cívica sigue en 0–1000. El componente "minijuegos" mantiene su máximo de 200 y ahora se reparte entre 5 retos.
- **Backend sin cambios de contrato:** las 142 pruebas pasan. Solo cambió la prueba del QR, que ahora acepta que el QR exista.
- **Datos ya publicados:** siguen siendo válidos.

### Correcciones de esta fase
- **Recorridos de QA contra producción:** en esta copia existe `game/leaderboard_url.txt`, así que los recorridos enviaban partidas al servidor de producción. Ahora QA nunca usa el servidor salvo con `--api`. Las 10 partidas de prueba ya enviadas están marcadas como **no verificadas**: no aparecen en la tabla pública. Ver §5.
- **Prueba del backend** que fallaba porque ya existe el QR.

## 2. Matriz de verificación

| Elemento | Implementado | Probado automáticamente | Probado visualmente | Escuchado | Hardware real |
|---|---|---|---|---|---|
| Motor rítmico (juicio, reloj, pausa, FPS) | Sí | 21 pruebas | — | — | — |
| Charts válidos y sincronizados con el audio | Sí | Sí: notas en la rejilla de 125 ms, duración ±60 ms, ataque de la señal a +10/+30 ms de la nota | — | **No** | — |
| Duelo dentro del motor real (feria 43 notas, historia 98) | Sí | Sí: 100 % Perfecto con el jugador automático, ningún cuadro de más de 20 ms | Sí: capturas de cuenta atrás, juego y resultados | **No** | — |
| Entrada con teclado (D F J K) | Sí | Eventos simulados: 43 de 43 | — | — | **No** |
| Entrada con mando (cruceta, X A Y RB, Start) | Sí | Eventos simulados: 43 de 43 | — | — | **No** |
| Táctil (tocar el carril, botón Pausa) | Sí | — | — | — | **No** |
| Web (Safari y Chrome móvil) | Respaldo del reloj si no hay posición | Respaldo con prueba unitaria | — | — | **No** |
| Cinco finales con el duelo | Sí | 10 de 10 recorridos | — | — | — |
| Lint de Ren'Py | — | Sin errores | — | — | — |
| Lógica, finales y backend | — | 37, 19 y 142 OK | — | — | — |

## 3. Pendiente (pruebas humanas y de hardware)
1. **Escuchar** `duelo_feria.ogg` y jugarlo una vez en PC. Si las notas se sienten adelantadas o atrasadas, ajusta la calibración en la pausa del duelo.
2. **Mando físico:** el duelo, las decisiones (prioridad heredada) y el resto de retos.
3. **Teléfono real:** el duelo en Fácil con toques, el sonido en iOS después del primer toque y la pausa.
4. **Partida de feria cronometrada:** la estimación es de unos 12 min (~80 líneas, 5 retos), pero no se ha medido con personas.
5. **Pendientes de fases anteriores:** escuchar voces y música, y las sesiones de `PROTOCOLO_PRUEBAS_JUGADORES.md`.

## 4. Cómo se promovió (y cómo repetirlo)
1. Fusiona la rama:
   ```bash
   git switch main && git merge --no-ff feature/duelo-frecuencias && git push origin main
   ```
   Render se redespliega desde `main`.
2. Comprueba el servidor:
   ```bash
   curl https://civitas-leaderboard.onrender.com/api/health?db=1
   ```
   Debe responder `{"ok":true,"db":"ok"}`.
3. Genera y publica la build web (`DESPLIEGUE.md` §3–4): `web_build`, luego `postbuild.py`, y copia sobre la carpeta de la rama `gh-pages` con `git add -A`, `git commit` y `git push`.
4. Abre `https://ac020907.github.io/pruebaslaboratorio/`, juega el duelo y confirma que la partida aparece en la tabla.
5. **Rollback:**
   ```bash
   git switch main && git revert -m 1 <commit del merge> && git push
   ```
   En `gh-pages`, revierte el último commit.

## 5. Limpieza opcional de las partidas de prueba en Neon
Las 10 partidas de QA (2026-11-05, hacia las 17:20 UTC) son no verificadas y no salen en la tabla pública. Si quieres borrarlas, en el *SQL Editor* de Neon revisa primero:
```sql
SELECT run_id, alias, score, created_at FROM scores
WHERE verified = false AND created_at BETWEEN '2026-11-05 17:00:00+00' AND '2026-11-05 17:40:00+00';
```
Si salen exactamente esas partidas de prueba, bórralas con la misma condición:
```sql
DELETE FROM scores
WHERE verified = false AND created_at BETWEEN '2026-11-05 17:00:00+00' AND '2026-11-05 17:40:00+00';
```

## 6. Créditos y licencias
- La música, los efectos y los sprites del duelo (formas de notas) son originales, generados con las herramientas del repositorio (`tools/musica`).
- Las voces usan TTS de Windows (OneCore).
- Las fuentes son Roboto (Apache 2.0).
- No se usaron recursos de terceros sin licencia.
