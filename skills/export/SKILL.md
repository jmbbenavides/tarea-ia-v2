# ExportSkill

## Objetivo

Exportar las transacciones validadas del contexto a archivos JSON
separados: uno para las válidas y otro para las inválidas.

## Capacidades

- Generar `data/valid.json` con transacciones que pasaron validación.
- Generar `data/invalid.json` con transacciones rechazadas (incluye errores).
- Serializar usando el modelo `Transaction.to_dict()` / `to_dict_full()`.
- Aceptar directorio de salida personalizado.

## Entradas

| Parámetro    | Tipo   | Descripción                                      |
|--------------|--------|--------------------------------------------------|
| `request`    | `str`  | Texto de la solicitud                            |
| `output_dir` | `Path` | Directorio de salida (default: `data/`)          |

Ejemplo de solicitud: `"exporta los resultados"` / `"guarda los archivos"`

## Salidas

- `data/valid.json`   → array JSON de transacciones válidas.
- `data/invalid.json` → array JSON con errores de validación incluidos.
- Mensaje de texto con rutas y conteos.

### Estructura de valid.json
```json
[
  {
    "id": "TXN-001",
    "amount": 1500.00,
    "currency": "USD",
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "SUCCESS",
    "source": "FormatA"
  }
]
```

### Estructura de invalid.json
```json
[
  {
    "id": "",
    "amount": -50.0,
    "currency": "XYZ",
    "timestamp": "...",
    "status": "UNKNOWN",
    "source": "Generic",
    "is_valid": false,
    "validation_errors": ["ID vacío o ausente", "Monto inválido: -50.0"]
  }
]
```

## Restricciones

- Requiere transacciones en el contexto.
- Si `ValidateSkill` no fue ejecutada, usa `is_valid` de cada Transaction.
- Los archivos se sobreescriben si ya existen.

## Dependencias

| Módulo                    | Uso                                          |
|---------------------------|----------------------------------------------|
| `models.transaction`      | `to_dict`, `to_dict_full`                    |
| `config.config.DATA_DIR`  | Ruta al directorio de datos                  |
| `agent.context.AgentContext` | Lee valid/invalid del contexto           |

## Ejemplos

```python
skill = ExportSkill(context=ctx)
result = skill.execute("exporta los resultados")
print(result)
# → [ExportSkill] ✔ valid.json (16 registros) → ... | invalid.json (4 registros) → ...
```
