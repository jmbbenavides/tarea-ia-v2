"""
services/normalizer.py
----------------------
Convierte campos crudos extraídos por el parser al modelo normalizado
`Transaction`.

Reglas de normalización implementadas:

Montos:
  - Texto con símbolo ("$1,234.56")  → float
  - Formato europeo ("1.234,56")     → float
  - Entero en centavos (> threshold) → divide / 100
  - Entero/float directo             → float

Moneda:
  - Siempre en mayúsculas y sin espacios.

Estados:
  - completed, ok, success → SUCCESS
  - failed, error          → FAILED
  - pending                → PENDING
  - cualquier otro         → UNKNOWN

Fechas:
  - Intenta múltiples formatos del rules.json.
  - Si ninguno aplica, devuelve la cadena original para que el
    validador la marque como inválida.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.transaction import Transaction, TransactionStatus

# ---------------------------------------------------------------------------
# Carga de configuración
# ---------------------------------------------------------------------------

_RULES_PATH = Path(__file__).parent.parent / "config" / "rules.json"


def _load_rules() -> dict:
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


_RULES: dict = _load_rules()
_DATE_FORMATS: List[str] = _RULES["date_formats"]
_CENTS_THRESHOLD: int = _RULES["amount_rules"]["cents_threshold"]


# ---------------------------------------------------------------------------
# Conversión de montos
# ---------------------------------------------------------------------------

def _parse_amount(raw: Any) -> Optional[float]:
    """
    Convierte un valor crudo de monto a float.

    Soporta:
      - Entero/float directo.
      - Entero en centavos (si supera _CENTS_THRESHOLD, divide entre 100).
      - Texto con símbolo de moneda y separadores.
      - Formato europeo (punto como miles, coma como decimal).

    Args:
        raw: Valor crudo del monto.

    Returns:
        Monto como float, o None si no se pudo convertir.
    """
    if raw is None:
        return None

    # Caso numérico directo
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        amount = float(raw)
        # Heurística: entero muy grande → probablemente está en centavos
        if isinstance(raw, int) and raw > _CENTS_THRESHOLD:
            amount = raw / 100.0
        return round(amount, 2)

    # Caso texto
    if isinstance(raw, str):
        cleaned = raw.strip()

        # Detectar formato europeo: "1.234,56"
        if re.match(r"^-?[\d.]+,\d{2}$", cleaned.replace(" ", "")):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # Eliminar símbolos de moneda y espacios
            cleaned = re.sub(r"[^\d.,\-]", "", cleaned)
            # Eliminar comas como separadores de miles: "1,234.56" → "1234.56"
            if cleaned.count(",") == 1 and cleaned.count(".") == 1:
                # Ambos presentes: coma es miles, punto es decimal
                cleaned = cleaned.replace(",", "")
            elif cleaned.count(",") >= 1 and "." not in cleaned:
                # Solo comas → última coma es decimal
                parts = cleaned.rsplit(",", 1)
                cleaned = parts[0].replace(",", "") + "." + parts[1]

        try:
            amount = float(cleaned)
            return round(amount, 2)
        except ValueError:
            return None

    return None


# ---------------------------------------------------------------------------
# Normalización de moneda
# ---------------------------------------------------------------------------

def _normalize_currency(raw: Any) -> str:
    """
    Normaliza el código de moneda a mayúsculas sin espacios.

    Args:
        raw: Valor crudo del campo moneda.

    Returns:
        Cadena normalizada en mayúsculas.
    """
    if not raw:
        return ""
    return str(raw).strip().upper()


# ---------------------------------------------------------------------------
# Normalización de estado
# ---------------------------------------------------------------------------

def _normalize_status(raw: Any) -> TransactionStatus:
    """
    Convierte un estado crudo al enum TransactionStatus.

    Args:
        raw: Valor crudo del campo estado.

    Returns:
        TransactionStatus correspondiente.
    """
    if not raw:
        return TransactionStatus.UNKNOWN
    return TransactionStatus.from_raw(str(raw))


# ---------------------------------------------------------------------------
# Normalización de fecha
# ---------------------------------------------------------------------------

def _normalize_timestamp(raw: Any) -> str:
    """
    Intenta parsear la fecha usando los formatos del rules.json.
    Devuelve la cadena en ISO-8601 si tiene éxito, o el valor original
    si ningún formato aplica (para que el validador lo detecte).

    Args:
        raw: Valor crudo del campo fecha.

    Returns:
        Cadena ISO-8601 o el valor original.
    """
    if not raw:
        return ""
    raw_str = str(raw).strip()

    # Ya es ISO-8601 con zona horaria explícita
    if "T" in raw_str and (raw_str.endswith("Z") or "+" in raw_str[10:]):
        try:
            # Normalizar Z → +00:00
            normalized = raw_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass

    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    # No se pudo parsear → devolver original para que el validador actúe
    return raw_str


# ---------------------------------------------------------------------------
# Normalizador principal
# ---------------------------------------------------------------------------

def normalize(raw_fields: Dict[str, Any], original_record: Dict[str, Any]) -> Transaction:
    """
    Convierte los campos crudos estandarizados en un objeto Transaction.

    Args:
        raw_fields:      Diccionario con campos pre-extraídos por el parser.
        original_record: Registro JSON original (para trazabilidad en `raw`).

    Returns:
        Objeto Transaction con valores normalizados.
    """
    amount = _parse_amount(raw_fields.get("raw_amount"))
    currency = _normalize_currency(raw_fields.get("raw_currency"))
    status = _normalize_status(raw_fields.get("raw_status"))
    timestamp = _normalize_timestamp(raw_fields.get("raw_timestamp"))

    return Transaction(
        id=str(raw_fields.get("raw_id", "")).strip(),
        amount=amount if amount is not None else 0.0,
        currency=currency,
        timestamp=timestamp,
        status=status,
        source=str(raw_fields.get("source", "Unknown")),
        raw=original_record,
    )
