# 💳 Normalizador de Transacciones Multifuente

Aplicación Python con CLI interactiva que lee transacciones desde JSON, detecta el formato de origen, normaliza al modelo estándar, valida los registros, calcula métricas y permite explorar la información.

---

## Estructura del proyecto

```
tarea-ia-v2/
├── main.py                        # Punto de entrada
├── requirements.txt               # Dependencias
├── README.md                      # Este archivo
├── NOTA_TECNICA.md                # Nota técnica de una página
├── config/
│   └── rules.json                 # Estados, monedas, formatos de fecha
├── data/
│   ├── sample_transactions.json   # Datos de prueba (22 registros)
│   ├── valid.json                 # Generado al exportar
│   └── invalid.json               # Generado al exportar
├── models/
│   └── transaction.py             # Dataclass Transaction + Enum TransactionStatus
├── services/
│   ├── parser.py                  # Detección de formato y extracción de campos
│   ├── normalizer.py              # Conversión al modelo normalizado
│   ├── validator.py               # Validación y separación
│   └── metrics.py                 # Cálculo y presentación de métricas
├── ui/
│   └── cli.py                     # CLI interactiva con menú de 8 opciones
└── tests/
    ├── test_normalizer.py
    ├── test_validator.py
    └── test_metrics.py
```

---

## Requisitos

- Python 3.9 o superior
- Dependencias:

```bash
pip install -r requirements.txt
```

---

## Cómo ejecutar

### CLI interactiva

```bash
python main.py
```

Abre el menú interactivo con 8 opciones.

### Modo batch (sin CLI)

```bash
python main.py --proceso
```

Procesa `data/sample_transactions.json`, genera `valid.json` e `invalid.json` e imprime las métricas.

---

## Menú de la CLI

| Opción | Descripción |
|--------|-------------|
| 1 | Cargar archivo JSON de transacciones |
| 2 | Ver todas las transacciones normalizadas |
| 3 | Filtrar por estado (SUCCESS / FAILED / PENDING) |
| 4 | Filtrar por moneda (USD, EUR, …) |
| 5 | Ver métricas del procesamiento |
| 6 | Ver transacciones inválidas con sus errores |
| 7 | Exportar normalizadas (valid.json / invalid.json) |
| 8 | Salir |

---

## Modelo normalizado

```json
{
  "id": "TXN-001",
  "amount": 1500.00,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00Z",
  "status": "SUCCESS",
  "source": "FormatA"
}
```

---

## Reglas de normalización

### Montos
| Entrada | Resultado |
|---------|-----------|
| `350000` (int > 10 000) | `3500.00` (÷100, asume centavos) |
| `"$1,234.56"` | `1234.56` |
| `"2.500,75"` (europeo) | `2500.75` |
| `99.99` | `99.99` |

### Moneda
- Siempre en MAYÚSCULAS: `eur` → `EUR`

### Estados
| Entrada | Normalizado |
|---------|-------------|
| completed, OK, success | SUCCESS |
| failed, error | FAILED |
| pending | PENDING |
| cualquier otro | UNKNOWN → inválido |

### Fechas soportadas
- `%Y-%m-%dT%H:%M:%SZ` (ISO-8601)
- `%Y-%m-%d %H:%M:%S`
- `%d/%m/%Y %H:%M`
- Y más formatos en `config/rules.json`

---

## Formatos de entrada detectados

| Formato | Claves características |
|---------|----------------------|
| FormatA | `transaction_id`, `amount`, `currency`, `date`, `status` |
| FormatB | `tx_id`, `tx_amount`, `tx_currency`, `tx_date`, `tx_status` |
| FormatC | `ref`, `value`, `cur`, `created_at`, `state` |
| FormatD | `id`, `amount_cents`, `currency_code`, `created_at`, `status` |
| FormatE | `uid`, `total`, `money_type`, `datetime`, `transaction_status` |

---

## Ejecutar pruebas

```bash
pytest tests/ -v
```

---

## Criterios de invalidación

Una transacción se marca inválida si:
- El ID está vacío o ausente.
- El monto es ≤ 0 o no se pudo convertir.
- La moneda está vacía o no está en la lista de soportadas.
- La fecha no puede interpretarse como ISO-8601.
- El estado no se pudo mapear (queda como UNKNOWN).
