"""
skills/export/skill.py
----------------------
ExportSkill: exporta las transacciones válidas e inválidas del
contexto a los archivos data/valid.json y data/invalid.json.

Responsabilidades:
  - Verificar que haya datos validados en el contexto.
  - Serializar las transacciones válidas con to_dict().
  - Serializar las transacciones inválidas con to_dict_full()
    (incluye errores de validación).
  - Guardar ambos archivos en data/.

Dependencias internas:
  - models.transaction → Transaction.to_dict, to_dict_full
  - config.config       → DATA_DIR
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_error, prompt_no_data
from config.config import DATA_DIR
from skills.base import BaseSkill

logger = logging.getLogger("TransactionAgent.ExportSkill")


class ExportSkill(BaseSkill):
    """
    Skill de exportación de transacciones normalizadas.

    Genera dos archivos JSON en la carpeta data/:
      - valid.json   → transacciones que pasaron validación.
      - invalid.json → transacciones rechazadas con sus errores.

    Requiere que ValidateSkill haya sido ejecutada previamente.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(self, request: str, output_dir: Path | None = None, **kwargs: Any) -> str:
        """
        Exporta los archivos valid.json e invalid.json.

        Args:
            request:    Texto de la solicitud.
            output_dir: Directorio de salida (default: data/).
            **kwargs:   Ignorados.

        Returns:
            Resumen de la exportación.
        """
        if not self.context.is_loaded():
            return prompt_no_data()

        # Si no se ha validado, usar todas las transacciones
        valid = self.context.valid or [
            tx for tx in self.context.transactions if tx.is_valid
        ]
        invalid = self.context.invalid or [
            tx for tx in self.context.transactions if not tx.is_valid
        ]

        out_dir = Path(output_dir) if output_dir else DATA_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        valid_path = out_dir / "valid.json"
        invalid_path = out_dir / "invalid.json"

        try:
            with open(valid_path, "w", encoding="utf-8") as f:
                json.dump(
                    [tx.to_dict() for tx in valid],
                    f, ensure_ascii=False, indent=2
                )

            with open(invalid_path, "w", encoding="utf-8") as f:
                json.dump(
                    [tx.to_dict_full() for tx in invalid],
                    f, ensure_ascii=False, indent=2
                )
        except IOError as exc:
            return prompt_error(self.name, f"Error al escribir archivos: {exc}")

        summary = (
            f"valid.json ({len(valid)} registros) → {valid_path} | "
            f"invalid.json ({len(invalid)} registros) → {invalid_path}"
        )
        logger.info("Exportación completada. %s", summary)
        return prompt_success(self.name, summary)
