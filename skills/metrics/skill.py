"""
skills/metrics/skill.py
-----------------------
MetricsSkill: calcula y formatea estadísticas agregadas sobre
el conjunto de transacciones del contexto.

Responsabilidades:
  - Calcular métricas usando services/metrics.
  - Almacenar el resultado en el contexto.
  - Devolver el resumen formateado listo para mostrar en CLI.

Dependencias internas:
  - services.metrics → compute_metrics, format_metrics
"""

from __future__ import annotations

import logging
from typing import Any

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_no_data
from skills.base import BaseSkill
from services.metrics import compute_metrics, format_metrics

logger = logging.getLogger("TransactionAgent.MetricsSkill")


class MetricsSkill(BaseSkill):
    """
    Skill de cálculo de métricas del procesamiento.

    Calcula estadísticas sobre las transacciones en el contexto
    y actualiza self.context.metrics con los resultados.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(self, request: str, **kwargs: Any) -> str:
        """
        Calcula y devuelve las métricas del conjunto actual.

        Args:
            request:  Texto de la solicitud (no usado activamente).
            **kwargs: Ignorados.

        Returns:
            Métricas formateadas como cadena de texto.
        """
        if not self.context.is_loaded():
            return prompt_no_data()

        metrics = compute_metrics(self.context.transactions)
        self.context.metrics = metrics

        formatted = format_metrics(metrics)
        logger.info(
            "Métricas calculadas: %d procesadas, %d válidas, %d inválidas.",
            metrics["total_processed"],
            metrics["total_valid"],
            metrics["total_invalid"],
        )
        # Devolver el bloque de métricas formateado directamente
        return formatted
