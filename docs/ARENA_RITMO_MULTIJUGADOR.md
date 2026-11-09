# Duelo de Frecuencias: modo competitivo (final del torneo)

**Recursos:** canciones, charts y sprites propios del proyecto (`game/ritmo/*.json`, `assets/audio/music/duelo_*.ogg`, `gui/ritmo/*`). No usa nada de otros juegos de ritmo.

## Juego

- **Carriles:** 4 por cliente. Se juegan con D F J K, las flechas o el mando, igual que en la Historia.
- **Chart:** el mismo para todos, `duelo_<modo>_normal.json` (98 notas en el completo y 43 en la Feria). Lo valida `Ritmo.validar_chart` en el cliente y en el servidor.
- **Juicios:** se usan las ventanas de la dificultad Normal.

| Juicio en pantalla | Interno | Ventana | Valor | Combo |
|---|---|---|---|---|
| PERFECT | `perfect` | ±45 ms | 100 % | Suma |
| GREAT | `good` | ±90 ms | 70 % | Suma |
| GOOD | `bad` | ±135 ms | 30 % | Lo rompe |
| MISS | `miss` | — | 0 % | Lo rompe |

- **Sincronía:** `Ritmo.RelojCancion` sigue la posición del audio (no el reloj del sistema) con el desfase calibrado del jugador (`persistent.ritmo_offset_ms`). Cada cliente juega con su propio audio. El torneo no exige que las canciones empiecen a la vez: compara precisión, no tiempos absolutos.

## Presentación

- **Antes del duelo:** la pantalla de la prueba lo anuncia como «PRUEBA 5 DE 5 · FINAL», con el botón «¡AL DUELO FINAL!». Después, `arena_duelo_intro` muestra el título animado, el número de notas, los cuatro juicios con su color y los controles.
- **Durante el duelo:** NOVA y el aliado reaccionan a los combos, como en la Historia.
- **Después del duelo:**
  - `arena_resumen_prueba`: barras por jugador con precisión y combo máximo, y la clasificación acumulada. El botón del anfitrión pasa a «Ver la elección ›».
  - `arena_final_torneo`: campeón con animación, desglose por prueba, ganadores de cada prueba, elección y resultado de la ciudad.

## Puntuación en el servidor

`torneo.puntuar_ritmo`:
1. Exige `dificultad == "normal"` y exactamente un juicio válido por nota del chart.
2. Recalcula la precisión, `Σ valor(juicio) / notas`.
3. Recalcula el combo máximo (solo `perfect` y `good` lo encadenan).
4. Puntúa con `850·precisión + 150·combo_máx/notas`. Un juego perfecto da 1000.

Las notas que el cliente no juzgó (por ejemplo, si abandonó) se envían como `miss`.

## Limitación

El instante de cada pulsación se mide en el cliente. El servidor no puede distinguir unos juicios reales de unos inventados que sean coherentes. Mitigaciones:
- longitud exacta del chart;
- dificultad fija;
- combo recalculado.

En una LAN de laboratorio se considera suficiente. Ver `ARENA_TORNEO.md` §Limitaciones.
