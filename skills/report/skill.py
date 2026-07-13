"""
skills/report/skill.py
----------------------
ReportSkill: genera un reporte Markdown con resumen ejecutivo
de las transacciones procesadas.

Responsabilidades:
  - Generar un documento Markdown estructurado.
  - Incluir: resumen general, métricas por estado, totales por
    moneda y lista de transacciones inválidas con errores.
  - Guardar el reporte en data/report.md.
  - Devolver la ruta del archivo generado.

Dependencias internas:
  - services.metrics → compute_metrics (si no hay métricas en contexto)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.context import AgentContext
from agent.prompts import prompt_success, prompt_error, prompt_no_data
from config.config import DATA_DIR
from services.metrics import compute_metrics
from skills.base import BaseSkill

logger = logging.getLogger("TransactionAgent.ReportSkill")


class ReportSkill(BaseSkill):
    """
    Skill de generación de reportes Markdown.

    Crea un reporte ejecutivo con el resumen completo del
    procesamiento y lo guarda en data/report.md.

    Requiere que haya transacciones en el contexto.
    """

    def __init__(self, context: AgentContext) -> None:
        super().__init__(context)

    def execute(
        self,
        request: str,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Genera el reporte Markdown.

        Args:
            request:     Texto de la solicitud.
            output_path: Ruta del archivo de salida (default: data/report.md).
            **kwargs:    Ignorados.

        Returns:
            Mensaje con la ruta del reporte generado.
        """
        if not self.context.is_loaded():
            return prompt_no_data()

        # Asegurar métricas disponibles
        metrics = self.context.metrics or compute_metrics(self.context.transactions)
        valid = self.context.valid or [tx for tx in self.context.transactions if tx.is_valid]
        invalid = self.context.invalid or [tx for tx in self.context.transactions if not tx.is_valid]

        report_path = Path(output_path) if output_path else (DATA_DIR / "report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._build_report(metrics, valid, invalid)

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
        except IOError as exc:
            return prompt_error(self.name, f"Error al guardar reporte: {exc}")

        logger.info("Reporte generado en: %s", report_path)
        return prompt_success(self.name, f"Reporte guardado en {report_path}")

    def _build_report(self, metrics: dict, valid: list, invalid: list) -> str:
        """
        Construye el contenido Markdown del reporte.

        Args:
            metrics: Diccionario de métricas calculadas.
            valid:   Lista de transacciones válidas.
            invalid: Lista de transacciones inválidas.

        Returns:
            Cadena con el contenido Markdown del reporte.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        file_name = (
            str(self.context.last_file.name)
            if self.context.last_file
            else "N/A"
        )

        lines = [
            "# Reporte de Normalización de Transacciones",
            "",
            f"**Generado:** {now}  ",
            f"**Archivo fuente:** {file_name}",
            "",
            "---",
            "",
            "## Resumen ejecutivo",
            "",
            f"| Indicador | Valor |",
            f"|-----------|-------|",
            f"| Total procesadas | {metrics['total_processed']} |",
            f"| Válidas | {metrics['total_valid']} |",
            f"| Inválidas | {metrics['total_invalid']} |",
            f"| Tasa de éxito | "
            f"{metrics['total_valid'] / max(metrics['total_processed'], 1) * 100:.1f}% |",
            "",
            "## Métricas por estado",
            "",
            "| Estado | Cantidad |",
            "|--------|----------|",
        ]

        for status, count in metrics["by_status"].items():
            lines.append(f"| {status} | {count} |")

        lines += [
            "",
            "## Totales por moneda (transacciones válidas)",
            "",
            "| Moneda | Total |",
            "|--------|-------|",
        ]

        if metrics["total_by_currency"]:
            for currency, total in sorted(metrics["total_by_currency"].items()):
                lines.append(f"| {currency} | {total:,.2f} |")
        else:
            lines.append("| — | Sin datos |")

        if invalid:
            lines += [
                "",
                "## Transacciones inválidas",
                "",
                "| ID | Errores |",
                "|----|---------|",
            ]
            for tx in invalid:
                errors = "; ".join(tx.validation_errors)
                tx_id = tx.id or "(sin ID)"
                lines.append(f"| {tx_id} | {errors} |")

        lines += ["", "---", "_Generado por TransactionAgent v2.0_"]
        return "\n".join(lines)
