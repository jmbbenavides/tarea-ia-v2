# MetricsSkill

## Objetivo

Calcular estadísticas agregadas sobre el conjunto de transacciones del contexto
y presentarlas en un formato legible para la consola.

## Capacidades

- Total de transacciones procesadas.
- Conteo de válidas e inválidas.
- Distribución por estado (SUCCESS, FAILED, PENDING).
- Monto total acumulado por moneda (solo transacciones válidas).
- Almacenar métricas en `AgentContext.metrics`.

## Entradas

| Parámetro | Tipo  | Descripción                                  |
|-----------|-------|----------------------------------------------|
| `request` | `str` | Texto de la solicitud (usado para el log)    |

La skill opera sobre `AgentContext.transactions`.

Ejemplo de solicitud: `"métricas del procesamiento"` / `"estadísticas"`

## Salidas

- Bloque de texto formateado con todas las métricas.
- `AgentContext.metrics` actualizado.

Ejemplo de salida:
```
==================================================
           MÉTRICAS DEL PROCESAMIENTO
==================================================
  Total procesadas :     20
  Total válidas    :     16
  Total inválidas  :      4

  Por estado:
    SUCCESS   : 10
    FAILED    :  4
    PENDING   :  2

  Totales por moneda (solo válidas):
    EUR   :     8,750.00
    USD   :    15,200.00
==================================================
```

## Restricciones

- Requiere transacciones en el contexto.
- Si `ValidateSkill` no fue ejecutada, calcula sobre todo el conjunto.

## Dependencias

| Módulo                    | Uso                                          |
|---------------------------|----------------------------------------------|
| `services.metrics`        | `compute_metrics`, `format_metrics`          |
| `agent.context.AgentContext` | Lee transacciones, actualiza metrics     |

## Ejemplos

```python
skill = MetricsSkill(context=ctx)
output = skill.execute("métricas")
print(output)
```
