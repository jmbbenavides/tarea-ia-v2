# SearchSkill

## Objetivo

Buscar transacciones específicas dentro del conjunto cargado en el contexto,
filtrando por ID, código de moneda o estado.

## Capacidades

- **Búsqueda por estado**: SUCCESS, FAILED, PENDING (y sinónimos en español).
- **Búsqueda por moneda**: código ISO de 3 letras (USD, EUR, MXN…).
- **Búsqueda por ID**: búsqueda parcial insensible a mayúsculas.
- **Búsqueda por fuente**: coincidencia parcial en el campo `source`.
- Extracción automática del término desde el texto de la solicitud.

## Entradas

| Parámetro | Tipo  | Descripción                                          |
|-----------|-------|------------------------------------------------------|
| `request` | `str` | Texto con el término de búsqueda integrado            |

Ejemplos de solicitud:
- `"busca TXN-001"`
- `"filtrar por moneda USD"`
- `"buscar estado pendientes"`
- `"busco exitosas"`

## Salidas

Lista de transacciones que coinciden, formateada en texto:
```
Resultados para «USD» (5 encontradas):
  ✔ [TXN-001] 1,500.00 USD | SUCCESS | FormatA
  ✔ [TXN-003] 800.00 USD | PENDING | FormatB
  ...
```

## Restricciones

- Requiere transacciones en el contexto.
- Si no se puede extraer un término de búsqueda, devuelve error.
- La búsqueda por moneda requiere exactamente 3 letras.

## Dependencias

| Módulo                    | Uso                                          |
|---------------------------|----------------------------------------------|
| `models.transaction`      | `Transaction`, `TransactionStatus`           |
| `agent.context.AgentContext` | Lee transacciones del contexto           |

## Ejemplos

```python
skill = SearchSkill(context=ctx)

# Por ID
result = skill.execute("busca TXN-001")

# Por moneda
result = skill.execute("filtrar USD")

# Por estado
result = skill.execute("buscar pendientes")

print(result)
```
