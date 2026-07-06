"""
models/transaction.py
---------------------
Define el modelo de datos normalizado para una transacción financiera.

Decisión de diseño:
- Se usa dataclass para inmutabilidad semántica y serialización sencilla.
- El Enum `TransactionStatus` evita strings mágicos en todo el proyecto.
- `is_valid` y `validation_errors` permiten transportar el resultado
  de validación junto con el objeto, sin acoplarlo al servicio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TransactionStatus(str, Enum):
    """Estados válidos para una transacción normalizada."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"  # temporal hasta validación

    @classmethod
    def from_raw(cls, raw: str) -> "TransactionStatus":
        """
        Mapea un estado crudo al enum correspondiente.

        Args:
            raw: Cadena de texto con el estado original.

        Returns:
            TransactionStatus normalizado.
        """
        mapping: dict[str, "TransactionStatus"] = {
            "completed": cls.SUCCESS,
            "ok": cls.SUCCESS,
            "success": cls.SUCCESS,
            "failed": cls.FAILED,
            "error": cls.FAILED,
            "pending": cls.PENDING,
        }
        return mapping.get(raw.lower().strip(), cls.UNKNOWN)


@dataclass
class Transaction:
    """
    Modelo normalizado de una transacción financiera.

    Attributes:
        id:               Identificador único de la transacción.
        amount:           Monto en punto flotante positivo.
        currency:         Código ISO de moneda en mayúsculas (ej. "USD").
        timestamp:        Fecha/hora en formato ISO-8601.
        status:           Estado de la transacción (TransactionStatus).
        source:           Identificador del sistema de origen.
        is_valid:         Indica si el registro pasó validación.
        validation_errors: Lista de errores encontrados durante validación.
        raw:              Registro original sin normalizar (para trazabilidad).
    """

    id: str
    amount: float
    currency: str
    timestamp: str
    status: TransactionStatus
    source: str
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    raw: Optional[dict] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        """
        Serializa la transacción al modelo normalizado estándar.

        Returns:
            Diccionario con los campos del modelo normalizado.
        """
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "source": self.source,
        }

    def to_dict_full(self) -> dict:
        """
        Serializa incluyendo campos de validación (para invalid.json).

        Returns:
            Diccionario completo con errores de validación.
        """
        base = self.to_dict()
        base["is_valid"] = self.is_valid
        base["validation_errors"] = self.validation_errors
        return base
