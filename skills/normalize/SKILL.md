# NormalizeSkill

## Objetivo

Detectar el formato de origen de registros JSON de transacciones financieras
y convertirlos al modelo normalizado `Transaction`, listo para validación.

## Capacidades

- Detectar automáticamente 5 formatos de entrada (FormatA–E) más un modo genérico.
- Extraer campos estandarizados (`raw_id`, `raw_amount`, `raw_currency`, `raw_timestamp`, `raw_status`).
- Normalizar montos (texto con símbolos, formato europeo, centavos).
- Normalizar estados al enum `TransactionStatus`.
- Normalizar fechas a ISO-8601.
- Almacenar resultados en el `AgentContext`.

## Entradas

| Parámetro | Tipo   | Descripción                                      |
|-----------|--------|--------------------------------------------------|
| `request` | `str`  | Texto con la solicitud, puede incluir la ruta    |
| `filepath`| `Path` | Ruta explícita al archivo JSON (opcional)        |

Ejemplo de solicitud: `"normaliza data/sample_transactions.json"`

## Salidas

- Lista de objetos `Transaction` almacenada en `AgentContext.transactions`.
- Mensaje de texto con resumen: archivo, procesadas, omitidas.

## Restricciones

- El archivo de entrada debe ser un array JSON en el nivel raíz.
- Cada elemento del array debe ser un objeto (`dict`).
- Si no se especifica archivo, usa `data/sample_transactions.json` por defecto.

## Dependencias

| Módulo                    | Uso                                  |
|---------------------------|--------------------------------------|
| `services.parser`         | `parse_record` → detecta y extrae    |
| `services.normalizer`     | `normalize` → convierte a Transaction|
| `agent.context.AgentContext` | Almacena resultados de sesión    |
| `config.config.DATA_DIR`  | Ruta al directorio de datos          |

## Ejemplos

```python
from agent.context import AgentContext
from skills.normalize.skill import NormalizeSkill

ctx = AgentContext()
skill = NormalizeSkill(context=ctx)

# Con archivo explícito
result = skill.execute("normaliza", filepath=Path("data/sample_transactions.json"))
print(result)
# → [NormalizeSkill] ✔ Archivo: sample_transactions.json | Procesadas: 20 | Omitidas: 0

# Con ruta en el texto
result = skill.execute("normaliza data/sample_transactions.json")
print(len(ctx.transactions))  # → 20
```
