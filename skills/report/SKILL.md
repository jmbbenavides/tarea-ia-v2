# ReportSkill

## Objetivo

Generar un reporte ejecutivo en formato Markdown con el resumen completo
del procesamiento de transacciones, incluyendo métricas, distribución por
estado, totales por moneda y listado de transacciones inválidas.

## Capacidades

- Resumen general (procesadas, válidas, inválidas, tasa de éxito).
- Tabla de distribución por estado.
- Tabla de totales por moneda (solo válidas).
- Tabla de transacciones inválidas con sus errores.
- Guardar reporte en `data/report.md`.
- Calcular métricas automáticamente si no están en el contexto.

## Entradas

| Parámetro     | Tipo   | Descripción                                       |
|---------------|--------|---------------------------------------------------|
| `request`     | `str`  | Texto de la solicitud                             |
| `output_path` | `Path` | Ruta del archivo de salida (default: `data/report.md`) |

Ejemplo de solicitud: `"genera un reporte"` / `"informe markdown"`

## Salidas

Archivo `data/report.md` con la siguiente estructura:

```markdown
# Reporte de Normalización de Transacciones

**Generado:** 2024-01-15 10:30:00 UTC
**Archivo fuente:** sample_transactions.json

---

## Resumen ejecutivo
| Indicador | Valor |
|-----------|-------|
| Total procesadas | 20 |
| Válidas | 16 |
| Inválidas | 4 |
| Tasa de éxito | 80.0% |

## Métricas por estado
...

## Totales por moneda (transacciones válidas)
...

## Transacciones inválidas
...
```

## Restricciones

- Requiere transacciones en el contexto.
- Si no hay métricas calculadas, las calcula internamente.
- El archivo se sobreescribe si ya existe.

## Dependencias

| Módulo                    | Uso                                          |
|---------------------------|----------------------------------------------|
| `services.metrics`        | `compute_metrics` (si no hay métricas)       |
| `config.config.DATA_DIR`  | Ruta al directorio de salida                 |
| `agent.context.AgentContext` | Lee el estado completo de la sesión      |

## Ejemplos

```python
skill = ReportSkill(context=ctx)
result = skill.execute("genera reporte")
print(result)
# → [ReportSkill] ✔ Reporte guardado en data/report.md
```
