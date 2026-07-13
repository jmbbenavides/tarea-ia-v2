"""
agent/agent.py
--------------
TransactionAgent: coordinador central del sistema agéntico.

Responsabilidades:
  1. Recibir solicitudes en texto libre o estructuradas.
  2. Delegar al SkillRouter la selección de skill.
  3. Instanciar y ejecutar la skill seleccionada.
  4. Devolver la respuesta al cliente (CLI u otro).
  5. Registrar cada acción en el log y en el contexto de sesión.

Decisión de diseño:
  El agente NO contiene lógica de negocio; actúa exclusivamente
  como orquestador entre el router y las skills. Esto permite
  sustituir el router rule-based por un LLM en el futuro sin
  cambiar las skills ni la CLI.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from config.config import setup_logging
from agent.context import AgentContext
from agent.router import SkillRouter
from agent.prompts import (
    prompt_skill_selected,
    prompt_no_skill,
    prompt_no_data,
    prompt_error,
)

# Importación de skills
from skills.normalize.skill import NormalizeSkill
from skills.validate.skill import ValidateSkill
from skills.metrics.skill import MetricsSkill
from skills.search.skill import SearchSkill
from skills.export.skill import ExportSkill
from skills.report.skill import ReportSkill

logger = setup_logging()

# Registro global de skills disponibles
_SKILL_REGISTRY: dict[str, type] = {
    "NormalizeSkill": NormalizeSkill,
    "ValidateSkill":  ValidateSkill,
    "MetricsSkill":   MetricsSkill,
    "SearchSkill":    SearchSkill,
    "ExportSkill":    ExportSkill,
    "ReportSkill":    ReportSkill,
}


class TransactionAgent:
    """
    Agente coordinador del sistema de normalización de transacciones.

    Orquesta el flujo completo:
      solicitud → router → skill → respuesta

    El estado de la sesión se mantiene en un AgentContext compartido
    entre todas las skills.

    Uso básico:
        agent = TransactionAgent()
        response = agent.run("normaliza data/sample_transactions.json")
        print(response)
    """

    def __init__(self) -> None:
        self.context = AgentContext()
        self.router = SkillRouter()
        self.router.register_skills(_SKILL_REGISTRY)
        logger.info("TransactionAgent inicializado con %d skills.", len(_SKILL_REGISTRY))

    def run(self, request: str, **kwargs: Any) -> str:
        """
        Procesa una solicitud y devuelve la respuesta del agente.

        El flujo es:
          1. Router identifica la skill.
          2. Se instancia la skill con el contexto compartido.
          3. Se ejecuta la skill.
          4. Se registra el resultado en el log.

        Args:
            request: Texto de la solicitud (puede incluir parámetros
                     como nombres de archivo o términos de búsqueda).
            **kwargs: Parámetros adicionales opcionales pasados a la skill.

        Returns:
            Cadena de texto con la respuesta del agente.
        """
        logger.info("Solicitud recibida: «%s»", request)
        self.context.log(f">> {request}")

        # 1. Seleccionar skill
        skill_class = self.router.route(request)

        if skill_class is None:
            response = prompt_no_skill(request, self.router.available_skills())
            logger.warning("Skill no identificada para solicitud: «%s»", request)
            self.context.log(f"   Sin skill: {request}")
            return response

        # 2. Instanciar y ejecutar skill
        skill_name = skill_class.__name__
        logger.info("Ejecutando skill: %s", skill_name)
        print(prompt_skill_selected(skill_name, request))

        try:
            skill = skill_class(context=self.context)
            response = skill.execute(request=request, **kwargs)
            self.context.log(f"   OK [{skill_name}]")
            logger.info("Skill %s completada.", skill_name)
        except Exception as exc:
            response = prompt_error(skill_name, str(exc))
            self.context.log(f"   ERROR [{skill_name}]: {exc}")
            logger.error("Error en skill %s: %s", skill_name, exc, exc_info=True)

        return response

    def run_pipeline(self, filepath: Optional[Path] = None) -> str:
        """
        Ejecuta el pipeline completo en modo batch:
        normaliza → valida → calcula métricas → exporta.

        Equivale al modo --proceso del main.py original.

        Args:
            filepath: Ruta opcional al archivo JSON de transacciones.

        Returns:
            Resumen del procesamiento batch.
        """
        from pathlib import Path as _Path
        from config.config import DATA_DIR

        target = filepath or (DATA_DIR / "sample_transactions.json")

        logger.info("Pipeline batch iniciado con archivo: %s", target)
        results = []

        # Paso 1: Normalizar
        results.append(self.run(f"normaliza {target}", filepath=target))

        # Paso 2: Validar (datos ya en contexto)
        if self.context.is_loaded():
            results.append(self.run("valida las transacciones"))

        # Paso 3: Métricas
        if self.context.is_loaded():
            results.append(self.run("métricas del procesamiento"))

        # Paso 4: Exportar
        if self.context.is_loaded():
            results.append(self.run("exporta los resultados"))

        return "\n\n".join(results)
