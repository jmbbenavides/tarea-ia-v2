# ValidateSkill

## Objetivo

Aplicar las reglas de validación de negocio sobre las transacciones normalizadas
del contexto y separarlas en dos grupos: válidas e inválidas.

## Capacidades

- Validar ID no vacío.
- Validar monto positivo (> 0).
- Validar moneda soportada (según `config/rules.json`).
- Validar timestamp en formato ISO-8601.
- Validar que el estado no sea `UNKNOWN`.
- Registrar todos los errores encontrados en cada transacción.
- Actualizar `AgentContext.valid` y `AgentContext.invalid`.

## Entradas

| Parámetro | Tipo  | Descripción                                  |
|-----------|-------|----------------------------------------------|
| `request` | `str` | Texto de la solicitud (usado para el log)    |

La skill opera sobre `AgentContext.transactions` (sin parámetros adicionales).

Ejemplo de solicitud: `"valida las transacciones"`

## Salidas

- `AgentContext.valid`   → lista de `Transaction` con `is_valid=True`.
- `AgentContext.invalid` → lista de `Transaction` con `is_valid=False`.
- Mensaje de texto con resumen: total, válidas, inválidas.

## Restricciones

- Requiere que `NormalizeSkill` haya sido ejecutada previamente.
- Si el contexto está vacío, devuelve mensaje de advertencia.
- Las reglas de validación provienen de `config/rules.json`.

## Dependencias

| Módulo                    | Uso                                      |
|---------------------------|------------------------------------------|
| `services.validator`      | `validate`, `split_transactions`         |
| `agent.context.AgentContext` | Lee y actualiza el estado de sesión  |

## Ejemplos

```python
from agent.context import AgentContext
from skills.validate.skill import ValidateSkill

# Asumiendo que ctx ya tiene transactions (tras NormalizeSkill)
skill = ValidateSkill(context=ctx)
result = skill.execute("valida las transacciones")
print(result)
# → [ValidateSkill] ✔ Total: 20 | Válidas: 16 | Inválidas: 4

print(len(ctx.valid))    # → 16
print(len(ctx.invalid))  # → 4
```
