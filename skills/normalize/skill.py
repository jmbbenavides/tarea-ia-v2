"""
skills/normalize/skill.py
-------------------------
NormalizeSkill: detecta el formato del archivo de entrada,
parsea los registros y los normaliza al modelo Transaction.

Responsabilidades:
  - Leer el archivo JSON indicado en la solicitud.
  - Detectar el formato de cada registro (FormatA…E / Generic).
  - Normalizar cada registro mediante services/normalizer.
  - Almacenar los resultados en el contexto compartido.

Dependencias internas:
  - services.parser   → detect_format, parse_record
  - services.normalizer → normalize
  - models.transaction  → Transaction
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_error
from skills.base import BaseSkill
from services.parser import parse_record
from services.normalizer import normalize

logger = logging.getLogger("TransactionAgent.NormalizeSkill")


class NormalizeSkill(BaseSkill):
    """
    Skill de normalización de transacciones multifuente.

    Lee un archivo JSON con registros de múltiples orígenes,
    detecta su formato y los convierte al modelo Transaction.
    Los resultados se almacenan en el AgentContext.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(self, request: str, filepath: Path | None = None, **kwargs: Any) -> str:
        """
        Normaliza las transacciones del archivo indicado.

        Args:
            request:  Texto de la solicitud (puede contener la ruta).
            filepath: Ruta explícita al archivo JSON (opcional).
            **kwargs: Ignorados.

        Returns:
            Resumen del procesamiento.
        """
        # Resolver la ruta del archivo
        target = self._resolve_filepath(request, filepath)
        if target is None:
            return prompt_error(self.name, "No se especificó un archivo válido.")

        if not target.exists():
            return prompt_error(self.name, f"Archivo no encontrado: {target}")

        # Leer registros
        try:
            with open(target, encoding="utf-8") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            return prompt_error(self.name, f"Error al leer archivo: {exc}")

        if not isinstance(records, list):
            return prompt_error(self.name, "El archivo debe contener un array JSON.")

        # Normalizar cada registro
        transactions = []
        skipped = 0
        for record in records:
            if not isinstance(record, dict):
                skipped += 1
                continue
            try:
                raw_fields = parse_record(record)
                tx = normalize(raw_fields, record)
                transactions.append(tx)
            except Exception as exc:
                logger.warning("Error procesando registro: %s", exc)
                skipped += 1

        # Actualizar contexto
        self.context.transactions = transactions
        self.context.last_file = target
        # Resetear métricas y separación (se recalculan con ValidateSkill)
        self.context.valid = []
        self.context.invalid = []
        self.context.metrics = None

        summary = (
            f"Archivo: {target.name} | "
            f"Procesadas: {len(transactions)} | "
            f"Omitidas: {skipped}"
        )
        logger.info(summary)
        return prompt_success(self.name, summary)

    def _resolve_filepath(
        self, request: str, explicit: Path | None
    ) -> Path | None:
        """
        Determina la ruta del archivo a procesar.

        Prioridad:
          1. Parámetro `filepath` explícito.
          2. Ruta extraída del texto de la solicitud.
          3. Archivo de muestra por defecto.

        Args:
            request:  Texto de la solicitud.
            explicit: Ruta explícita proporcionada por el agente.

        Returns:
            Path resuelto, o None si no se puede determinar.
        """
        if explicit:
            return Path(explicit)

        # Intentar extraer una ruta del texto de la solicitud
        match = re.search(r"[\w./\\:]+\.json", request, re.IGNORECASE)
        if match:
            candidate = Path(match.group(0))
            if candidate.exists():
                return candidate

        # Default: archivo de muestra del proyecto
        from config.config import DATA_DIR
        default = DATA_DIR / "sample_transactions.json"
        return default
