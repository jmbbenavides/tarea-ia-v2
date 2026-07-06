# Nota Técnica — Normalizador de Transacciones Multifuente

**Autor:** Estudiante Kodigo  
**Fecha:** Julio 2026  
**Proyecto:** Tarea IA v2 — Normalización y Exploración de Transacciones

---

## 1. Decisiones del modelo

Se utilizó una **`dataclass`** de Python para representar la transacción normalizada (`Transaction`). Esta elección obedece a tres razones:

1. **Claridad**: los campos son inmediatamente visibles en la definición de la clase, sin getters ni setters.
2. **Serialización sencilla**: el método `to_dict()` convierte la instancia al modelo JSON en una sola llamada.
3. **Transporte de metadatos de validación**: al incluir `is_valid` y `validation_errors` en la misma dataclass, el objeto viaja "auto-anotado" por toda la cadena de procesamiento sin necesidad de estructuras paralelas.

El estado se modeló con un **`Enum` (`TransactionStatus`)** en lugar de strings, eliminando la posibilidad de comparaciones con strings mágicos y haciendo el código más seguro en tiempo de ejecución.

---

## 2. Reglas de normalización

### Montos
La mayor fuente de heterogeneidad entre sistemas financieros es el formato del monto. Se implementaron cuatro casos:

| Tipo | Ejemplo | Lógica |
|------|---------|--------|
| Float/int directo | `99.99` | Conversión directa |
| Entero en centavos | `350000` | Si el entero supera el umbral (10 000, configurable en `rules.json`), se divide entre 100 |
| Texto con símbolo | `"$1,234.56"` | Se eliminan caracteres no numéricos, luego se parsea |
| Formato europeo | `"2.500,75"` | El punto es separador de miles y la coma es decimal; se invierten para obtener el float |

### Moneda
Normalización trivial pero importante: `.strip().upper()`. Esto convierte `"eur "` → `"EUR"`.

### Estados
Se definió una tabla de mapeo explícita en `TransactionStatus.from_raw()`. El estado `UNKNOWN` actúa como centinela: cualquier estado que llegue y no esté en la tabla quedará marcado como `UNKNOWN` y el validador lo rechazará.

### Fechas
Se prueban secuencialmente todos los formatos listados en `config/rules.json`. Si ninguno funciona, el string original se devuelve sin modificar, para que el validador detecte la fecha inválida y anote el error específico. Esto evita lanzar excepciones silenciosas.

---

## 3. Criterios de validación

Se validaron cinco campos de forma independiente:

| Campo | Criterio de invalidación |
|-------|--------------------------|
| `id` | Vacío o string de solo espacios |
| `amount` | ≤ 0 o valor nulo |
| `currency` | Vacía o no presente en la lista de `rules.json` |
| `timestamp` | No coincide con el patrón ISO-8601 mínimo |
| `status` | Quedó como `UNKNOWN` tras el mapeo |

Cada validación agrega un mensaje descriptivo a `validation_errors`, permitiendo diagnosticar exactamente qué falló sin releer el registro original.

---

## 4. Cómo se utilizó la IA

La IA (Antigravity / Claude) fue utilizada para:

- **Generación del esqueleto inicial**: estructura de archivos, interfaces de funciones con type hints y docstrings.
- **Implementación de los extractores por formato** (`parser.py`): se generaron los cinco extractores y el genérico de fallback de forma automatizada.
- **Generación de los tests unitarios**: los tres archivos de tests (`test_normalizer.py`, `test_validator.py`, `test_metrics.py`) fueron generados por la IA con cobertura de casos límite.
- **Diseño de los datos de prueba**: los 22 registros en `sample_transactions.json` cubren todos los formatos y casos de invalidación requeridos.

---

## 5. Sugerencias modificadas manualmente

Las siguientes decisiones se tomaron de forma consciente sobre las sugerencias de la IA:

1. **Umbral de centavos configurable**: la IA propuso un valor hardcodeado de `10_000`. Se movió a `config/rules.json` (`"cents_threshold": 10000`) para facilitar ajustes sin tocar el código.

2. **`UNKNOWN` como estado intermedio**: la IA inicialmente proponía lanzar un `ValueError` si el estado no se reconocía. Se cambió a devolver `UNKNOWN` y dejar que el validador lo rechace con un mensaje descriptivo, lo que mejora la trazabilidad.

3. **Modo batch (`--proceso`)**: se añadió esta opción en `main.py` para poder procesar y exportar sin abrir la CLI, útil para pruebas automatizadas y pipelines CI.

4. **`colorama` como dependencia opcional**: se envolvió la importación en `try/except` para que la CLI funcione también en entornos donde `colorama` no esté instalado, sin fallar.

5. **Campo `raw` en `Transaction`**: la IA no lo incluyó inicialmente. Se añadió para mantener trazabilidad del registro original, especialmente útil para depurar los errores de validación.
