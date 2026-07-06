"""
services/validator.py
---------------------
Valida los objetos Transaction normalizados y los separa en válidos e
inválidos según los criterios del proyecto.

Criterios de invalidación:
  - ID vacío o ausente.
  - Monto <= 0 o None.
  - Moneda vacía o no soportada.
  - Fecha inválida (no está en formato ISO-8601 reconocible).
  - Estado UNKNOWN (no se pudo mapear a SUCCESS/FAILED/PENDING).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

from models.transaction import Transaction, TransactionStatus

# ---------------------------------------------------------------------------
# Carga de configuración
# ---------------------------------------------------------------------------

_RULES_PATH = Path(__file__).parent.parent / "config" / "rules.json"


def _load_rules() -> dict:
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


_RULES: dict = _load_rules()
_SUPPORTED_CURRENCIES: set[str] = set(_RULES["supported_currencies"])

# Patrón mínimo ISO-8601 que acepta el sistema tras la normalización
_ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2}|\.?\d*Z?)?$"
)


# ---------------------------------------------------------------------------
# Funciones de validación individuales
# ---------------------------------------------------------------------------

def _check_id(tx: Transaction) -> List[str]:
    """Valida que el ID no esté vacío."""
    if not tx.id or tx.id.strip() == "":
        return ["ID vacío o ausente"]
    return []


def _check_amount(tx: Transaction) -> List[str]:
    """Valida que el monto sea un número positivo."""
    errors: List[str] = []
    if tx.amount is None:
        errors.append("Monto inválido: valor nulo")
    elif tx.amount <= 0:
        errors.append(f"Monto inválido: {tx.amount} (debe ser > 0)")
    return errors


def _check_currency(tx: Transaction) -> List[str]:
    """Valida que la moneda no esté vacía y sea soportada."""
    errors: List[str] = []
    if not tx.currency:
        errors.append("Moneda vacía")
    elif tx.currency not in _SUPPORTED_CURRENCIES:
        errors.append(f"Moneda no soportada: '{tx.currency}'")
    return errors


def _check_timestamp(tx: Transaction) -> List[str]:
    """Valida que el timestamp sea un ISO-8601 reconocido."""
    if not tx.timestamp or not _ISO8601_PATTERN.match(tx.timestamp):
        return [f"Fecha inválida: '{tx.timestamp}'"]
    return []


def _check_status(tx: Transaction) -> List[str]:
    """Valida que el estado sea conocido (no UNKNOWN)."""
    if tx.status == TransactionStatus.UNKNOWN:
        raw_status = tx.raw.get("status", tx.raw.get("state", tx.raw.get("tx_status", ""))) if tx.raw else ""
        return [f"Estado desconocido: '{raw_status}'"]
    return []


# ---------------------------------------------------------------------------
# Validador principal
# ---------------------------------------------------------------------------

def validate(tx: Transaction) -> Transaction:
    """
    Ejecuta todas las validaciones sobre una Transaction y actualiza
    sus campos `is_valid` y `validation_errors` in-place.

    Args:
        tx: Objeto Transaction normalizado.

    Returns:
        El mismo objeto Transaction con campos de validación actualizados.
    """
    errors: List[str] = []
    errors.extend(_check_id(tx))
    errors.extend(_check_amount(tx))
    errors.extend(_check_currency(tx))
    errors.extend(_check_timestamp(tx))
    errors.extend(_check_status(tx))

    tx.validation_errors = errors
    tx.is_valid = len(errors) == 0
    return tx


def split_transactions(
    transactions: List[Transaction],
) -> Tuple[List[Transaction], List[Transaction]]:
    """
    Separa una lista de transacciones en válidas e inválidas.

    Args:
        transactions: Lista de objetos Transaction validados.

    Returns:
        Tupla (válidas, inválidas).
    """
    valid = [tx for tx in transactions if tx.is_valid]
    invalid = [tx for tx in transactions if not tx.is_valid]
    return valid, invalid
