"""
skills/search/skill.py
----------------------
SearchSkill: búsqueda de transacciones por ID, moneda o estado
sobre el conjunto cargado en el contexto.

Responsabilidades:
  - Parsear el término de búsqueda de la solicitud.
  - Buscar por ID exacto.
  - Buscar por código de moneda.
  - Buscar por estado (SUCCESS, FAILED, PENDING).
  - Devolver resultados formateados.

Decisión de diseño:
  La skill intenta determinar el tipo de búsqueda por el formato
  del término: IDs suelen contener guiones, monedas son 3 letras,
  estados son palabras clave específicas.
"""

from __future__ import annotations

import logging
import re
from typing import Any, List

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_error, prompt_no_data
from models.transaction import Transaction, TransactionStatus
from skills.base import BaseSkill

logger = logging.getLogger("TransactionAgent.SearchSkill")

# Mapeado de términos de búsqueda a estados
_STATUS_MAP: dict[str, TransactionStatus] = {
    "success":   TransactionStatus.SUCCESS,
    "exitosas":  TransactionStatus.SUCCESS,
    "completadas": TransactionStatus.SUCCESS,
    "failed":    TransactionStatus.FAILED,
    "fallidas":  TransactionStatus.FAILED,
    "errores":   TransactionStatus.FAILED,
    "pending":   TransactionStatus.PENDING,
    "pendientes": TransactionStatus.PENDING,
}


class SearchSkill(BaseSkill):
    """
    Skill de búsqueda de transacciones.

    Soporta búsqueda por:
      - ID: detectado si el término contiene guiones o prefijo TXN-
      - Moneda: detectado si es una cadena de 3 letras mayúsculas.
      - Estado: detectado por palabras clave de estado.
      - General: búsqueda por coincidencia parcial en ID o fuente.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(self, request: str, **kwargs: Any) -> str:
        """
        Ejecuta la búsqueda según el término extraído de la solicitud.

        Args:
            request:  Texto de la solicitud con el término de búsqueda.
            **kwargs: Ignorados.

        Returns:
            Resultados de la búsqueda formateados.
        """
        if not self.context.is_loaded():
            return prompt_no_data()

        term = self._extract_term(request)
        if not term:
            return prompt_error(self.name, "No se especificó un término de búsqueda.")

        # Determinar tipo de búsqueda
        results = self._search(term, self.context.transactions)

        if not results:
            return prompt_success(
                self.name, f"No se encontraron resultados para «{term}»."
            )

        lines = [f"Resultados para «{term}» ({len(results)} encontradas):"]
        for tx in results:
            valid_marker = "✔" if tx.is_valid else "✘"
            lines.append(
                f"  {valid_marker} [{tx.id}] "
                f"{tx.amount:,.2f} {tx.currency} | "
                f"{tx.status.value} | {tx.source}"
            )

        logger.info("Búsqueda «%s»: %d resultados.", term, len(results))
        return "\n".join(lines)

    def _extract_term(self, request: str) -> str:
        """
        Extrae el término de búsqueda del texto de la solicitud.

        Elimina las palabras clave del router y devuelve lo restante.

        Args:
            request: Texto de la solicitud.

        Returns:
            Término de búsqueda limpio.
        """
        remove_words = {
            "buscar", "busca", "busco", "encontrar", "encuentra",
            "filtrar", "filtra", "search", "por", "el", "la", "los",
            "las", "de", "con", "estado", "moneda", "id",
        }
        tokens = request.lower().split()
        filtered = [t for t in tokens if t not in remove_words]
        return " ".join(filtered).strip()

    def _search(
        self, term: str, transactions: List[Transaction]
    ) -> List[Transaction]:
        """
        Ejecuta la búsqueda sobre la lista de transacciones.

        Orden de prioridad:
          1. Búsqueda por estado.
          2. Búsqueda por moneda (3 letras exactas).
          3. Búsqueda por ID parcial o fuente.

        Args:
            term:         Término de búsqueda normalizado.
            transactions: Lista de transacciones del contexto.

        Returns:
            Lista de transacciones que coinciden.
        """
        term_upper = term.upper()

        # 1. Por estado
        status = _STATUS_MAP.get(term.lower())
        if status:
            return [tx for tx in transactions if tx.status == status]

        # 2. Por moneda (exactamente 3 letras)
        if re.fullmatch(r"[A-Z]{3}", term_upper):
            return [tx for tx in transactions if tx.currency == term_upper]

        # 3. Por ID o fuente (búsqueda parcial case-insensitive)
        return [
            tx for tx in transactions
            if term_upper in tx.id.upper() or term_upper in tx.source.upper()
        ]
