# Duelo de Frecuencias · modo DIFÍCIL (5 carriles)

## Música: por qué no es Megalovania

Megalovania (Toby Fox) es una obra protegida y el proyecto no tiene licencia para usarla. Así que **no se usa la canción ni se copia su melodía**. En su lugar hay una pista original, `duelo_dificil.ogg`, generada por código con `tools/musica/duelo_dificil.py`. Busca una energía parecida: tempo rápido, riff insistente en el registro medio-agudo, bajo en corcheas y una batería con caja en 2 y 4. La melodía, la escala, la armonía y la estructura son propias.

| Dato | Valor |
|---|---|
| Tempo | 144 BPM, 4/4, 27 compases (unos 45 s) |
| Escala | Mi menor pentatónica extendida (E4 a D6) |
| Secciones | cuenta (0-1) · riff (2-5) · llamada y respuesta con NOVA (6-9) · dobles (10-13) · medio tiempo (14-17) · clímax (18-23) · acorde final (24) |
| Notas jugables | 199, de ellas 31 dobles (Normal: 98; Fácil: 43) |

## Cómo se diseña el chart

- **Cada nota del chart es una nota real de la melodía.** El script genera el audio y el JSON a partir de los mismos eventos, así que la sincronía viene dada por la construcción.
- **El carril sale del grado de la escala:** `carril = grado % 5`. Una frase que sube recorre los carriles de izquierda a derecha, y repetir un motivo repite su patrón de teclas. Nada es aleatorio.
- **Las notas simultáneas son dos voces del arreglo**, como los golpes del clímax o el acorde final. Nunca hay más de dos a la vez.
- **Las respuestas de NOVA en la sección de llamada** suenan, pero no se juegan. Dan aire entre ráfagas.
- **Restricciones de jugabilidad** (comprobadas por test):
  - rejilla de semicorcheas;
  - nunca dos notas en el mismo carril a menos de 200 ms;
  - como máximo 2 simultáneas;
  - más del 80 % de cambios de carril;
  - ráfagas de 5 o más notas;
  - al menos 20 dobles.

## Controles

| Carril | Teclado | Mando |
|---|---|---|
| 1 | D | Cruceta izquierda / X |
| 2 | F | Cruceta abajo |
| 3 | Espacio | A |
| 4 | J | Cruceta arriba / Y |
| 5 | K | Cruceta derecha / RB |

**El quinto carril** es el central, en ámbar con forma de hexágono. Su arte está en `tools/arte/ritmo_quinto_carril.py`.

**Fácil y Normal** no cambian: siguen con 4 carriles, sus mismos charts y las mismas teclas.

## Integración

- **Menú:** el tutorial del duelo ofrece el botón «Difícil» junto a Fácil y Normal.
- **Puntuación y juicio:** usa el mismo juez, combo, rango S-D y umbral de éxito. Difícil muestra los nombres de juicio de juego de ritmo (PERFECT/GREAT/GOOD/MISS), como la Arena; al salir se restaura el modo anterior.
- **Hitos de combo:** «COMBO x25», «x50», «x75»… laten en el centro cada 25 aciertos seguidos.
- **Narrativa y Arena:**
  - El resultado alimenta la historia por la misma vía que las otras dificultades.
  - `Ritmo.validar_chart` acepta `lanes` de 4 o 5 y conserva 4 por defecto, así que los charts y las partidas de la Arena no cambian.

## Pruebas

| Prueba | Resultado |
|---|---|
| `tests/test_ritmo_dificil.py` | Valida el chart: 5 carriles y más de 2,5 veces la densidad de Normal. Comprueba las restricciones de arriba. **Al menos el 95 % de las notas coincide con un ataque del audio a ±20 ms** (detección por flujo espectral sobre el `.ogg`). El juez de 5 carriles llega a S perfecto. Fácil y Normal siguen con 4 carriles |
| `tests/test_ritmo.py` | Los charts existentes no cambian |
| Juego real, teclado (`tests/qa_ritmo_dificil.py`) | Pulsaciones reales de D/F/Espacio/J/K inyectadas en Ren'Py: **198/199 PERFECT, rango S, deriva máxima audio-chart de 17 ms**. Con capturas activas: 196/199 y 31,8 ms (las capturas cuestan fotogramas) |
| Mando | El mapeo y el runner (`qa_ritmo.rpy` con botones de mando) admiten 5 carriles; la evidencia de esta ronda es con teclado |

Las capturas están en `docs/remaster/duelo_dificil/`.

**Límite:** las partidas son automatizadas con pulsaciones reales sobre el juego en marcha, pero no hay sesiones de jugadores humanos.
