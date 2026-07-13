"""
skills/validate/skill.py
------------------------
ValidateSkill: valida las transacciones normalizadas almacenadas
en el contexto y las separa en válidas e inválidas.

Responsabilidades:
  - Aplicar todas las reglas de validación a cada Transaction.
  - Separar el conjunto en válidas e inválidas.
  - Actualizar el contexto con los resultados.

Dependencias internas:
  - services.validator → validate, split_transactions
"""

from __future__ import annotations

import logging
from typing import Any

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_error, prompt_no_data
from skills.base import BaseSkill
from services.validator import validate, split_transactions

logger = logging.getLogger("TransactionAgent.ValidateSkill")


class ValidateSkill(BaseSkill):
    """
    Skill de validación de transacciones.

    Opera sobre las transacciones almacenadas en el AgentContext
    (previamente normalizadas por NormalizeSkill). Aplica todas
    las reglas de validación y actualiza los subconjuntos
    valid/invalid del contexto.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(self, request: str, **kwargs: Any) -> str:
        """
        Valida todas las transacciones del contexto.

        Args:
            request:  Texto de la solicitud (no usado activamente).
            **kwargs: Ignorados.

        Returns:
            Resumen de validación con conteos.
        """
        if not self.context.is_loaded():
            return prompt_no_data()

        # Validar cada transacción (actualiza is_valid y validation_errors)
        validated = [validate(tx) for tx in self.context.transactions]
        self.context.transactions = validated

        # Separar en válidas e inválidas
        valid, invalid = split_transactions(validated)
        self.context.valid = valid
        self.context.invalid = invalid

        # Detalles de errores para el log
        if invalid:
            for tx in invalid:
                logger.debug(
                    "Inválida [%s]: %s", tx.id, "; ".join(tx.validation_errors)
                )

        summary = (
            f"Total: {len(validated)} | "
            f"Válidas: {len(valid)} | "
            f"Inválidas: {len(invalid)}"
        )
        logger.info("Validación completada. %s", summary)
        return prompt_success(self.name, summary)
