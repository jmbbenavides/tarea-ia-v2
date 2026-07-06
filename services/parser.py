"""
services/parser.py
------------------
Detecta el formato de origen de cada registro crudo y lo pre-procesa
antes de que el normalizador lo convierta al modelo estándar.

Formatos soportados:
  - FormatA: claves estándar (transaction_id, amount, currency, date, status)
  - FormatB: claves con prefijo "tx_" (tx_id, tx_amount, tx_currency, tx_date, tx_status)
  - FormatC: claves snake_case alternativas (ref, value, cur, created_at, state)
  - FormatD: payload plano con "id" y campos numéricos/de texto variados
  - FormatE: campos genéricos (uid, total, money_type, datetime, transaction_status)

Decisión de diseño:
  Se prefiere detección por presencia de claves en lugar de versión
  explícita en el payload, para soportar fuentes que no indican versión.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


# ---------------------------------------------------------------------------
# Detectores de formato
# ---------------------------------------------------------------------------

_FORMAT_SIGNATURES: list[Tuple[str, set[str]]] = [
    ("FormatA", {"transaction_id", "amount", "currency", "date", "status"}),
    ("FormatB", {"tx_id", "tx_amount", "tx_currency", "tx_date", "tx_status"}),
    ("FormatC", {"ref", "value", "cur", "created_at", "state"}),
    ("FormatD", {"id", "amount_cents", "currency_code", "created_at", "status"}),
    ("FormatE", {"uid", "total", "money_type", "datetime", "transaction_status"}),
]


def detect_format(record: Dict[str, Any]) -> str:
    """
    Detecta el formato de un registro crudo comparando sus claves.

    Args:
        record: Diccionario con los datos crudos del registro.

    Returns:
        Nombre del formato detectado (ej. "FormatA") o "Unknown".
    """
    record_keys = set(record.keys())
    for format_name, signature in _FORMAT_SIGNATURES:
        if signature.issubset(record_keys):
            return format_name
    # Intento genérico: si tiene "id" y algo parecido a monto
    if "id" in record_keys:
        return "Generic"
    return "Unknown"


# ---------------------------------------------------------------------------
# Extractor de campos crudos según formato
# ---------------------------------------------------------------------------

def extract_raw_fields(record: Dict[str, Any], fmt: str) -> Dict[str, Any]:
    """
    Extrae y estandariza los campos crudos de un registro al conjunto:
    {raw_id, raw_amount, raw_currency, raw_timestamp, raw_status, source}.

    Args:
        record: Registro de datos sin normalizar.
        fmt:    Nombre del formato detectado.

    Returns:
        Diccionario con claves estandarizadas para el normalizador.

    Raises:
        KeyError: Si el formato conocido no tiene las claves esperadas.
    """
    extractors = {
        "FormatA": _extract_format_a,
        "FormatB": _extract_format_b,
        "FormatC": _extract_format_c,
        "FormatD": _extract_format_d,
        "FormatE": _extract_format_e,
    }
    extractor = extractors.get(fmt, _extract_generic)
    return extractor(record)


def _extract_format_a(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_id":        r.get("transaction_id", ""),
        "raw_amount":    r.get("amount", 0),
        "raw_currency":  r.get("currency", ""),
        "raw_timestamp": r.get("date", ""),
        "raw_status":    r.get("status", ""),
        "source":        "FormatA",
    }


def _extract_format_b(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_id":        r.get("tx_id", ""),
        "raw_amount":    r.get("tx_amount", 0),
        "raw_currency":  r.get("tx_currency", ""),
        "raw_timestamp": r.get("tx_date", ""),
        "raw_status":    r.get("tx_status", ""),
        "source":        "FormatB",
    }


def _extract_format_c(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_id":        r.get("ref", ""),
        "raw_amount":    r.get("value", 0),
        "raw_currency":  r.get("cur", ""),
        "raw_timestamp": r.get("created_at", ""),
        "raw_status":    r.get("state", ""),
        "source":        "FormatC",
    }


def _extract_format_d(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_id":        r.get("id", ""),
        "raw_amount":    r.get("amount_cents", 0),
        "raw_currency":  r.get("currency_code", ""),
        "raw_timestamp": r.get("created_at", ""),
        "raw_status":    r.get("status", ""),
        "source":        "FormatD",
    }


def _extract_format_e(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "raw_id":        r.get("uid", ""),
        "raw_amount":    r.get("total", 0),
        "raw_currency":  r.get("money_type", ""),
        "raw_timestamp": r.get("datetime", ""),
        "raw_status":    r.get("transaction_status", ""),
        "source":        "FormatE",
    }


def _extract_generic(r: Dict[str, Any]) -> Dict[str, Any]:
    """Extractor de último recurso para formatos no reconocidos."""
    amount_keys = ("amount", "total", "value", "amount_cents", "tx_amount")
    currency_keys = ("currency", "cur", "currency_code", "money_type", "tx_currency")
    timestamp_keys = ("date", "created_at", "datetime", "tx_date", "timestamp")
    status_keys = ("status", "state", "tx_status", "transaction_status")

    return {
        "raw_id":        r.get("id", r.get("uid", r.get("ref", r.get("transaction_id", "")))),
        "raw_amount":    next((r[k] for k in amount_keys if k in r), 0),
        "raw_currency":  next((r[k] for k in currency_keys if k in r), ""),
        "raw_timestamp": next((r[k] for k in timestamp_keys if k in r), ""),
        "raw_status":    next((r[k] for k in status_keys if k in r), ""),
        "source":        "Generic",
    }


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------

def parse_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Punto de entrada del parser: detecta el formato y extrae los campos.

    Args:
        record: Registro JSON crudo.

    Returns:
        Diccionario con campos estandarizados para el normalizador.
    """
    fmt = detect_format(record)
    fields = extract_raw_fields(record, fmt)
    return fields
